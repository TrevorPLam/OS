"""
DRF Serializers for Webhooks module.
"""

from rest_framework import serializers

from modules.webhooks.models import WebhookDelivery, WebhookEndpoint


class WebhookEndpointSerializer(serializers.ModelSerializer):
    """Serializer for WebhookEndpoint model (Task 3.7)."""
    
    success_rate = serializers.ReadOnlyField()
    subscribed_events_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = WebhookEndpoint
        fields = [
            "id",
            "firm",
            "name",
            "url",
            "description",
            "status",
            "subscribed_events",
            "subscribed_events_count",
            "secret",
            "max_retries",
            "retry_delay_seconds",
            "timeout_seconds",
            "rate_limit_per_minute",
            "total_deliveries",
            "successful_deliveries",
            "failed_deliveries",
            "success_rate",
            "last_delivery_at",
            "last_success_at",
            "last_failure_at",
            "metadata",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "secret",
            "total_deliveries",
            "successful_deliveries",
            "failed_deliveries",
            "success_rate",
            "last_delivery_at",
            "last_success_at",
            "last_failure_at",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "secret": {"write_only": True},  # Don't expose secret in list views by default
        }
    
    def get_subscribed_events_count(self, obj):
        """Get count of subscribed events."""
        if not obj.subscribed_events:
            return 0
        return len(obj.subscribed_events)
    
    def get_created_by_name(self, obj):
        """Get name of user who created the webhook."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
    
    def validate_subscribed_events(self, value):
        """Validate subscribed events is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of event types")
        
        # Validate event type format
        for event in value:
            if not isinstance(event, str):
                raise serializers.ValidationError("Event types must be strings")
            if not event or len(event) > 100:
                raise serializers.ValidationError("Event types must be 1-100 characters")
        
        return value
    
    def validate_metadata(self, value):
        """Validate metadata is a dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be a dictionary")
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Validate retry settings
        max_retries = attrs.get("max_retries", 0)
        if max_retries < 0:
            raise serializers.ValidationError({"max_retries": "Must be non-negative"})
        
        retry_delay = attrs.get("retry_delay_seconds", 1)
        if retry_delay < 1:
            raise serializers.ValidationError({"retry_delay_seconds": "Must be at least 1 second"})
        
        timeout = attrs.get("timeout_seconds", 1)
        if timeout < 1:
            raise serializers.ValidationError({"timeout_seconds": "Must be at least 1 second"})
        
        rate_limit = attrs.get("rate_limit_per_minute")
        if rate_limit is not None and rate_limit < 1:
            raise serializers.ValidationError({
                "rate_limit_per_minute": "Must be at least 1 per minute or null"
            })
        
        return attrs


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Serializer for WebhookDelivery model (Task 3.7)."""
    
    webhook_endpoint_name = serializers.CharField(source="webhook_endpoint.name", read_only=True)
    webhook_endpoint_url = serializers.CharField(source="webhook_endpoint.url", read_only=True)
    is_success = serializers.ReadOnlyField()
    duration_seconds = serializers.ReadOnlyField()
    
    class Meta:
        model = WebhookDelivery
        fields = [
            "id",
            "webhook_endpoint",
            "webhook_endpoint_name",
            "webhook_endpoint_url",
            "event_type",
            "event_id",
            "payload",
            "status",
            "attempts",
            "http_status_code",
            "response_headers",
            "response_body",
            "error_message",
            "created_at",
            "first_attempt_at",
            "last_attempt_at",
            "next_retry_at",
            "completed_at",
            "signature",
            "is_success",
            "duration_seconds",
        ]
        read_only_fields = [
            "id",
            "signature",
            "attempts",
            "http_status_code",
            "response_headers",
            "response_body",
            "error_message",
            "created_at",
            "first_attempt_at",
            "last_attempt_at",
            "next_retry_at",
            "completed_at",
            "is_success",
            "duration_seconds",
        ]
    
    def validate_payload(self, value):
        """Validate payload is a dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be a dictionary")
        return value


class WebhookEventSerializer(serializers.Serializer):
    """Serializer for webhook event data (for testing webhooks)."""
    
    event_type = serializers.CharField(
        max_length=100,
        help_text="Event type to trigger (e.g., 'test.event')"
    )
    payload = serializers.JSONField(
        help_text="Event payload data"
    )
    
    def validate_event_type(self, value):
        """Validate event type format."""
        if not value or len(value) > 100:
            raise serializers.ValidationError("Event type must be 1-100 characters")
        return value
    
    def validate_payload(self, value):
        """Validate payload is a dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be a dictionary")
        return value
