"""
Firm (Workspace) Models - Multi-Tenant Foundation

This module implements the top-level tenant boundary for the multi-firm SaaS platform.
All data isolation, authorization, and privacy guarantees depend on this boundary.

CRITICAL: This is Tier 0 - Foundational Safety.
Every firm-side object MUST belong to exactly one Firm.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils.text import slugify


class Firm(models.Model):
    """
    Top-level tenant boundary.

    Represents a consulting firm or organization using the platform.
    All users, clients, projects, and billing records belong to exactly one Firm.

    SECURITY: Firm isolation MUST be enforced at the query level everywhere.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('trial', 'Trial Period'),
        ('suspended', 'Suspended'),
        ('canceled', 'Canceled'),
    ]

    SUBSCRIPTION_TIER_CHOICES = [
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]

    # Identity
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Firm name (must be unique across platform)"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="URL-safe identifier for subdomain (e.g., 'acme-consulting')",
        validators=[
            MinLengthValidator(3),
            RegexValidator(
                regex=r'^[a-z0-9-]+$',
                message='Slug must contain only lowercase letters, numbers, and hyphens'
            )
        ]
    )

    # Subscription & Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial'
    )
    subscription_tier = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TIER_CHOICES,
        default='starter'
    )

    # Trial Management
    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When trial period ends (null if not on trial)"
    )

    # Firm Settings
    timezone = models.CharField(
        max_length=50,
        default='America/New_York',
        help_text="Firm's default timezone"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Default currency code (ISO 4217)"
    )

    # Limits & Quotas
    max_users = models.IntegerField(
        default=5,
        help_text="Maximum number of firm users allowed"
    )
    max_clients = models.IntegerField(
        default=25,
        help_text="Maximum number of active clients allowed"
    )
    max_storage_gb = models.IntegerField(
        default=10,
        help_text="Maximum storage in gigabytes"
    )

    # Usage Tracking
    current_users_count = models.IntegerField(
        default=0,
        help_text="Current number of active users"
    )
    current_clients_count = models.IntegerField(
        default=0,
        help_text="Current number of active clients"
    )
    current_storage_gb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Current storage usage in GB"
    )

    # Audit & Compliance
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_firms',
        help_text="User who created this firm"
    )

    # Metadata
    notes = models.TextField(
        blank=True,
        help_text="Internal platform notes (not visible to firm)"
    )

    class Meta:
        db_table = 'firm_firm'
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
            models.Index(fields=['subscription_tier']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if firm is in active status."""
        return self.status == 'active'

    @property
    def is_over_user_limit(self):
        """Check if firm has exceeded user limit."""
        return self.current_users_count >= self.max_users

    @property
    def is_over_client_limit(self):
        """Check if firm has exceeded client limit."""
        return self.current_clients_count >= self.max_clients

    @property
    def is_over_storage_limit(self):
        """Check if firm has exceeded storage limit."""
        return self.current_storage_gb >= self.max_storage_gb


class FirmMembership(models.Model):
    """
    Links Users to Firms with roles and permissions.

    Implements the Firm ↔ User relationship required for tenant isolation.
    Each user can be a member of multiple firms (e.g., consultants, contractors).
    """
    ROLE_CHOICES = [
        ('owner', 'Firm Owner'),           # Master Admin - full control
        ('admin', 'Firm Admin'),           # Admin with granular permissions
        ('staff', 'Staff Member'),         # Standard user with limited permissions
        ('contractor', 'Contractor'),       # External contractor
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='firm_memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='staff'
    )

    # Permissions
    can_manage_users = models.BooleanField(
        default=False,
        help_text="Can invite/remove users"
    )
    can_manage_clients = models.BooleanField(
        default=False,
        help_text="Can create/delete clients"
    )
    can_manage_billing = models.BooleanField(
        default=False,
        help_text="Can view/modify billing"
    )
    can_manage_settings = models.BooleanField(
        default=False,
        help_text="Can modify firm settings"
    )
    can_view_reports = models.BooleanField(
        default=False,
        help_text="Can access analytics/reports"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this membership is currently active"
    )

    # Audit
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invited_firm_members',
        help_text="User who invited this member"
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time user was active in this firm"
    )

    class Meta:
        db_table = 'firm_membership'
        unique_together = [['firm', 'user']]
        ordering = ['-invited_at']
        indexes = [
            models.Index(fields=['firm', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.firm.name} ({self.role})"

    def save(self, *args, **kwargs):
        """Auto-set permissions based on role."""
        if self.role == 'owner':
            # Owner has all permissions
            self.can_manage_users = True
            self.can_manage_clients = True
            self.can_manage_billing = True
            self.can_manage_settings = True
            self.can_view_reports = True
        elif self.role == 'admin':
            # Admin has most permissions (but not settings by default)
            self.can_manage_users = True
            self.can_manage_clients = True
            self.can_manage_billing = True
            self.can_view_reports = True

        super().save(*args, **kwargs)


class BreakGlassSession(models.Model):
    """
    Break-glass activation record for platform operators.

    Meta-commentary:
    - This model captures the minimum audit trail required to make break-glass visible,
      time-bound, and reviewable.
    - Enforcement hooks (middleware/permissions) are intentionally not wired yet; that is
      a follow-up task under Tier 0.6 and Tier 2.1 to ensure access is actually gated.
    - Potential enhancement: add immutable, append-only audit events linked to each
      session for action-level logging once the audit subsystem exists.
    """

    STATUS_ACTIVE = 'active'
    STATUS_EXPIRED = 'expired'
    STATUS_REVOKED = 'revoked'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_REVOKED, 'Revoked'),
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='break_glass_sessions'
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='break_glass_sessions',
        help_text="Platform operator who activated break-glass"
    )
    impersonated_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='impersonated_by_break_glass_sessions',
        help_text="Optional: firm user being impersonated during break-glass"
    )
    reason = models.TextField(
        help_text="Required reason string for break-glass activation"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    activated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="Auto-expiration timestamp for break-glass"
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When break-glass was revoked early (if applicable)"
    )
    revoked_reason = models.TextField(
        blank=True,
        help_text="Optional: why break-glass was revoked early"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When break-glass usage was reviewed by platform ops"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_break_glass_sessions',
        help_text="Reviewer for break-glass session audit"
    )

    class BreakGlassSessionQuerySet(models.QuerySet):
        """
        Query helpers for break-glass session lifecycle tracking.

        Meta-commentary:
        - These helpers support visibility and cleanup without introducing
          direct authorization enforcement (still pending).
        """

        def active(self):
            """Return active, unexpired sessions."""
            return self.filter(status=self.model.STATUS_ACTIVE, expires_at__gt=timezone.now())

        def overdue(self):
            """Return sessions that should be expired based on expires_at."""
            return self.filter(status=self.model.STATUS_ACTIVE, expires_at__lte=timezone.now())

        def expire_overdue(self):
            """
            Mark overdue sessions as expired.

            Meta-commentary:
            - Intended to be called from a tenant-aware background job once
              async jobs are firm-scoped (Tier 2.3).
            """
            return self.overdue().update(status=self.model.STATUS_EXPIRED)

        def for_firm(self, firm):
            """
            Return sessions scoped to a single firm.

            Meta-commentary:
            - Guarding against missing firm context here reinforces tenant isolation,
              but enforcement hooks still need to call this helper consistently.
            """
            if firm is None:
                raise ValueError("Firm context is required to scope break-glass sessions.")
            return self.filter(firm=firm)

    objects = BreakGlassSessionQuerySet.as_manager()

    class Meta:
        db_table = 'firm_break_glass_session'
        ordering = ['-activated_at']
        indexes = [
            models.Index(fields=['firm', 'status'], name='firm_bg_firm_status_idx'),
            models.Index(fields=['operator', 'status'], name='firm_bg_operator_status_idx'),
            models.Index(fields=['expires_at'], name='firm_bg_expires_at_idx'),
        ]

    def __str__(self):
        return f"Break-glass {self.id} for {self.firm.name} ({self.status})"

    @property
    def is_active(self):
        """
        Return True if break-glass is currently active and unexpired.

        Meta-commentary:
        - This is a convenience check for guards/permissions.
        - Enforcement logic still needs to call this method in middleware or permissions.
        """
        return self.status == self.STATUS_ACTIVE and not self.is_expired

    @property
    def is_expired(self):
        """Return True when the break-glass session is past its expiry."""
        return timezone.now() >= self.expires_at

    def clean(self):
        """
        Validate basic invariants for break-glass sessions.

        Meta-commentary:
        - We enforce that expiry timestamps are in the future to prevent
          immediately-expired sessions from being created while active.
        - Follow-up: enforce maximum duration via policy config.
        """
        if self.status == self.STATUS_ACTIVE and self.expires_at <= timezone.now():
            raise ValidationError({'expires_at': 'Break-glass expiry must be in the future.'})
        if self.status == self.STATUS_REVOKED:
            if not self.revoked_at:
                raise ValidationError({'revoked_at': 'Revoked sessions must include a revocation timestamp.'})
            if not self.revoked_reason:
                raise ValidationError({'revoked_reason': 'Revoked sessions must include a revocation reason.'})
        if self.reviewed_at and not self.reviewed_by:
            raise ValidationError({'reviewed_by': 'Reviewed sessions must include a reviewer.'})
        if self.reviewed_by and not self.reviewed_at:
            raise ValidationError({'reviewed_at': 'Reviewed sessions must include a review timestamp.'})
        if self.reviewed_at and self.status == self.STATUS_ACTIVE:
            raise ValidationError({'reviewed_at': 'Active sessions cannot be reviewed until closed.'})
        if self.activated_at and self.expires_at <= self.activated_at:
            raise ValidationError({'expires_at': 'Expiry must be after activation.'})
        if self.revoked_at and self.revoked_at < self.activated_at:
            raise ValidationError({'revoked_at': 'Revocation cannot occur before activation.'})
        if self.reviewed_at and self.reviewed_at < self.activated_at:
            raise ValidationError({'reviewed_at': 'Review cannot occur before activation.'})

    def mark_expired(self):
        """
        Mark the session as expired if it has passed its expiry.

        Meta-commentary:
        - This is intended for periodic cleanup jobs once the async job system
          carries firm context (Tier 2.3).
        """
        if self.is_expired and self.status == self.STATUS_ACTIVE:
            self.status = self.STATUS_EXPIRED

    def revoke(self, reason: str):
        """
        Revoke break-glass access before expiry.

        Meta-commentary:
        - Revocations should be written to the audit event system once it exists.
        """
        if not reason:
            raise ValidationError({'revoked_reason': 'Revocation reason is required.'})
        self.status = self.STATUS_REVOKED
        self.revoked_at = timezone.now()
        self.revoked_reason = reason

    def mark_reviewed(self, reviewer):
        """
        Mark the session as reviewed by platform ops.

        Meta-commentary:
        - Review should only occur after the session is expired or revoked.
        - Follow-up: attach review events to the audit stream.
        """
        if self.status == self.STATUS_ACTIVE:
            raise ValidationError({'reviewed_at': 'Active sessions cannot be reviewed until closed.'})
        if reviewer is None:
            raise ValidationError({'reviewed_by': 'Reviewer is required to mark a session as reviewed.'})
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()

    def save(self, *args, **kwargs):
        """Run validation and update status before saving."""
        self.mark_expired()
        self.full_clean()
        super().save(*args, **kwargs)
