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


class UserProfile(models.Model):
    """
    Extended user profile for platform-level roles and preferences.
    
    TIER 0.5: Platform Privacy Enforcement
    Separates platform operators from firm users and enforces metadata-only access.
    
    Platform Roles:
    - None (default): Regular firm user, no platform access
    - Platform Operator: Metadata-only access for operations/support
    - Break-Glass Operator: Rare, audited content access (requires active BreakGlassSession)
    """
    
    PLATFORM_ROLE_NONE = None
    PLATFORM_ROLE_OPERATOR = 'operator'
    PLATFORM_ROLE_BREAK_GLASS = 'break_glass'
    
    PLATFORM_ROLE_CHOICES = [
        (PLATFORM_ROLE_NONE, 'None (Firm User)'),
        (PLATFORM_ROLE_OPERATOR, 'Platform Operator'),
        (PLATFORM_ROLE_BREAK_GLASS, 'Break-Glass Operator'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='platform_profile',
        primary_key=True
    )
    
    # Platform Role
    platform_role = models.CharField(
        max_length=20,
        choices=PLATFORM_ROLE_CHOICES,
        null=True,
        blank=True,
        default=None,
        help_text=(
            "Platform-level role. None = regular firm user. "
            "Operator = metadata-only platform access. "
            "Break-Glass = can activate break-glass sessions for content access."
        )
    )
    
    # Preferences
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's preferred timezone"
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'firm_user_profile'
        indexes = [
            models.Index(fields=['platform_role']),
        ]
    
    def __str__(self):
        role_display = dict(self.PLATFORM_ROLE_CHOICES).get(self.platform_role, 'Firm User')
        return f"{self.user.username} - {role_display}"
    
    @property
    def is_platform_operator(self):
        """Check if user is a platform operator (metadata-only)."""
        return self.platform_role == self.PLATFORM_ROLE_OPERATOR
    
    @property
    def is_break_glass_operator(self):
        """Check if user is a break-glass operator (can activate break-glass)."""
        return self.platform_role == self.PLATFORM_ROLE_BREAK_GLASS
    
    @property
    def is_platform_staff(self):
        """Check if user has any platform role."""
        return self.platform_role in [self.PLATFORM_ROLE_OPERATOR, self.PLATFORM_ROLE_BREAK_GLASS]


class AuditEvent(models.Model):
    """
    Immutable audit event log (TIER 0.6 - Break-Glass Audit).
    
    Records all sensitive actions for compliance and security review.
    Events are immutable once created - no updates or deletions allowed.
    
    Categories:
    - AUTH: Authentication and authorization events
    - PERMISSIONS: Permission changes and grants
    - BREAK_GLASS: Break-glass activation, expiry, revocation, actions
    - BILLING_METADATA: Billing-related metadata access
    - PURGE: Content purges and deletions
    - CONFIG: Configuration changes affecting access or billing
    """
    
    # Event Categories
    CATEGORY_AUTH = 'AUTH'
    CATEGORY_PERMISSIONS = 'PERMISSIONS'
    CATEGORY_BREAK_GLASS = 'BREAK_GLASS'
    CATEGORY_BILLING_METADATA = 'BILLING_METADATA'
    CATEGORY_PURGE = 'PURGE'
    CATEGORY_CONFIG = 'CONFIG'
    
    CATEGORY_CHOICES = [
        (CATEGORY_AUTH, 'Authentication & Authorization'),
        (CATEGORY_PERMISSIONS, 'Permission Changes'),
        (CATEGORY_BREAK_GLASS, 'Break-Glass Access'),
        (CATEGORY_BILLING_METADATA, 'Billing Metadata Access'),
        (CATEGORY_PURGE, 'Content Purge'),
        (CATEGORY_CONFIG, 'Configuration Change'),
    ]
    
    # Break-Glass Action Types
    ACTION_BG_ACTIVATED = 'break_glass_activated'
    ACTION_BG_EXPIRED = 'break_glass_expired'
    ACTION_BG_REVOKED = 'break_glass_revoked'
    ACTION_BG_CONTENT_ACCESS = 'break_glass_content_access'
    ACTION_BG_REVIEWED = 'break_glass_reviewed'
    
    # TIER 0.6: Firm tenancy (nullable for platform-wide events)
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='audit_events',
        null=True,
        blank=True,
        help_text="Firm context (null for platform-wide events)"
    )
    
    # Event Details
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text="Event category for filtering and review"
    )
    action = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Specific action taken (e.g., 'break_glass_activated')"
    )
    
    # Actor
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_events',
        help_text="User who performed the action"
    )
    actor_username = models.CharField(
        max_length=150,
        help_text="Actor username (denormalized for immutability)"
    )
    actor_email = models.EmailField(
        blank=True,
        help_text="Actor email (denormalized for immutability)"
    )
    
    # Target
    target_model = models.CharField(
        max_length=100,
        blank=True,
        help_text="Target model (e.g., 'Document', 'BreakGlassSession')"
    )
    target_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Target object ID"
    )
    target_description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable target description"
    )
    
    # Context
    reason = models.TextField(
        blank=True,
        help_text="Reason for action (required for break-glass)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context (IP, user agent, etc.) - never contains content"
    )
    
    # Timestamp
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the event occurred"
    )
    
    class Meta:
        db_table = 'firm_audit_event'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['firm', 'category', '-timestamp']),
            models.Index(fields=['actor', '-timestamp']),
            models.Index(fields=['category', 'action', '-timestamp']),
        ]
        # Permissions to prevent modifications
        permissions = [
            ('view_audit_events', 'Can view audit events'),
        ]
    
    def __str__(self):
        firm_str = f"{self.firm.name}" if self.firm else "Platform"
        return f"[{firm_str}] {self.category}: {self.action} by {self.actor_username}"
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure immutability.
        
        Only allow creation, not updates.
        """
        if self.pk is not None:
            raise ValidationError("Audit events are immutable and cannot be updated.")
        
        # Denormalize actor info for immutability
        if self.actor and not self.actor_username:
            self.actor_username = self.actor.username
            self.actor_email = self.actor.email or ''
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of audit events."""
        raise ValidationError("Audit events are immutable and cannot be deleted.")
    
    @classmethod
    def log_break_glass_activation(cls, session: BreakGlassSession):
        """Log break-glass activation event."""
        return cls.objects.create(
            firm=session.firm,
            category=cls.CATEGORY_BREAK_GLASS,
            action=cls.ACTION_BG_ACTIVATED,
            actor=session.operator,
            target_model='BreakGlassSession',
            target_id=str(session.id),
            target_description=f"Break-glass for {session.firm.name}",
            reason=session.reason,
            metadata={
                'expires_at': session.expires_at.isoformat(),
                'impersonated_user': session.impersonated_user.username if session.impersonated_user else None,
            }
        )
    
    @classmethod
    def log_break_glass_content_access(cls, session: BreakGlassSession, 
                                       target_model: str, target_id: str,
                                       description: str):
        """Log content access during break-glass session."""
        return cls.objects.create(
            firm=session.firm,
            category=cls.CATEGORY_BREAK_GLASS,
            action=cls.ACTION_BG_CONTENT_ACCESS,
            actor=session.operator,
            target_model=target_model,
            target_id=target_id,
            target_description=description,
            reason=f"Break-glass session #{session.id}",
            metadata={
                'break_glass_session_id': session.id,
            }
        )
    
    @classmethod
    def log_break_glass_revocation(cls, session: BreakGlassSession, revoked_by):
        """Log break-glass revocation event."""
        return cls.objects.create(
            firm=session.firm,
            category=cls.CATEGORY_BREAK_GLASS,
            action=cls.ACTION_BG_REVOKED,
            actor=revoked_by,
            target_model='BreakGlassSession',
            target_id=str(session.id),
            target_description=f"Break-glass #{session.id} revoked",
            reason=session.revoked_reason,
            metadata={
                'original_operator': session.operator.username,
            }
        )

