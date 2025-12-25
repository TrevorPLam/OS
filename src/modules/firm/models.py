"""
Firm (Workspace) Models - Multi-Tenant Foundation

This module implements the top-level tenant boundary for the multi-firm SaaS platform.
All data isolation, authorization, and privacy guarantees depend on this boundary.

CRITICAL: This is Tier 0 - Foundational Safety.
Every firm-side object MUST belong to exactly one Firm.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils.text import slugify
import json


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
        settings.AUTH_USER_MODEL,
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
        settings.AUTH_USER_MODEL,
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
        settings.AUTH_USER_MODEL,
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


class PlatformUserProfile(models.Model):
    """
    Platform operator profile for users with platform-level access.

    TIER 0 REQUIREMENT: Platform staff roles must be separated:
    - Platform Operator: metadata-only access (default, safe operations)
    - Break-Glass Operator: can activate break-glass for content access (rare, audited)

    Meta-commentary:
    - This model extends Django User with platform-specific role information.
    - Platform operators should NEVER have default access to customer content.
    - Break-glass capability is explicitly granted, not default for all platform staff.
    - All platform actions should be auditable (future: link to audit system).
    """

    ROLE_PLATFORM_OPERATOR = 'platform_operator'
    ROLE_BREAK_GLASS_OPERATOR = 'break_glass_operator'
    ROLE_CHOICES = [
        (ROLE_PLATFORM_OPERATOR, 'Platform Operator (Metadata Only)'),
        (ROLE_BREAK_GLASS_OPERATOR, 'Break-Glass Operator (Rare, Audited Access)'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='platform_profile',
        help_text="Link to Django User"
    )
    platform_role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default=ROLE_PLATFORM_OPERATOR,
        help_text="Platform access level: operator (metadata) or break-glass (rare content access)"
    )
    is_platform_active = models.BooleanField(
        default=True,
        help_text="Whether platform access is currently active"
    )
    can_activate_break_glass = models.BooleanField(
        default=False,
        help_text="Explicit flag: can this user activate break-glass sessions? (separate from role)"
    )

    # Audit
    granted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When platform access was granted"
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_platform_profiles',
        help_text="Who granted this platform access"
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When platform access was revoked (if applicable)"
    )
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_platform_profiles',
        help_text="Who revoked this platform access"
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this platform user (e.g., reason for access)"
    )

    class Meta:
        db_table = 'firm_platform_user_profile'
        ordering = ['-granted_at']
        indexes = [
            models.Index(
                fields=['platform_role', 'is_platform_active'],
                name='firm_plat_role_active_idx',
            ),
            models.Index(
                fields=['can_activate_break_glass'],
                name='firm_plat_bg_perm_idx',
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_platform_role_display()}"

    @property
    def is_break_glass_operator(self):
        """Check if user is a break-glass operator with active access."""
        return (
            self.platform_role == self.ROLE_BREAK_GLASS_OPERATOR
            and self.is_platform_active
            and self.can_activate_break_glass
        )

    @property
    def is_platform_operator(self):
        """Check if user is a platform operator (metadata-only access)."""
        return self.platform_role == self.ROLE_PLATFORM_OPERATOR and self.is_platform_active

    def revoke_access(self, revoker, reason=""):
        """Revoke platform access for this user."""
        self.is_platform_active = False
        self.can_activate_break_glass = False
        self.revoked_at = timezone.now()
        self.revoked_by = revoker
        if reason:
            self.notes = f"{self.notes}\n[REVOKED] {reason}".strip()

    def clean(self):
        """Validate platform profile invariants."""
        # Break-glass operators must have explicit break-glass activation permission
        if self.platform_role == self.ROLE_BREAK_GLASS_OPERATOR and not self.can_activate_break_glass:
            raise ValidationError({
                'can_activate_break_glass': 'Break-glass operators must have can_activate_break_glass enabled.'
            })

        # Revocation invariants
        if not self.is_platform_active and not self.revoked_at:
            raise ValidationError({
                'revoked_at': 'Inactive platform profiles must have revoked_at timestamp.'
            })
        if self.revoked_at and not self.revoked_by:
            raise ValidationError({
                'revoked_by': 'Revoked platform profiles must include who revoked access.'
            })

    def save(self, *args, **kwargs):
        """Run validation before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


class AuditEvent(models.Model):
    """
    Immutable audit event log for platform operations.

    TIER 3 REQUIREMENT: Audit event taxonomy + retention policy

    This model implements structured, tenant-scoped audit logging for:
    - Authentication and authorization events
    - Break-glass content access
    - Billing metadata operations
    - Data purges and deletions
    - Configuration changes
    - Permission changes

    CRITICAL INVARIANTS:
    - All audit events are immutable (no updates, no deletes via application code)
    - All audit events are tenant-scoped (firm_id required)
    - All audit events are content-free (metadata only, no customer content)
    - Actor and timestamp are always captured
    - Retention policies are defined per category

    Meta-commentary:
    - This is the foundational audit system for TIER 3 compliance
    - Break-glass actions, purges, and billing changes MUST emit audit events
    - Events survive content purges (tombstone pattern)
    - Review ownership and cadence are defined per category
    """

    # Event Categories (TIER 3 requirement)
    CATEGORY_AUTH = 'AUTH'
    CATEGORY_PERMISSIONS = 'PERMISSIONS'
    CATEGORY_BREAK_GLASS = 'BREAK_GLASS'
    CATEGORY_BILLING_METADATA = 'BILLING_METADATA'
    CATEGORY_PURGE = 'PURGE'
    CATEGORY_CONFIG = 'CONFIG'
    CATEGORY_DATA_ACCESS = 'DATA_ACCESS'
    CATEGORY_ROLE_CHANGE = 'ROLE_CHANGE'
    CATEGORY_EXPORT = 'EXPORT'
    CATEGORY_SIGNING = 'SIGNING'

    CATEGORY_CHOICES = [
        (CATEGORY_AUTH, 'Authentication & Authorization'),
        (CATEGORY_PERMISSIONS, 'Permission Changes'),
        (CATEGORY_BREAK_GLASS, 'Break-Glass Content Access'),
        (CATEGORY_BILLING_METADATA, 'Billing Metadata Operations'),
        (CATEGORY_PURGE, 'Data Purge/Deletion'),
        (CATEGORY_CONFIG, 'Configuration Changes'),
        (CATEGORY_DATA_ACCESS, 'Data Access Events'),
        (CATEGORY_ROLE_CHANGE, 'Role & Membership Changes'),
        (CATEGORY_EXPORT, 'Data Export Operations'),
        (CATEGORY_SIGNING, 'Document Signing Events'),
    ]

    # Retention Policy (in days)
    RETENTION_POLICY = {
        CATEGORY_AUTH: 90,                    # 90 days - authentication events
        CATEGORY_PERMISSIONS: 365,            # 1 year - permission changes
        CATEGORY_BREAK_GLASS: 2555,           # 7 years - legal/compliance requirement
        CATEGORY_BILLING_METADATA: 2555,      # 7 years - financial records
        CATEGORY_PURGE: None,                 # Forever - never delete purge records
        CATEGORY_CONFIG: 365,                 # 1 year - config changes
        CATEGORY_DATA_ACCESS: 90,             # 90 days - general data access
        CATEGORY_ROLE_CHANGE: 365,            # 1 year - role changes
        CATEGORY_EXPORT: 365,                 # 1 year - export operations
        CATEGORY_SIGNING: None,               # Forever - signing evidence survives content purge
    }

    # Severity Levels
    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_CRITICAL = 'critical'

    SEVERITY_CHOICES = [
        (SEVERITY_INFO, 'Informational'),
        (SEVERITY_WARNING, 'Warning'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    # Core Tenant Context (required)
    firm = models.ForeignKey(
        Firm,
        on_delete=models.PROTECT,  # PROTECT: never delete audit events via cascade
        related_name='audit_events',
        help_text="Tenant context: which firm this event belongs to"
    )

    # Event Classification
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text="Event category for filtering and retention policy"
    )
    action = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Action performed (e.g., 'user.login', 'break_glass.activate', 'document.purge')"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_INFO,
        help_text="Event severity level"
    )

    # Actor Context (who performed the action)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events_as_actor',
        help_text="User who performed the action (null for system events)"
    )
    actor_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of actor (if available)"
    )
    actor_user_agent = models.TextField(
        blank=True,
        help_text="User agent string (if available)"
    )

    # Target Context (what was acted upon)
    # Using GenericForeignKey for flexible target references
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Type of object this event targets"
    )
    target_object_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID of target object"
    )
    target_object = GenericForeignKey('target_content_type', 'target_object_id')
    target_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Human-readable description of target (survives target deletion)"
    )

    # Additional Context
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
        help_text="Client context (if action is client-scoped)"
    )

    # Event Metadata (content-free, structured data only)
    reason = models.TextField(
        blank=True,
        help_text="Reason string for actions requiring justification (break-glass, purge, etc.)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured metadata (MUST be content-free, operational data only)"
    )

    # Timestamps (immutable)
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this event occurred (immutable)"
    )

    # Retention Management
    retention_until = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this event can be deleted per retention policy (null = keep forever)"
    )

    class AuditEventQuerySet(models.QuerySet):
        """Query helpers for audit event filtering and retention management."""

        def for_firm(self, firm):
            """Return audit events scoped to a single firm."""
            if firm is None:
                raise ValueError("Firm context is required to scope audit events.")
            return self.filter(firm=firm)

        def for_category(self, category):
            """Filter by event category."""
            return self.filter(category=category)

        def for_actor(self, user):
            """Filter by actor (user who performed the action)."""
            return self.filter(actor=user)

        def break_glass_events(self):
            """Return all break-glass audit events."""
            return self.filter(category=self.model.CATEGORY_BREAK_GLASS)

        def purge_events(self):
            """Return all purge/deletion audit events."""
            return self.filter(category=self.model.CATEGORY_PURGE)

        def billing_events(self):
            """Return all billing metadata audit events."""
            return self.filter(category=self.model.CATEGORY_BILLING_METADATA)

        def critical_events(self):
            """Return all critical severity events."""
            return self.filter(severity=self.model.SEVERITY_CRITICAL)

        def eligible_for_deletion(self):
            """
            Return events eligible for deletion per retention policy.

            Meta-commentary:
            - Events with retention_until in the past can be deleted
            - Events with retention_until=null are kept forever
            - This should be called from a tenant-aware background job
            """
            return self.filter(
                retention_until__isnull=False,
                retention_until__lte=timezone.now()
            )

        def since(self, start_date):
            """Return events since a given date."""
            return self.filter(timestamp__gte=start_date)

        def between(self, start_date, end_date):
            """Return events between two dates."""
            return self.filter(timestamp__gte=start_date, timestamp__lte=end_date)

    objects = AuditEventQuerySet.as_manager()

    class Meta:
        db_table = 'firm_audit_event'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['firm', 'category', '-timestamp'], name='firm_audit_firm_cat_ts_idx'),
            models.Index(fields=['firm', 'actor', '-timestamp'], name='firm_audit_firm_actor_ts_idx'),
            models.Index(fields=['category', '-timestamp'], name='firm_audit_cat_ts_idx'),
            models.Index(fields=['action', '-timestamp'], name='firm_audit_action_ts_idx'),
            models.Index(fields=['severity', '-timestamp'], name='firm_audit_severity_ts_idx'),
            models.Index(fields=['retention_until'], name='firm_audit_retention_idx'),
        ]
        # Prevent updates and deletes via Django ORM (immutable records)
        permissions = [
            ('view_audit_event', 'Can view audit events'),
            ('export_audit_event', 'Can export audit events'),
            # NOTE: No 'change' or 'delete' permissions - audit events are immutable
        ]

    def __str__(self):
        actor_str = self.actor.username if self.actor else "SYSTEM"
        return f"[{self.category}] {self.action} by {actor_str} at {self.timestamp}"

    @property
    def is_expired(self):
        """Check if this event is past its retention period."""
        if self.retention_until is None:
            return False  # Keep forever
        return timezone.now() >= self.retention_until

    def calculate_retention_until(self):
        """
        Calculate retention_until based on category retention policy.

        Returns None for categories with indefinite retention.
        """
        retention_days = self.RETENTION_POLICY.get(self.category)
        if retention_days is None:
            return None  # Keep forever
        return self.timestamp + timezone.timedelta(days=retention_days)

    def clean(self):
        """Validate audit event invariants."""
        # Ensure metadata is content-free (basic validation)
        if self.metadata:
            # Prevent accidental inclusion of sensitive keys
            forbidden_keys = ['password', 'token', 'secret', 'content', 'body', 'message_text']
            for key in forbidden_keys:
                if key in self.metadata:
                    raise ValidationError({
                        'metadata': f'Audit metadata must be content-free. Remove key: {key}'
                    })

        # Require reason for certain critical categories
        critical_categories = [
            self.CATEGORY_BREAK_GLASS,
            self.CATEGORY_PURGE,
        ]
        if self.category in critical_categories and not self.reason:
            raise ValidationError({
                'reason': f'Reason is required for {self.category} events'
            })

    def save(self, *args, **kwargs):
        """
        Save audit event (create-only, immutable).

        Meta-commentary:
        - Audit events are immutable: only allow creation, not updates
        - Calculate retention_until on creation if not already set
        - Run validation before saving
        """
        # Prevent updates (immutable records)
        if self.pk is not None:
            raise ValidationError('Audit events are immutable and cannot be updated.')

        # Calculate retention if not set
        if self.retention_until is None:
            self.retention_until = self.calculate_retention_until()

        # Run validation
        self.full_clean()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Prevent deletion via Django ORM.

        Meta-commentary:
        - Audit events should only be deleted via explicit retention cleanup jobs
        - This prevents accidental deletion via cascade or application logic
        """
        raise ValidationError('Audit events cannot be deleted via application code. Use retention cleanup jobs.')


# Audit Event Helper Functions

def create_audit_event(
    firm,
    category,
    action,
    actor=None,
    actor_ip=None,
    actor_user_agent=None,
    target_object=None,
    target_description='',
    client=None,
    reason='',
    metadata=None,
    severity=AuditEvent.SEVERITY_INFO,
):
    """
    Create an immutable audit event.

    This is the primary interface for writing audit events throughout the application.

    Args:
        firm: Firm instance (required for tenant scoping)
        category: Event category (use AuditEvent.CATEGORY_* constants)
        action: Action string (e.g., 'user.login', 'break_glass.activate')
        actor: User who performed the action (null for system events)
        actor_ip: IP address of actor
        actor_user_agent: User agent string
        target_object: Django model instance that was acted upon
        target_description: Human-readable description (survives target deletion)
        client: Client instance (if action is client-scoped)
        reason: Reason string (required for break-glass, purge, etc.)
        metadata: Content-free structured data (dict)
        severity: Event severity (info/warning/critical)

    Returns:
        AuditEvent instance

    Raises:
        ValueError: If firm is None or category is invalid
        ValidationError: If event validation fails

    Example:
        >>> create_audit_event(
        ...     firm=request.firm,
        ...     category=AuditEvent.CATEGORY_BREAK_GLASS,
        ...     action='break_glass.activate',
        ...     actor=request.user,
        ...     actor_ip=get_client_ip(request),
        ...     reason='Customer support case #12345',
        ...     severity=AuditEvent.SEVERITY_CRITICAL,
        ...     metadata={'session_id': session.id, 'duration_minutes': 60}
        ... )
    """
    if firm is None:
        raise ValueError("Firm context is required to create audit events.")

    if category not in dict(AuditEvent.CATEGORY_CHOICES):
        raise ValueError(f"Invalid audit category: {category}")

    event = AuditEvent(
        firm=firm,
        category=category,
        action=action,
        actor=actor,
        actor_ip=actor_ip,
        actor_user_agent=actor_user_agent,
        target_description=target_description,
        client=client,
        reason=reason,
        metadata=metadata or {},
        severity=severity,
    )

    # Set target object if provided
    if target_object:
        event.target_object = target_object

    event.save()
    return event


def get_audit_review_cadence(category):
    """
    Return recommended review cadence for a given audit event category.

    TIER 3 REQUIREMENT: Define review ownership, cadence, and escalation path

    Returns:
        dict with 'owner', 'cadence', and 'escalation_path' keys

    Example:
        >>> get_audit_review_cadence(AuditEvent.CATEGORY_BREAK_GLASS)
        {'owner': 'Platform Security Team', 'cadence': 'Weekly', 'escalation_path': [...]}
    """
    default_escalation = [
        'Review Owner',
        'Security Lead',
        'CTO/VP Engineering',
        'Legal/Compliance (if required)',
    ]
    review_policy = {
        AuditEvent.CATEGORY_AUTH: {
            'owner': 'Platform Operations',
            'cadence': 'Monthly',
            'description': 'Review authentication failures and anomalies',
            'escalation_path': default_escalation,
        },
        AuditEvent.CATEGORY_PERMISSIONS: {
            'owner': 'Platform Security Team',
            'cadence': 'Monthly',
            'description': 'Review permission changes and role escalations',
            'escalation_path': default_escalation,
        },
        AuditEvent.CATEGORY_BREAK_GLASS: {
            'owner': 'Platform Security Team',
            'cadence': 'Weekly',
            'description': 'Review all break-glass activations and content access',
            'escalation_path': [
                'Platform Security Team',
                'Security Lead',
                'CTO/VP Engineering',
                'Legal/Compliance (if required)',
            ],
        },
        AuditEvent.CATEGORY_BILLING_METADATA: {
            'owner': 'Finance Team',
            'cadence': 'Monthly',
            'description': 'Review billing metadata operations for compliance',
            'escalation_path': [
                'Finance Team Lead',
                'Security Lead',
                'CTO/VP Engineering',
                'Legal/Compliance (if required)',
            ],
        },
        AuditEvent.CATEGORY_PURGE: {
            'owner': 'Platform Security + Legal',
            'cadence': 'Weekly',
            'description': 'Review all data purge operations and reasons',
            'escalation_path': [
                'Platform Security + Legal',
                'Security Lead',
                'CTO/VP Engineering',
                'Legal/Compliance (if required)',
            ],
        },
        AuditEvent.CATEGORY_CONFIG: {
            'owner': 'Platform Operations',
            'cadence': 'Monthly',
            'description': 'Review configuration changes affecting security or billing',
            'escalation_path': default_escalation,
        },
        AuditEvent.CATEGORY_DATA_ACCESS: {
            'owner': 'Platform Operations',
            'cadence': 'Quarterly',
            'description': 'Review data access patterns for anomalies',
            'escalation_path': default_escalation,
        },
        AuditEvent.CATEGORY_ROLE_CHANGE: {
            'owner': 'Platform Security Team',
            'cadence': 'Monthly',
            'description': 'Review role and membership changes',
            'escalation_path': default_escalation,
        },
        AuditEvent.CATEGORY_EXPORT: {
            'owner': 'Platform Operations',
            'cadence': 'Quarterly',
            'description': 'Review data export operations',
            'escalation_path': default_escalation,
        },
        AuditEvent.CATEGORY_SIGNING: {
            'owner': 'Legal + Compliance',
            'cadence': 'As Needed',
            'description': 'Document signing evidence (review during disputes)',
            'escalation_path': [
                'Legal + Compliance',
                'Security Lead',
                'CTO/VP Engineering',
                'Legal/Compliance (if required)',
            ],
        },
    }

    return review_policy.get(category, {
        'owner': 'Platform Operations',
        'cadence': 'As Needed',
        'description': 'Review as required',
        'escalation_path': default_escalation,
    })
