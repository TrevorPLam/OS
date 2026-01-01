"""
Webhooks Models: WebhookEndpoint, WebhookDelivery.

This module provides a general webhook platform for external integrations (Task 3.7).

TIER 0: All webhook entities MUST belong to exactly one Firm for tenant isolation.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class WebhookEndpoint(models.Model):
    """
    WebhookEndpoint represents a registered webhook receiver (Task 3.7).
    
    External systems register webhook endpoints to receive real-time
    notifications about events in the system. Each endpoint can subscribe
    to specific event types and has authentication credentials.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("disabled", "Disabled"),
    ]
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="webhook_endpoints",
        help_text="Firm (workspace) this webhook belongs to"
    )
    
    # Endpoint Configuration
    name = models.CharField(
        max_length=255,
        help_text="Descriptive name for this webhook endpoint"
    )
    url = models.URLField(
        max_length=2048,
        validators=[validate_safe_url],
        help_text="URL to POST webhook events to"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this webhook is for"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Webhook status (active, paused, disabled)"
    )
    
    # Event Subscriptions
    subscribed_events = models.JSONField(
        default=list,
        help_text="List of event types this endpoint subscribes to (e.g., ['client.created', 'project.updated'])"
    )
    
    # Authentication
    secret = models.CharField(
        max_length=255,
        help_text="Secret key for HMAC signature verification (auto-generated)"
    )
    
    # Delivery Settings
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retry attempts for failed deliveries"
    )
    retry_delay_seconds = models.IntegerField(
        default=60,
        help_text="Initial retry delay in seconds (exponential backoff applied)"
    )
    timeout_seconds = models.IntegerField(
        default=30,
        help_text="HTTP request timeout in seconds"
    )
    
    # Rate Limiting
    rate_limit_per_minute = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum events per minute (null = no limit)"
    )
    
    # Statistics
    total_deliveries = models.IntegerField(
        default=0,
        help_text="Total number of delivery attempts"
    )
    successful_deliveries = models.IntegerField(
        default=0,
        help_text="Number of successful deliveries (HTTP 2xx)"
    )
    failed_deliveries = models.IntegerField(
        default=0,
        help_text="Number of failed deliveries"
    )
    last_delivery_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last delivery attempt"
    )
    last_success_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last successful delivery"
    )
    last_failure_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last failed delivery"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata for this webhook (custom fields)"
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_webhook_endpoints",
        help_text="User who created this webhook"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager
    objects = FirmScopedManager()
    
    class Meta:
        db_table = "webhooks_endpoint"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="webhook_ep_firm_status_idx"),
            models.Index(fields=["status"], name="webhook_ep_status_idx"),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.url})"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to generate secret if not set."""
        if not self.secret:
            self.secret = self._generate_secret()
        super().save(*args, **kwargs)
    
    @staticmethod
    def _generate_secret():
        """Generate a random secret key for webhook signing."""
        return secrets.token_urlsafe(32)
    
    def generate_signature(self, payload: str) -> str:
        """
        Generate HMAC SHA-256 signature for payload.
        
        Args:
            payload: JSON string payload to sign
            
        Returns:
            Hex-encoded HMAC signature
        """
        return hmac.new(
            self.secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify HMAC signature for payload.
        
        Args:
            payload: JSON string payload
            signature: Hex-encoded HMAC signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = self.generate_signature(payload)
        return hmac.compare_digest(signature, expected_signature)
    
    def is_subscribed_to(self, event_type: str) -> bool:
        """Check if this endpoint is subscribed to an event type."""
        if not self.subscribed_events:
            return False
        
        # Support wildcard subscriptions (e.g., "client.*" matches "client.created")
        for subscribed in self.subscribed_events:
            if subscribed == event_type:
                return True
            if subscribed.endswith(".*"):
                prefix = subscribed[:-2]
                if event_type.startswith(f"{prefix}."):
                    return True
        
        return False
    
    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_deliveries == 0:
            return 0.0
        return (self.successful_deliveries / self.total_deliveries) * 100.0
    
    def clean(self):
        """Validate webhook endpoint."""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Validate subscribed events is a list
        if not isinstance(self.subscribed_events, list):
            errors["subscribed_events"] = "Must be a list of event types"
        
        # Validate metadata is a dict
        if not isinstance(self.metadata, dict):
            errors["metadata"] = "Must be a dictionary"
        
        # Validate retry settings
        if self.max_retries < 0:
            errors["max_retries"] = "Must be non-negative"
        
        if self.retry_delay_seconds < 1:
            errors["retry_delay_seconds"] = "Must be at least 1 second"
        
        if self.timeout_seconds < 1:
            errors["timeout_seconds"] = "Must be at least 1 second"
        
        if self.rate_limit_per_minute is not None and self.rate_limit_per_minute < 1:
            errors["rate_limit_per_minute"] = "Must be at least 1 per minute or null"
        
        if errors:
            raise ValidationError(errors)


class WebhookDelivery(models.Model):
    """
    WebhookDelivery tracks individual webhook event deliveries (Task 3.7).
    
    Each time an event is sent to a webhook endpoint, a delivery record is created
    to track the status, response, and retry attempts.
    
    TIER 0: Inherits firm from webhook_endpoint.
    """
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sending", "Sending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("retrying", "Retrying"),
    ]
    
    # Webhook Reference
    webhook_endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name="deliveries",
        help_text="Webhook endpoint this delivery is for"
    )
    
    # Event Data
    event_type = models.CharField(
        max_length=100,
        help_text="Event type (e.g., 'client.created', 'project.updated')"
    )
    event_id = models.CharField(
        max_length=255,
        help_text="Unique identifier for this event"
    )
    payload = models.JSONField(
        help_text="Event payload (data sent to webhook)"
    )
    
    # Delivery Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current delivery status"
    )
    attempts = models.IntegerField(
        default=0,
        help_text="Number of delivery attempts made"
    )
    
    # Response Data
    http_status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP response status code from webhook endpoint"
    )
    response_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="HTTP response headers from webhook endpoint"
    )
    response_body = models.TextField(
        blank=True,
        help_text="HTTP response body from webhook endpoint"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if delivery failed"
    )
    
    # Timing
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this delivery was created"
    )
    first_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of first delivery attempt"
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of most recent delivery attempt"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of next retry attempt (if retrying)"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when delivery completed (success or final failure)"
    )
    
    # Signature
    signature = models.CharField(
        max_length=255,
        blank=True,
        help_text="HMAC signature sent in request headers"
    )
    
    class Meta:
        db_table = "webhooks_delivery"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["webhook_endpoint", "status"], name="webhook_del_ep_status_idx"),
            models.Index(fields=["event_type"], name="webhook_del_event_idx"),
            models.Index(fields=["status", "next_retry_at"], name="webhook_del_retry_idx"),
            models.Index(fields=["created_at"], name="webhook_del_created_idx"),
        ]
        verbose_name_plural = "Webhook Deliveries"
    
    def __str__(self):
        return f"{self.event_type} to {self.webhook_endpoint.name} ({self.status})"
    
    def calculate_next_retry_time(self):
        """
        Calculate next retry time using exponential backoff.
        
        Formula: initial_delay * (2 ** attempts)
        Example: 60s, 120s, 240s, 480s, ...
        """
        if not self.webhook_endpoint:
            return None
        
        delay_seconds = self.webhook_endpoint.retry_delay_seconds * (2 ** self.attempts)
        return timezone.now() + timedelta(seconds=delay_seconds)
    
    def should_retry(self) -> bool:
        """Check if this delivery should be retried."""
        if self.status in ["success", "failed"]:
            return False
        
        if self.attempts >= self.webhook_endpoint.max_retries:
            return False
        
        return True
    
    @property
    def is_success(self) -> bool:
        """Check if delivery was successful (HTTP 2xx)."""
        return self.http_status_code is not None and 200 <= self.http_status_code < 300
    
    @property
    def duration_seconds(self):
        """Calculate delivery duration in seconds."""
        if not self.first_attempt_at or not self.completed_at:
            return None
        
        delta = self.completed_at - self.first_attempt_at
        return delta.total_seconds()
    
    def clean(self):
        """Validate webhook delivery."""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Validate payload is a dict
        if not isinstance(self.payload, dict):
            errors["payload"] = "Must be a dictionary"
        
        # Validate response headers is a dict
        if not isinstance(self.response_headers, dict):
            errors["response_headers"] = "Must be a dictionary"
        
        if errors:
            raise ValidationError(errors)
