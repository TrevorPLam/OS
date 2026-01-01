"""Admin configuration for Accounting Integrations."""

from django.contrib import admin
from .models import AccountingOAuthConnection, InvoiceSyncMapping, CustomerSyncMapping


@admin.register(AccountingOAuthConnection)
class AccountingOAuthConnectionAdmin(admin.ModelAdmin):
    """Admin interface for accounting OAuth connections."""

    list_display = [
        'connection_id',
        'firm',
        'provider',
        'provider_company_name',
        'status',
        'sync_enabled',
        'created_at',
    ]
    list_filter = ['provider', 'status', 'sync_enabled', 'created_at']
    search_fields = ['firm__name', 'provider_company_name', 'provider_company_id']
    readonly_fields = [
        'connection_id',
        'access_token',
        'refresh_token',
        'token_expires_at',
        'created_at',
        'updated_at',
    ]
    fieldsets = [
        ('Identity', {
            'fields': ['connection_id', 'firm', 'user', 'provider']
        }),
        ('OAuth Credentials', {
            'fields': [
                'access_token',
                'refresh_token',
                'token_expires_at',
                'scopes',
            ],
            'classes': ['collapse'],
        }),
        ('Provider Information', {
            'fields': [
                'provider_company_id',
                'provider_company_name',
                'provider_metadata',
            ]
        }),
        ('Sync Configuration', {
            'fields': [
                'sync_enabled',
                'invoice_sync_enabled',
                'payment_sync_enabled',
                'customer_sync_enabled',
            ]
        }),
        ('Sync Status', {
            'fields': [
                'last_invoice_sync_at',
                'last_payment_sync_at',
                'last_customer_sync_at',
            ]
        }),
        ('Status', {
            'fields': ['status', 'error_message']
        }),
        ('Audit', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]


@admin.register(InvoiceSyncMapping)
class InvoiceSyncMappingAdmin(admin.ModelAdmin):
    """Admin interface for invoice sync mappings."""

    list_display = [
        'mapping_id',
        'firm',
        'invoice',
        'connection',
        'external_id',
        'external_number',
        'sync_status',
        'last_synced_at',
    ]
    list_filter = ['sync_status', 'connection__provider', 'created_at']
    search_fields = [
        'invoice__invoice_number',
        'external_id',
        'external_number',
        'firm__name',
    ]
    readonly_fields = [
        'mapping_id',
        'last_synced_at',
        'created_at',
        'updated_at',
    ]
    fieldsets = [
        ('Identity', {
            'fields': ['mapping_id', 'firm', 'connection', 'invoice']
        }),
        ('External Reference', {
            'fields': ['external_id', 'external_number', 'external_metadata']
        }),
        ('Sync Status', {
            'fields': ['sync_status', 'sync_error', 'last_synced_at']
        }),
        ('Audit', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]


@admin.register(CustomerSyncMapping)
class CustomerSyncMappingAdmin(admin.ModelAdmin):
    """Admin interface for customer sync mappings."""

    list_display = [
        'mapping_id',
        'firm',
        'client',
        'connection',
        'external_id',
        'external_name',
        'sync_status',
        'last_synced_at',
    ]
    list_filter = ['sync_status', 'connection__provider', 'created_at']
    search_fields = [
        'client__name',
        'client__email',
        'external_id',
        'external_name',
        'firm__name',
    ]
    readonly_fields = [
        'mapping_id',
        'last_synced_at',
        'created_at',
        'updated_at',
    ]
    fieldsets = [
        ('Identity', {
            'fields': ['mapping_id', 'firm', 'connection', 'client']
        }),
        ('External Reference', {
            'fields': ['external_id', 'external_name', 'external_metadata']
        }),
        ('Sync Status', {
            'fields': ['sync_status', 'sync_error', 'last_synced_at']
        }),
        ('Audit', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]
