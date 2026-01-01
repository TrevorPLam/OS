"""
Django Admin configuration for Webhooks models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import WebhookDelivery, WebhookEndpoint


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "url_display",
        "status",
        "subscribed_events_count",
        "success_rate_display",
        "total_deliveries",
        "last_delivery_at",
    ]
    list_filter = ["status", "created_at", "last_delivery_at"]
    search_fields = ["name", "url", "description"]
    readonly_fields = [
        "secret",
        "total_deliveries",
        "successful_deliveries",
        "failed_deliveries",
        "last_delivery_at",
        "last_success_at",
        "last_failure_at",
        "success_rate_display",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["firm", "created_by"]
    
    fieldsets = (
        ("Webhook Configuration", {
            "fields": ("firm", "name", "url", "description", "status")
        }),
        ("Event Subscriptions", {
            "fields": ("subscribed_events",)
        }),
        ("Authentication", {
            "fields": ("secret",),
            "classes": ("collapse",)
        }),
        ("Delivery Settings", {
            "fields": (
                "max_retries",
                "retry_delay_seconds",
                "timeout_seconds",
                "rate_limit_per_minute",
            )
        }),
        ("Statistics", {
            "fields": (
                "total_deliveries",
                "successful_deliveries",
                "failed_deliveries",
                "success_rate_display",
                "last_delivery_at",
                "last_success_at",
                "last_failure_at",
            ),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("metadata",),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def url_display(self, obj):
        """Display truncated URL."""
        if len(obj.url) > 50:
            return f"{obj.url[:47]}..."
        return obj.url
    url_display.short_description = "URL"
    
    def subscribed_events_count(self, obj):
        """Display count of subscribed events."""
        if not obj.subscribed_events:
            return "0"
        return str(len(obj.subscribed_events))
    subscribed_events_count.short_description = "Subscribed Events"
    
    def success_rate_display(self, obj):
        """Display success rate with color coding."""
        rate = obj.success_rate
        if rate >= 95:
            color = "green"
        elif rate >= 80:
            color = "orange"
        else:
            color = "red"
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            rate
        )
    success_rate_display.short_description = "Success Rate"
    
    actions = ["regenerate_secret", "pause_webhooks", "activate_webhooks"]
    
    def regenerate_secret(self, request, queryset):
        """Regenerate secret keys for selected webhooks."""
        count = 0
        for endpoint in queryset:
            endpoint.secret = endpoint._generate_secret()
            endpoint.save()
            count += 1
        self.message_user(request, f"Regenerated secrets for {count} webhook endpoint(s).")
    regenerate_secret.short_description = "Regenerate secret keys"
    
    def pause_webhooks(self, request, queryset):
        """Pause selected webhooks."""
        count = queryset.update(status="paused")
        self.message_user(request, f"Paused {count} webhook endpoint(s).")
    pause_webhooks.short_description = "Pause selected webhooks"
    
    def activate_webhooks(self, request, queryset):
        """Activate selected webhooks."""
        count = queryset.update(status="active")
        self.message_user(request, f"Activated {count} webhook endpoint(s).")
    activate_webhooks.short_description = "Activate selected webhooks"


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = [
        "event_type",
        "webhook_endpoint",
        "status",
        "attempts",
        "http_status_code",
        "created_at",
        "completed_at",
    ]
    list_filter = ["status", "event_type", "http_status_code", "created_at"]
    search_fields = ["event_type", "event_id", "webhook_endpoint__name"]
    readonly_fields = [
        "event_id",
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
    raw_id_fields = ["webhook_endpoint"]
    
    fieldsets = (
        ("Webhook", {
            "fields": ("webhook_endpoint",)
        }),
        ("Event", {
            "fields": ("event_type", "event_id", "payload")
        }),
        ("Delivery Status", {
            "fields": ("status", "attempts")
        }),
        ("Response", {
            "fields": (
                "http_status_code",
                "response_headers",
                "response_body",
                "error_message",
                "is_success",
            )
        }),
        ("Timing", {
            "fields": (
                "created_at",
                "first_attempt_at",
                "last_attempt_at",
                "next_retry_at",
                "completed_at",
                "duration_seconds",
            )
        }),
        ("Authentication", {
            "fields": ("signature",),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["retry_failed_deliveries"]
    
    def retry_failed_deliveries(self, request, queryset):
        """Mark failed deliveries for retry."""
        count = 0
        for delivery in queryset.filter(status="failed"):
            if delivery.should_retry():
                delivery.status = "retrying"
                delivery.next_retry_at = delivery.calculate_next_retry_time()
                delivery.save()
                count += 1
        self.message_user(request, f"Marked {count} delivery(s) for retry.")
    retry_failed_deliveries.short_description = "Retry failed deliveries"
