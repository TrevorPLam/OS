"""
Tenant Provisioning Service (DOC-19.1).

Implements idempotent firm provisioning workflow per DB_SCHEMA_AND_MIGRATIONS spec (docs/19).

Workflow:
1. Create Firm record
2. Create firm admin user
3. Seed baseline config (roles, default stages, template stubs)
4. Record audit events and provisioning logs
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from typing import Dict, Any, Optional
import logging

from modules.firm.models import Firm, FirmMembership
from modules.firm.audit import audit

User = get_user_model()
logger = logging.getLogger(__name__)


class ProvisioningError(Exception):
    """Raised when provisioning fails."""
    pass


class ProvisioningLog(models.Model):
    """
    Records provisioning attempts for auditability.

    Per docs/19 section 2: Migration runner records:
    - start/end time
    - success/failure
    - correlation id
    """
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='provisioning_logs',
        null=True,  # Null if provisioning failed before Firm creation
        help_text="Firm that was provisioned (null if provisioning failed early)"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('rolled_back', 'Rolled Back'),
        ],
        default='pending'
    )

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total provisioning duration in seconds"
    )

    # Tracking
    correlation_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Correlation ID for request tracing"
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who initiated provisioning (platform operator)"
    )

    # Configuration
    provisioning_config = models.JSONField(
        default=dict,
        help_text="Configuration used for provisioning (firm details, admin user, etc.)"
    )

    # Results
    steps_completed = models.JSONField(
        default=list,
        help_text="List of provisioning steps successfully completed"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if provisioning failed"
    )
    error_step = models.CharField(
        max_length=100,
        blank=True,
        help_text="Step where provisioning failed"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional provisioning metadata (created resources, etc.)"
    )

    class Meta:
        db_table = 'firm_provisioning_log'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['-started_at']),
        ]

    def __str__(self):
        firm_name = self.firm.name if self.firm else self.provisioning_config.get('firm_name', 'Unknown')
        return f"Provisioning {firm_name} - {self.status} ({self.started_at})"

    def mark_completed(self):
        """Mark provisioning as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        self.save()

    def mark_failed(self, error_message: str, error_step: str):
        """Mark provisioning as failed."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        self.error_message = error_message
        self.error_step = error_step
        self.save()


from django.db import models


class TenantProvisioningService:
    """
    Idempotent tenant provisioning service.

    Implements docs/19 section 1: Row-level tenant provisioning workflow.
    """

    def __init__(self, correlation_id: Optional[str] = None, initiated_by: Optional[User] = None):
        """
        Initialize provisioning service.

        Args:
            correlation_id: Optional correlation ID for request tracing
            initiated_by: Optional user who initiated provisioning
        """
        from modules.core.observability import generate_correlation_id
        self.correlation_id = correlation_id or generate_correlation_id()
        self.initiated_by = initiated_by
        self.provisioning_log = None

    def provision_firm(
        self,
        firm_name: str,
        firm_slug: str,
        admin_email: str,
        admin_password: str,
        admin_first_name: str = "",
        admin_last_name: str = "",
        timezone: str = "America/New_York",
        currency: str = "USD",
        subscription_tier: str = "starter",
        **extra_config
    ) -> Dict[str, Any]:
        """
        Provision a new firm with baseline configuration.

        This method is IDEMPOTENT:
        - If firm with slug already exists, returns existing firm
        - If admin user with email already exists, reuses that user
        - Baseline config seeding is idempotent (creates only if not exists)

        Per docs/19 section 1:
        1. Create Firm record
        2. Create firm admin user
        3. Seed baseline config (roles, default stages, template stubs)
        4. Record audit events and provisioning logs

        Args:
            firm_name: Name of the firm
            firm_slug: URL-safe slug for the firm
            admin_email: Email for the firm admin user
            admin_password: Password for the firm admin user
            admin_first_name: Admin's first name
            admin_last_name: Admin's last name
            timezone: Firm's default timezone
            currency: Firm's default currency
            subscription_tier: Subscription tier (starter, professional, enterprise)
            **extra_config: Additional configuration options

        Returns:
            Dict with:
                - firm: Created/existing Firm instance
                - admin_user: Created/existing User instance
                - firm_membership: Created/existing FirmMembership instance
                - created: Boolean indicating if new firm was created
                - provisioning_log: ProvisioningLog instance

        Raises:
            ProvisioningError: If provisioning fails
        """
        # Create provisioning log
        provisioning_config = {
            'firm_name': firm_name,
            'firm_slug': firm_slug,
            'admin_email': admin_email,
            'timezone': timezone,
            'currency': currency,
            'subscription_tier': subscription_tier,
            **extra_config
        }

        self.provisioning_log = ProvisioningLog.objects.create(
            status='in_progress',
            correlation_id=self.correlation_id,
            initiated_by=self.initiated_by,
            provisioning_config=provisioning_config
        )

        steps_completed = []
        firm = None
        admin_user = None
        membership = None
        created = False

        try:
            with transaction.atomic():
                # Step 1: Create Firm record (idempotent)
                firm, firm_created = self._create_firm(
                    name=firm_name,
                    slug=firm_slug,
                    timezone=timezone,
                    currency=currency,
                    subscription_tier=subscription_tier,
                    **extra_config
                )
                steps_completed.append('create_firm')
                created = firm_created

                # Update provisioning log with firm reference
                self.provisioning_log.firm = firm
                self.provisioning_log.save()

                # Step 2: Create firm admin user (idempotent)
                admin_user, user_created = self._create_admin_user(
                    email=admin_email,
                    password=admin_password,
                    first_name=admin_first_name,
                    last_name=admin_last_name,
                    firm=firm
                )
                steps_completed.append('create_admin_user')

                # Step 3: Create firm membership (idempotent)
                membership, membership_created = self._create_firm_membership(
                    user=admin_user,
                    firm=firm
                )
                steps_completed.append('create_firm_membership')

                # Step 4: Seed baseline configuration (idempotent)
                self._seed_baseline_config(firm)
                steps_completed.append('seed_baseline_config')

                # Step 5: Record audit events
                self._record_provisioning_audit(
                    firm=firm,
                    admin_user=admin_user,
                    created=created
                )
                steps_completed.append('record_audit_events')

            # Mark provisioning as completed
            self.provisioning_log.steps_completed = steps_completed
            self.provisioning_log.metadata = {
                'firm_id': firm.id,
                'admin_user_id': admin_user.id,
                'membership_id': membership.id,
                'created': created,
            }
            self.provisioning_log.mark_completed()

            logger.info(
                f"Firm provisioning {'completed' if created else 'verified'}: {firm.name} (slug={firm.slug})",
                extra={
                    'correlation_id': self.correlation_id,
                    'firm_id': firm.id,
                    'created': created,
                }
            )

            return {
                'firm': firm,
                'admin_user': admin_user,
                'firm_membership': membership,
                'created': created,
                'provisioning_log': self.provisioning_log,
            }

        except Exception as e:
            error_message = str(e)
            error_step = steps_completed[-1] if steps_completed else 'initialization'

            self.provisioning_log.steps_completed = steps_completed
            self.provisioning_log.mark_failed(error_message, error_step)

            logger.error(
                f"Firm provisioning failed at step '{error_step}': {error_message}",
                extra={
                    'correlation_id': self.correlation_id,
                    'firm_slug': firm_slug,
                    'error_step': error_step,
                },
                exc_info=True
            )

            raise ProvisioningError(f"Provisioning failed at step '{error_step}': {error_message}") from e

    def _create_firm(
        self,
        name: str,
        slug: str,
        timezone: str,
        currency: str,
        subscription_tier: str,
        **extra_config
    ) -> tuple[Firm, bool]:
        """
        Create Firm record (idempotent).

        Returns:
            (firm, created) tuple
        """
        firm, created = Firm.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'timezone': timezone,
                'currency': currency,
                'subscription_tier': subscription_tier,
                'status': 'trial',
                'created_by': self.initiated_by,
                **extra_config
            }
        )

        if not created:
            logger.info(
                f"Firm with slug '{slug}' already exists, reusing existing firm",
                extra={'correlation_id': self.correlation_id, 'firm_id': firm.id}
            )

        return firm, created

    def _create_admin_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        firm: Firm
    ) -> tuple[User, bool]:
        """
        Create firm admin user (idempotent).

        Returns:
            (user, created) tuple
        """
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,  # Use email as username
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
                'is_staff': False,  # Not platform staff, just firm admin
            }
        )

        if created:
            # Set password only for newly created users
            user.set_password(password)
            user.save()
        else:
            logger.info(
                f"User with email '{email}' already exists, reusing existing user",
                extra={'correlation_id': self.correlation_id, 'user_id': user.id}
            )

        return user, created

    def _create_firm_membership(
        self,
        user: User,
        firm: Firm
    ) -> tuple[FirmMembership, bool]:
        """
        Create firm membership for admin user (idempotent).

        Returns:
            (membership, created) tuple
        """
        membership, created = FirmMembership.objects.get_or_create(
            user=user,
            firm=firm,
            defaults={
                'role': 'admin',  # Firm admin role
                'is_active': True,
            }
        )

        if not created:
            # Ensure admin role if membership already existed
            if membership.role != 'admin':
                membership.role = 'admin'
                membership.save()
                logger.info(
                    f"Updated existing membership to admin role",
                    extra={'correlation_id': self.correlation_id, 'membership_id': membership.id}
                )

        return membership, created

    def _seed_baseline_config(self, firm: Firm):
        """
        Seed baseline configuration for new firm (idempotent).

        Per docs/19 section 1:
        - Roles (handled via FirmMembership)
        - Default stages (CRM pipeline stages)
        - Template stubs (project templates, email templates, etc.)

        All seeding operations must be idempotent (create only if not exists).
        """
        # STUB: Baseline configuration seeding
        # TODO: Implement when configuration models are defined
        # - CRM pipeline stages (Lead → Prospect → Negotiation → Won/Lost)
        # - Default project templates
        # - Email notification templates
        # - Default document categories
        # - Default task statuses

        logger.debug(
            f"Baseline config seeding for firm {firm.id} (stub - no config to seed yet)",
            extra={'correlation_id': self.correlation_id, 'firm_id': firm.id}
        )

    def _record_provisioning_audit(
        self,
        firm: Firm,
        admin_user: User,
        created: bool
    ):
        """
        Record audit events for provisioning.

        Per docs/19 section 1: Record audit events and provisioning logs.
        """
        action = 'firm_provisioned' if created else 'firm_provisioning_verified'

        audit.log_event(
            firm=firm,
            category='config',
            action=action,
            actor=self.initiated_by or admin_user,
            target_model='Firm',
            target_id=firm.id,
            metadata={
                'correlation_id': self.correlation_id,
                'admin_user_id': admin_user.id,
                'admin_email': admin_user.email,
                'created': created,
                'subscription_tier': firm.subscription_tier,
                'timezone': firm.timezone,
                'currency': firm.currency,
            }
        )


def provision_firm(
    firm_name: str,
    firm_slug: str,
    admin_email: str,
    admin_password: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to provision a new firm.

    This is the primary entry point for tenant provisioning.

    Args:
        firm_name: Name of the firm
        firm_slug: URL-safe slug for the firm
        admin_email: Email for the firm admin user
        admin_password: Password for the firm admin user
        **kwargs: Additional configuration (timezone, currency, etc.)

    Returns:
        Dict with provisioning results (firm, admin_user, etc.)

    Raises:
        ProvisioningError: If provisioning fails

    Example:
        >>> result = provision_firm(
        ...     firm_name="Acme Consulting",
        ...     firm_slug="acme-consulting",
        ...     admin_email="admin@acme.com",
        ...     admin_password="secure_password_123",
        ...     timezone="America/Los_Angeles",
        ...     currency="USD",
        ...     subscription_tier="professional"
        ... )
        >>> print(result['firm'].name)
        Acme Consulting
        >>> print(result['created'])
        True
    """
    service = TenantProvisioningService()
    return service.provision_firm(
        firm_name=firm_name,
        firm_slug=firm_slug,
        admin_email=admin_email,
        admin_password=admin_password,
        **kwargs
    )
