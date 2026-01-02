"""Tests for e-signature models."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from modules.esignature.models import DocuSignConnection, Envelope, WebhookEvent


pytestmark = pytest.mark.django_db


class TestDocuSignConnection:
    """Test DocuSignConnection model."""

    def test_create_docusign_connection(self, firm, user):
        """Test creating a DocuSign connection."""
        connection = DocuSignConnection.objects.create(
            firm=firm,
            access_token="test_token",
            refresh_token="test_refresh",
            token_expires_at=timezone.now() + timedelta(hours=1),
            account_id="account_123",
            account_name="Test Account",
            base_uri="https://demo.docusign.net",
            connected_by=user,
        )

        assert connection.firm == firm
        assert connection.is_active is True
        assert connection.connected_by == user

    def test_docusign_connection_str(self, docusign_connection):
        """Test string representation."""
        assert str(docusign_connection) == f"DocuSign Connection for {docusign_connection.firm.name}"

    def test_is_token_expired_false(self, docusign_connection):
        """Test is_token_expired returns False for future expiration."""
        docusign_connection.token_expires_at = timezone.now() + timedelta(hours=1)
        docusign_connection.save()

        assert docusign_connection.is_token_expired() is False

    def test_is_token_expired_true(self, docusign_connection):
        """Test is_token_expired returns True for past expiration."""
        docusign_connection.token_expires_at = timezone.now() - timedelta(hours=1)
        docusign_connection.save()

        assert docusign_connection.is_token_expired() is True

    def test_one_connection_per_firm(self, firm, user):
        """Test one-to-one relationship: only one connection per firm."""
        # Create first connection
        DocuSignConnection.objects.create(
            firm=firm,
            access_token="token1",
            refresh_token="refresh1",
            token_expires_at=timezone.now() + timedelta(hours=1),
            account_id="account1",
            account_name="Account 1",
            base_uri="https://demo.docusign.net",
            connected_by=user,
        )

        # Attempting to create second connection should fail
        with pytest.raises(IntegrityError):
            DocuSignConnection.objects.create(
                firm=firm,
                access_token="token2",
                refresh_token="refresh2",
                token_expires_at=timezone.now() + timedelta(hours=1),
                account_id="account2",
                account_name="Account 2",
                base_uri="https://demo.docusign.net",
                connected_by=user,
            )


class TestEnvelope:
    """Test Envelope model."""

    def test_create_envelope(self, firm, docusign_connection, user):
        """Test creating an envelope."""
        envelope = Envelope.objects.create(
            firm=firm,
            connection=docusign_connection,
            envelope_id="env_123",
            status="sent",
            subject="Test Subject",
            message="Test Message",
            recipients=[{"email": "test@example.com", "name": "Test User", "recipient_id": 1}],
            created_by=user,
        )

        assert envelope.firm == firm
        assert envelope.connection == docusign_connection
        assert envelope.status == "sent"
        assert len(envelope.recipients) == 1

    def test_envelope_str(self, envelope):
        """Test string representation."""
        result = str(envelope)
        assert envelope.envelope_id in result
        assert envelope.status in result

    def test_envelope_status_choices(self, envelope):
        """Test envelope has valid status choices."""
        valid_statuses = [
            "created", "sent", "delivered", "signed",
            "completed", "declined", "voided", "error"
        ]

        for status_value in valid_statuses:
            envelope.status = status_value
            envelope.save()
            envelope.refresh_from_db()
            assert envelope.status == status_value

    def test_envelope_unique_envelope_id(self, firm, docusign_connection, user):
        """Test envelope_id must be unique."""
        Envelope.objects.create(
            firm=firm,
            connection=docusign_connection,
            envelope_id="unique_id",
            status="sent",
            subject="Test",
            message="Test",
            recipients=[],
            created_by=user,
        )

        # Creating another envelope with same envelope_id should fail
        with pytest.raises(IntegrityError):
            Envelope.objects.create(
                firm=firm,
                connection=docusign_connection,
                envelope_id="unique_id",
                status="sent",
                subject="Test",
                message="Test",
                recipients=[],
                created_by=user,
            )

    def test_envelope_linked_to_one_entity_constraint(self, firm, docusign_connection, user):
        """Test envelope can only be linked to proposal OR contract, not both."""
        # This test requires Proposal and Contract models which we'll skip for now
        # The constraint is defined in the model with CheckConstraint
        pass


class TestWebhookEvent:
    """Test WebhookEvent model."""

    def test_create_webhook_event(self, envelope):
        """Test creating a webhook event."""
        event = WebhookEvent.objects.create(
            envelope=envelope,
            envelope_id=envelope.envelope_id,
            event_type="envelope-completed",
            event_status="completed",
            payload={"test": "data"},
            headers={"signature": "test_sig"},
        )

        assert event.envelope == envelope
        assert event.processed is False
        assert event.event_type == "envelope-completed"

    def test_webhook_event_str(self, envelope):
        """Test string representation."""
        event = WebhookEvent.objects.create(
            envelope=envelope,
            envelope_id=envelope.envelope_id,
            event_type="envelope-completed",
            event_status="completed",
            payload={},
        )

        result = str(event)
        assert event.event_type in result
        assert envelope.envelope_id in result

    def test_webhook_event_ordering(self, envelope):
        """Test webhook events are ordered by received_at descending."""
        # Create multiple events
        event1 = WebhookEvent.objects.create(
            envelope=envelope,
            envelope_id=envelope.envelope_id,
            event_type="envelope-sent",
            event_status="sent",
            payload={},
        )

        event2 = WebhookEvent.objects.create(
            envelope=envelope,
            envelope_id=envelope.envelope_id,
            event_type="envelope-completed",
            event_status="completed",
            payload={},
        )

        # Query should return events in reverse chronological order
        events = WebhookEvent.objects.all()
        assert events[0] == event2  # Most recent first
        assert events[1] == event1

    def test_webhook_event_without_envelope(self):
        """Test webhook event can be created without linked envelope."""
        event = WebhookEvent.objects.create(
            envelope=None,
            envelope_id="unknown_envelope_id",
            event_type="envelope-sent",
            event_status="sent",
            payload={"test": "data"},
        )

        assert event.envelope is None
        assert event.envelope_id == "unknown_envelope_id"

    def test_webhook_event_processing(self, envelope):
        """Test marking webhook event as processed."""
        event = WebhookEvent.objects.create(
            envelope=envelope,
            envelope_id=envelope.envelope_id,
            event_type="envelope-completed",
            event_status="completed",
            payload={},
        )

        assert event.processed is False
        assert event.processed_at is None

        # Mark as processed
        event.processed = True
        event.processed_at = timezone.now()
        event.save()

        event.refresh_from_db()
        assert event.processed is True
        assert event.processed_at is not None
