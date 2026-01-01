"""Django admin configuration for e-signature models."""

from django.contrib import admin

from modules.esignature.models import DocuSignConnection, Envelope, WebhookEvent


@admin.register(DocuSignConnection)
class DocuSignConnectionAdmin(admin.ModelAdmin):
    """Admin interface for DocuSign connections."""
    
    list_display = [
        "firm",
        "account_name",
        "account_id",
        "is_active",
        "is_token_expired_display",
        "connected_at",
        "last_sync_at",
    ]
    
    list_filter = [
        "is_active",
        "connected_at",
    ]
    
    search_fields = [
        "firm__name",
        "account_name",
        "account_id",
    ]
    
    readonly_fields = [
        "firm",
        "account_id",
        "account_name",
        "base_uri",
        "connected_at",
        "connected_by",
        "last_sync_at",
        "last_error",
        "created_at",
        "updated_at",
        "is_token_expired_display",
    ]
    
    fieldsets = (
        ("Connection Information", {
            "fields": (
                "firm",
                "account_id",
                "account_name",
                "base_uri",
                "is_active",
            )
        }),
        ("Status", {
            "fields": (
                "is_token_expired_display",
                "connected_at",
                "connected_by",
                "last_sync_at",
                "last_error",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",)
        }),
    )
    
    def is_token_expired_display(self, obj):
        """Display whether token is expired."""
        return obj.is_token_expired()
    is_token_expired_display.short_description = "Token Expired"
    is_token_expired_display.boolean = True
    
    def has_add_permission(self, request):
        """Connections are created via OAuth flow, not admin."""
        return False


@admin.register(Envelope)
class EnvelopeAdmin(admin.ModelAdmin):
    """Admin interface for envelopes."""
    
    list_display = [
        "envelope_id",
        "firm",
        "status",
        "linked_entity_display",
        "subject",
        "created_at",
        "completed_at",
    ]
    
    list_filter = [
        "status",
        "created_at",
    ]
    
    search_fields = [
        "envelope_id",
        "firm__name",
        "subject",
        "proposal__proposal_number",
        "contract__contract_number",
    ]
    
    readonly_fields = [
        "firm",
        "connection",
        "envelope_id",
        "status",
        "proposal",
        "contract",
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
        "created_by",
    ]
    
    fieldsets = (
        ("Envelope Information", {
            "fields": (
                "firm",
                "connection",
                "envelope_id",
                "status",
            )
        }),
        ("Linked Entity", {
            "fields": (
                "proposal",
                "contract",
            )
        }),
        ("Email Details", {
            "fields": (
                "subject",
                "message",
            )
        }),
        ("Recipients", {
            "fields": (
                "recipients",
            )
        }),
        ("Status Tracking", {
            "fields": (
                "sent_at",
                "delivered_at",
                "signed_at",
                "completed_at",
                "voided_at",
                "voided_reason",
                "error_message",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
                "updated_at",
                "created_by",
            ),
            "classes": ("collapse",)
        }),
    )
    
    def linked_entity_display(self, obj):
        """Display linked proposal or contract."""
        if obj.proposal:
            return f"Proposal: {obj.proposal.proposal_number}"
        elif obj.contract:
            return f"Contract: {obj.contract.contract_number}"
        return "None"
    linked_entity_display.short_description = "Linked To"
    
    def has_add_permission(self, request):
        """Envelopes are created via API, not admin."""
        return False


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Admin interface for webhook events."""
    
    list_display = [
        "envelope_id",
        "event_type",
        "event_status",
        "processed",
        "received_at",
    ]
    
    list_filter = [
        "processed",
        "event_type",
        "event_status",
        "received_at",
    ]
    
    search_fields = [
        "envelope_id",
        "event_type",
    ]
    
    readonly_fields = [
        "envelope",
        "envelope_id",
        "event_type",
        "event_status",
        "payload",
        "headers",
        "processed",
        "processed_at",
        "error_message",
        "received_at",
    ]
    
    fieldsets = (
        ("Event Information", {
            "fields": (
                "envelope",
                "envelope_id",
                "event_type",
                "event_status",
            )
        }),
        ("Payload", {
            "fields": (
                "payload",
                "headers",
            ),
            "classes": ("collapse",)
        }),
        ("Processing Status", {
            "fields": (
                "processed",
                "processed_at",
                "error_message",
            )
        }),
        ("Metadata", {
            "fields": (
                "received_at",
            )
        }),
    )
    
    def has_add_permission(self, request):
        """Webhook events are created by webhooks, not admin."""
        return False
