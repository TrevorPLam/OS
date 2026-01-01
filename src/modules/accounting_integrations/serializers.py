"""Serializers for Accounting Integrations API."""

from rest_framework import serializers
from .models import AccountingOAuthConnection, InvoiceSyncMapping, CustomerSyncMapping


class AccountingOAuthConnectionSerializer(serializers.ModelSerializer):
    """Serializer for accounting OAuth connections."""

    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    needs_refresh = serializers.SerializerMethodField()

    class Meta:
        model = AccountingOAuthConnection
        fields = [
            'connection_id',
            'provider',
            'provider_display',
            'provider_company_id',
            'provider_company_name',
            'status',
            'status_display',
            'needs_refresh',
            'sync_enabled',
            'invoice_sync_enabled',
            'payment_sync_enabled',
            'customer_sync_enabled',
            'last_invoice_sync_at',
            'last_payment_sync_at',
            'last_customer_sync_at',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'connection_id',
            'provider_company_id',
            'provider_company_name',
            'status',
            'last_invoice_sync_at',
            'last_payment_sync_at',
            'last_customer_sync_at',
            'error_message',
            'created_at',
            'updated_at',
        ]

    def get_needs_refresh(self, obj):
        """Check if connection needs token refresh."""
        return obj.needs_refresh()


class InvoiceSyncMappingSerializer(serializers.ModelSerializer):
    """Serializer for invoice sync mappings."""

    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    invoice_total = serializers.DecimalField(
        source='invoice.total_amount',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    provider = serializers.CharField(source='connection.provider', read_only=True)

    class Meta:
        model = InvoiceSyncMapping
        fields = [
            'mapping_id',
            'invoice',
            'invoice_number',
            'invoice_total',
            'provider',
            'external_id',
            'external_number',
            'sync_status',
            'sync_error',
            'last_synced_at',
            'created_at',
        ]
        read_only_fields = [
            'mapping_id',
            'external_id',
            'external_number',
            'sync_status',
            'sync_error',
            'last_synced_at',
            'created_at',
        ]


class CustomerSyncMappingSerializer(serializers.ModelSerializer):
    """Serializer for customer sync mappings."""

    client_name = serializers.CharField(source='client.name', read_only=True)
    provider = serializers.CharField(source='connection.provider', read_only=True)

    class Meta:
        model = CustomerSyncMapping
        fields = [
            'mapping_id',
            'client',
            'client_name',
            'provider',
            'external_id',
            'external_name',
            'sync_status',
            'sync_error',
            'last_synced_at',
            'created_at',
        ]
        read_only_fields = [
            'mapping_id',
            'external_id',
            'external_name',
            'sync_status',
            'sync_error',
            'last_synced_at',
            'created_at',
        ]
