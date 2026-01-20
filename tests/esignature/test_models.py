import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.esignature.models import DocuSignConnection, WebhookEvent
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.mark.django_db
class TestDocuSignConnection:
    """Test DocuSign connection behavior."""

    def test_token_expiration(self, firm, user):
        """Expired tokens should be detected."""
        connection = DocuSignConnection.objects.create(
            firm=firm,
            access_token="token",
            refresh_token="refresh",
            token_expires_at=timezone.now() - timedelta(minutes=5),
            account_id="acct-1",
            account_name="Acme",
            base_uri="https://demo.docusign.net",
            connected_by=user,
        )

        assert connection.is_token_expired() is True
        assert firm.name in str(connection)


@pytest.mark.django_db
class TestWebhookEvent:
    """Test DocuSign webhook events."""

    def test_webhook_event_string(self, firm):
        """Webhook events should include type and envelope in string."""
        event = WebhookEvent.objects.create(
            firm=firm,
            envelope=None,
            envelope_id="env-1",
            event_id="evt-1",
            event_type="envelope-completed",
            event_status="completed",
            payload={"event": "completed"},
        )

        assert "envelope-completed" in str(event)
        assert "env-1" in str(event)
