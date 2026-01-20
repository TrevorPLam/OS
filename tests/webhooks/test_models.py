import pytest
import hmac
import hashlib
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.webhooks.models import WebhookEndpoint, WebhookDelivery
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.fixture
def webhook_endpoint(db, firm, user):
    return WebhookEndpoint.objects.create(
        firm=firm,
        name="Test Webhook",
        url="https://example.com/webhook",
        description="Test webhook endpoint",
        status="active",
        secret="test-secret-key-12345",
        subscribed_events=["client.created", "project.updated"],
        created_by=user,
    )


@pytest.mark.django_db
class TestWebhookEndpoint:
    """Test WebhookEndpoint model functionality"""

    def test_webhook_endpoint_creation(self, firm, user):
        """Test basic webhook endpoint creation"""
        webhook = WebhookEndpoint.objects.create(
            firm=firm,
            name="New Webhook",
            url="https://example.com/events",
            description="Webhook for external integration",
            status="active",
            secret="secret-key-xyz",
            subscribed_events=["invoice.paid", "client.created"],
            created_by=user,
        )

        assert webhook.name == "New Webhook"
        assert webhook.url == "https://example.com/events"
        assert webhook.status == "active"
        assert webhook.firm == firm
        assert "invoice.paid" in webhook.subscribed_events

    def test_webhook_status_choices(self, firm, user):
        """Test webhook status choices"""
        statuses = ["active", "paused", "disabled"]

        for status in statuses:
            webhook = WebhookEndpoint.objects.create(
                firm=firm,
                name=f"Webhook {status}",
                url="https://example.com/webhook",
                status=status,
                secret="secret-key",
                created_by=user,
            )
            assert webhook.status == status

    def test_webhook_event_subscriptions(self, firm, user):
        """Test webhook event subscriptions"""
        events = ["client.created", "client.updated", "project.completed", "invoice.paid", "task.assigned"]

        webhook = WebhookEndpoint.objects.create(
            firm=firm,
            name="Multi-Event Webhook",
            url="https://example.com/webhook",
            secret="secret-key",
            subscribed_events=events,
            created_by=user,
        )

        assert len(webhook.subscribed_events) == len(events)
        assert "client.created" in webhook.subscribed_events
        assert "invoice.paid" in webhook.subscribed_events

    def test_webhook_secret_key(self, firm, user):
        """Test webhook secret key for HMAC"""
        secret = "my-secure-secret-key"

        webhook = WebhookEndpoint.objects.create(
            firm=firm, name="Secure Webhook", url="https://example.com/webhook", secret=secret, created_by=user
        )

        assert webhook.secret == secret

    def test_webhook_delivery_settings(self, firm, user):
        """Test webhook delivery configuration"""
        webhook = WebhookEndpoint.objects.create(
            firm=firm,
            name="Custom Delivery Webhook",
            url="https://example.com/webhook",
            secret="secret-key",
            max_retries=5,
            retry_delay_seconds=120,
            timeout_seconds=60,
            created_by=user,
        )

        assert webhook.max_retries == 5
        assert webhook.retry_delay_seconds == 120
        assert webhook.timeout_seconds == 60

    def test_webhook_rate_limiting(self, firm, user):
        """Test webhook rate limiting configuration"""
        webhook = WebhookEndpoint.objects.create(
            firm=firm,
            name="Rate Limited Webhook",
            url="https://example.com/webhook",
            secret="secret-key",
            rate_limit_per_minute=100,
            created_by=user,
        )

        assert webhook.rate_limit_per_minute == 100

    def test_webhook_statistics_tracking(self, webhook_endpoint):
        """Test webhook delivery statistics"""
        # Update statistics
        webhook_endpoint.total_deliveries = 100
        webhook_endpoint.successful_deliveries = 95
        webhook_endpoint.failed_deliveries = 5
        webhook_endpoint.last_delivery_at = timezone.now()
        webhook_endpoint.last_success_at = timezone.now()
        webhook_endpoint.save()

        assert webhook_endpoint.total_deliveries == 100
        assert webhook_endpoint.successful_deliveries == 95
        assert webhook_endpoint.failed_deliveries == 5
        assert webhook_endpoint.last_delivery_at is not None

    def test_webhook_metadata(self, firm, user):
        """Test webhook metadata storage"""
        metadata = {"integration": "zapier", "version": "2.0", "custom_field": "value"}

        webhook = WebhookEndpoint.objects.create(
            firm=firm,
            name="Metadata Webhook",
            url="https://example.com/webhook",
            secret="secret-key",
            metadata=metadata,
            created_by=user,
        )

        assert webhook.metadata["integration"] == "zapier"
        assert webhook.metadata["version"] == "2.0"


@pytest.mark.django_db
class TestWebhookDelivery:
    """Test WebhookDelivery model functionality"""

    def test_webhook_delivery_creation(self, webhook_endpoint):
        """Test basic webhook delivery creation"""
        payload = {"event": "client.created", "client_id": 123, "timestamp": "2024-01-01T00:00:00Z"}

        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook_endpoint,
            event_type="client.created",
            payload=payload,
            status="pending",
            attempt_count=0,
        )

        assert delivery.webhook_endpoint == webhook_endpoint
        assert delivery.event_type == "client.created"
        assert delivery.status == "pending"
        assert delivery.payload["client_id"] == 123

    def test_webhook_delivery_status_transitions(self, webhook_endpoint):
        """Test webhook delivery status transitions"""
        payload = {"event": "project.updated", "project_id": 456}

        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook_endpoint, event_type="project.updated", payload=payload, status="pending"
        )

        # Start delivery
        delivery.status = "sending"
        delivery.attempt_count = 1
        delivery.attempted_at = timezone.now()
        delivery.save()

        assert delivery.status == "sending"
        assert delivery.attempt_count == 1

        # Mark as successful
        delivery.status = "delivered"
        delivery.delivered_at = timezone.now()
        delivery.response_status_code = 200
        delivery.response_body = '{"success": true}'
        delivery.save()

        assert delivery.status == "delivered"
        assert delivery.response_status_code == 200

    def test_webhook_delivery_retry_logic(self, webhook_endpoint):
        """Test webhook delivery retry logic"""
        payload = {"event": "invoice.paid", "invoice_id": 789}

        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook_endpoint, event_type="invoice.paid", payload=payload, status="pending"
        )

        # First attempt fails
        delivery.status = "failed"
        delivery.attempt_count = 1
        delivery.error_message = "Connection timeout"
        delivery.next_retry_at = timezone.now() + timedelta(seconds=60)
        delivery.save()

        assert delivery.status == "failed"
        assert delivery.attempt_count == 1
        assert delivery.next_retry_at is not None

        # Retry
        delivery.attempt_count = 2
        delivery.status = "sending"
        delivery.save()

        assert delivery.attempt_count == 2

    def test_webhook_delivery_max_retries(self, webhook_endpoint):
        """Test webhook delivery max retries"""
        payload = {"event": "task.assigned", "task_id": 101}

        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook_endpoint,
            event_type="task.assigned",
            payload=payload,
            status="pending",
            max_attempts=3,
        )

        # Exhaust retries
        delivery.attempt_count = 3
        delivery.status = "failed"
        delivery.error_message = "Max retries exceeded"
        delivery.save()

        assert delivery.attempt_count == delivery.max_attempts
        assert delivery.status == "failed"

    def test_webhook_delivery_signature(self, webhook_endpoint):
        """Test webhook HMAC signature generation"""
        payload = {"event": "client.created", "data": {"id": 123, "name": "Test Client"}}

        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook_endpoint, event_type="client.created", payload=payload, status="pending"
        )

        # Generate HMAC signature
        import json

        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(
            webhook_endpoint.secret.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()

        # Store signature (in actual implementation)
        delivery.signature = expected_signature
        delivery.save()

        assert delivery.signature == expected_signature

    def test_webhook_delivery_response_tracking(self, webhook_endpoint):
        """Test webhook delivery response tracking"""
        payload = {"event": "project.completed"}

        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook_endpoint, event_type="project.completed", payload=payload, status="sending"
        )

        # Successful response
        delivery.status = "delivered"
        delivery.response_status_code = 200
        delivery.response_body = '{"received": true, "processed": true}'
        delivery.response_headers = {"Content-Type": "application/json", "X-Request-ID": "abc123"}
        delivery.delivered_at = timezone.now()
        delivery.save()

        assert delivery.response_status_code == 200
        assert "received" in delivery.response_body
        assert delivery.response_headers["X-Request-ID"] == "abc123"

    def test_webhook_delivery_error_handling(self, webhook_endpoint):
        """Test webhook delivery error handling"""
        payload = {"event": "invoice.cancelled"}

        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook_endpoint, event_type="invoice.cancelled", payload=payload, status="sending"
        )

        # Failed delivery
        delivery.status = "failed"
        delivery.attempt_count = 1
        delivery.error_message = "HTTP 500: Internal Server Error"
        delivery.response_status_code = 500
        delivery.response_body = '{"error": "Server error"}'
        delivery.save()

        assert delivery.status == "failed"
        assert delivery.response_status_code == 500
        assert "Server error" in delivery.response_body


@pytest.mark.django_db
class TestWebhookIntegration:
    """Test webhook integration scenarios"""

    def test_webhook_delivery_workflow(self, webhook_endpoint):
        """Test complete webhook delivery workflow"""
        # Create event
        payload = {"event": "client.created", "client": {"id": 123, "name": "New Client", "email": "client@example.com"}}

        # Create delivery
        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook_endpoint,
            event_type="client.created",
            payload=payload,
            status="pending",
            max_attempts=3,
        )

        # Attempt delivery
        delivery.status = "sending"
        delivery.attempt_count = 1
        delivery.attempted_at = timezone.now()
        delivery.save()

        # Successful delivery
        delivery.status = "delivered"
        delivery.response_status_code = 200
        delivery.delivered_at = timezone.now()
        delivery.save()

        # Update endpoint statistics
        webhook_endpoint.total_deliveries += 1
        webhook_endpoint.successful_deliveries += 1
        webhook_endpoint.last_delivery_at = timezone.now()
        webhook_endpoint.last_success_at = timezone.now()
        webhook_endpoint.save()

        assert delivery.status == "delivered"
        assert webhook_endpoint.successful_deliveries == 1
        assert webhook_endpoint.total_deliveries == 1
