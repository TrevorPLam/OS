"""Serializers for e-signature API endpoints."""

from rest_framework import serializers

from modules.esignature.models import DocuSignConnection, Envelope, WebhookEvent


class DocuSignConnectionSerializer(serializers.ModelSerializer):
    """Serializer for DocuSign connection (read-only, excludes sensitive tokens)."""
    
    firm_name = serializers.CharField(source="firm.name", read_only=True)
    is_token_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = DocuSignConnection
        fields = [
            "id",
            "firm",
            "firm_name",
            "account_id",
            "account_name",
            "base_uri",
            "is_active",
            "is_token_expired",
            "connected_at",
            "last_sync_at",
            "last_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
    
    def get_is_token_expired(self, obj):
        """Check if token is expired."""
        return obj.is_token_expired()


class EnvelopeSerializer(serializers.ModelSerializer):
    """Serializer for envelope information."""
    
    firm_name = serializers.CharField(source="firm.name", read_only=True)
    proposal_number = serializers.CharField(source="proposal.proposal_number", read_only=True, allow_null=True)
    contract_number = serializers.CharField(source="contract.contract_number", read_only=True, allow_null=True)
    
    class Meta:
        model = Envelope
        fields = [
            "id",
            "firm",
            "firm_name",
            "envelope_id",
            "status",
            "proposal",
            "proposal_number",
            "contract",
            "contract_number",
            "subject",
            "message",
            "recipients",
            "sent_at",
            "delivered_at",
            "signed_at",
            "completed_at",
            "voided_at",
            "voided_reason",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class WebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for webhook event logs."""
    
    class Meta:
        model = WebhookEvent
        fields = [
            "id",
            "envelope",
            "envelope_id",
            "event_type",
            "event_status",
            "processed",
            "processed_at",
            "error_message",
            "received_at",
        ]
        read_only_fields = fields
