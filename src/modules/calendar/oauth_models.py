"""
Calendar OAuth Models.

Models for managing OAuth connections to external calendar providers
(Google Calendar, Microsoft Outlook).
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from modules.firm.models import Firm
from modules.firm.utils import FirmScopedManager


class OAuthConnection(models.Model):
    """
    OAuth connection to external calendar provider.

    Stores encrypted credentials for syncing with Google Calendar,
    Microsoft Outlook, or other calendar providers.
    """

    PROVIDER_CHOICES = [
        ('google', 'Google Calendar'),
        ('microsoft', 'Microsoft Outlook/Office 365'),
        ('apple', 'Apple Calendar (iCloud)'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired (Token Refresh Needed)'),
        ('revoked', 'Revoked'),
        ('error', 'Error'),
    ]

    # Identity
    connection_id = models.BigAutoField(primary_key=True)

    # Tenancy
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='oauth_calendar_connections',
        help_text='Firm this connection belongs to'
    )

    # Owner
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_oauth_connections',
        help_text='Staff user who owns this connection'
    )

    # Provider
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text='Calendar provider'
    )

    # OAuth Credentials (encrypted at rest)
    access_token = models.TextField(
        blank=True,
        help_text='Encrypted OAuth access token'
    )
    refresh_token = models.TextField(
        blank=True,
        help_text='Encrypted OAuth refresh token'
    )
    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When access token expires'
    )

    # Scopes and Permissions
    scopes = models.JSONField(
        default=list,
        blank=True,
        help_text='OAuth scopes granted'
    )

    # Provider-specific metadata
    provider_user_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Provider user ID (Google: email, Microsoft: user ID)'
    )
    provider_email = models.EmailField(
        blank=True,
        help_text='Email address of connected calendar'
    )
    provider_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional provider-specific metadata'
    )

    # Sync Configuration
    sync_enabled = models.BooleanField(
        default=True,
        help_text='Whether automatic sync is enabled'
    )
    sync_window_days = models.IntegerField(
        default=30,
        help_text='Number of days to sync (past and future)'
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful sync timestamp'
    )
    last_sync_cursor = models.TextField(
        blank=True,
        help_text='Sync cursor/token from provider (for delta sync)'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Connection status'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Last error message if status=error'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'calendar_oauth_connections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'user', 'provider']),
            models.Index(fields=['firm', 'status']),
            models.Index(fields=['provider', 'status']),
        ]
        # One connection per user per provider per firm
        unique_together = [('firm', 'user', 'provider')]

    def __str__(self):
        return f"{self.provider} - {self.user.username} ({self.firm.name})"

    def is_token_expired(self):
        """Check if access token is expired."""
        if not self.token_expires_at:
            return False
        return timezone.now() >= self.token_expires_at

    def needs_refresh(self):
        """Check if token needs refresh (expired or expiring soon)."""
        if not self.token_expires_at:
            return False
        # Refresh if token expires in less than 5 minutes
        threshold = timezone.now() + timezone.timedelta(minutes=5)
        return self.token_expires_at <= threshold


class OAuthAuthorizationCode(models.Model):
    """
    Temporary storage for OAuth authorization codes.

    Used during OAuth flow before exchanging code for tokens.
    Codes expire after a short time (typically 10 minutes).
    """

    STATE_CHOICES = [
        ('pending', 'Pending Exchange'),
        ('exchanged', 'Exchanged for Tokens'),
        ('expired', 'Expired'),
        ('error', 'Error'),
    ]

    # Identity
    code_id = models.BigAutoField(primary_key=True)

    # Session tracking
    state_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='OAuth state parameter for CSRF protection'
    )

    # User context
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='oauth_authorization_codes',
        help_text='Firm for this authorization'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='oauth_authorization_codes',
        help_text='User initiating OAuth flow'
    )

    # Provider
    provider = models.CharField(
        max_length=20,
        choices=OAuthConnection.PROVIDER_CHOICES,
        help_text='Calendar provider'
    )

    # Authorization data
    authorization_code = models.TextField(
        blank=True,
        help_text='OAuth authorization code from provider'
    )
    redirect_uri = models.URLField(
        max_length=512,
        help_text='Redirect URI used in OAuth flow'
    )

    # State
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='pending',
        help_text='Authorization code state'
    )

    # Expiration
    expires_at = models.DateTimeField(
        help_text='When this code expires'
    )

    # Result
    connection = models.ForeignKey(
        OAuthConnection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorization_codes',
        help_text='Resulting connection (after exchange)'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if exchange failed'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    exchanged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When code was exchanged'
    )

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'calendar_oauth_authorization_codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state_token']),
            models.Index(fields=['firm', 'user', 'state']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.provider} auth code for {self.user.username}"

    def is_expired(self):
        """Check if authorization code is expired."""
        return timezone.now() >= self.expires_at

    def is_valid(self):
        """Check if authorization code is valid for exchange."""
        return (
            self.state == 'pending' and
            not self.is_expired() and
            self.authorization_code
        )

    def save(self, *args, **kwargs):
        """Set default expiration if not set."""
        if not self.expires_at:
            # Default: 10 minutes
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
