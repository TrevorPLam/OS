"""
Accounting Integration Models.

Models for managing OAuth connections to accounting platforms
(QuickBooks Online, Xero) and sync state management.
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from modules.firm.models import Firm
from modules.firm.utils import FirmScopedManager


class AccountingOAuthConnection(models.Model):
    """
    OAuth connection to external accounting provider.

    Stores encrypted credentials for syncing with QuickBooks Online,
    Xero, or other accounting platforms.
    """

    PROVIDER_CHOICES = [
        ('quickbooks', 'QuickBooks Online'),
        ('xero', 'Xero'),
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
        related_name='accounting_oauth_connections',
        help_text='Firm this connection belongs to'
    )

    # Owner
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accounting_oauth_connections',
        help_text='Staff user who owns this connection'
    )

    # Provider
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text='Accounting provider'
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
    provider_company_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Provider company/organization ID (QuickBooks: realmId, Xero: tenantId)'
    )
    provider_company_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Name of the connected company in the accounting system'
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
    invoice_sync_enabled = models.BooleanField(
        default=True,
        help_text='Sync invoices to accounting system'
    )
    payment_sync_enabled = models.BooleanField(
        default=True,
        help_text='Sync payments from accounting system'
    )
    customer_sync_enabled = models.BooleanField(
        default=True,
        help_text='Sync customers/contacts bidirectionally'
    )

    # Sync Status
    last_invoice_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful invoice sync timestamp'
    )
    last_payment_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful payment sync timestamp'
    )
    last_customer_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful customer sync timestamp'
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
        db_table = 'accounting_oauth_connections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'user', 'provider']),
            models.Index(fields=['firm', 'status']),
            models.Index(fields=['provider', 'status']),
        ]
        # One connection per firm per provider
        unique_together = [('firm', 'provider')]

    def __str__(self):
        return f"{self.provider} - {self.firm.name}"

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
        from datetime import timedelta
        threshold = timezone.now() + timedelta(minutes=5)
        return self.token_expires_at <= threshold


class InvoiceSyncMapping(models.Model):
    """
    Mapping between internal Invoice and external accounting system invoice.

    Tracks synchronization state and handles bidirectional mapping.
    """

    # Identity
    mapping_id = models.BigAutoField(primary_key=True)

    # Relationships
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='invoice_sync_mappings',
        help_text='Firm this mapping belongs to'
    )
    connection = models.ForeignKey(
        AccountingOAuthConnection,
        on_delete=models.CASCADE,
        related_name='invoice_mappings',
        help_text='Accounting connection used'
    )
    invoice = models.ForeignKey(
        'finance.Invoice',
        on_delete=models.CASCADE,
        related_name='accounting_sync_mappings',
        help_text='Internal invoice'
    )

    # External Reference
    external_id = models.CharField(
        max_length=255,
        help_text='Invoice ID in external accounting system'
    )
    external_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Invoice number in external accounting system'
    )

    # Sync State
    last_synced_at = models.DateTimeField(
        auto_now=True,
        help_text='Last sync timestamp'
    )
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('synced', 'Synced'),
            ('pending', 'Pending Sync'),
            ('error', 'Sync Error'),
        ],
        default='synced',
        help_text='Current sync status'
    )
    sync_error = models.TextField(
        blank=True,
        help_text='Error message if sync failed'
    )

    # Metadata
    external_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata from external system'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'accounting_invoice_sync_mappings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'invoice']),
            models.Index(fields=['connection', 'external_id']),
            models.Index(fields=['firm', 'sync_status']),
        ]
        # One mapping per invoice per connection
        unique_together = [('connection', 'invoice')]

    def __str__(self):
        return f"{self.invoice} -> {self.connection.provider}:{self.external_id}"


class CustomerSyncMapping(models.Model):
    """
    Mapping between internal Client and external accounting system customer/contact.

    Tracks synchronization state and handles bidirectional mapping.
    """

    # Identity
    mapping_id = models.BigAutoField(primary_key=True)

    # Relationships
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='customer_sync_mappings',
        help_text='Firm this mapping belongs to'
    )
    connection = models.ForeignKey(
        AccountingOAuthConnection,
        on_delete=models.CASCADE,
        related_name='customer_mappings',
        help_text='Accounting connection used'
    )
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='accounting_sync_mappings',
        help_text='Internal client'
    )

    # External Reference
    external_id = models.CharField(
        max_length=255,
        help_text='Customer/Contact ID in external accounting system'
    )
    external_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Customer/Contact name in external accounting system'
    )

    # Sync State
    last_synced_at = models.DateTimeField(
        auto_now=True,
        help_text='Last sync timestamp'
    )
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('synced', 'Synced'),
            ('pending', 'Pending Sync'),
            ('error', 'Sync Error'),
        ],
        default='synced',
        help_text='Current sync status'
    )
    sync_error = models.TextField(
        blank=True,
        help_text='Error message if sync failed'
    )

    # Metadata
    external_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata from external system'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'accounting_customer_sync_mappings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'client']),
            models.Index(fields=['connection', 'external_id']),
            models.Index(fields=['firm', 'sync_status']),
        ]
        # One mapping per client per connection
        unique_together = [('connection', 'client')]

    def __str__(self):
        return f"{self.client} -> {self.connection.provider}:{self.external_id}"
