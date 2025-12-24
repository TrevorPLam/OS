"""
Firm (Workspace) Models - Multi-Tenant Foundation

This module implements the top-level tenant boundary for the multi-firm SaaS platform.
All data isolation, authorization, and privacy guarantees depend on this boundary.

CRITICAL: This is Tier 0 - Foundational Safety.
Every firm-side object MUST belong to exactly one Firm.
"""
from django.db import models
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
