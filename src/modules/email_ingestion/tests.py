"""
Email Ingestion Tests.

Tests idempotent ingestion, mapping suggestions, triage behavior, and audit events.
Implements docs/15 section 7 testing requirements.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from modules.firm.models import Firm
from modules.crm.models import Account, Engagement, Contact
from modules.email_ingestion.models import EmailConnection, EmailArtifact, IngestionAttempt
from modules.email_ingestion.services import EmailIngestionService, EmailMappingService
from modules.firm.audit import AuditEvent

User = get_user_model()


class EmailIngestionIdempotencyTest(TestCase):
    """Test idempotent ingestion per docs/15 section 7."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )
        self.service = EmailIngestionService()

    def test_idempotent_ingestion_on_retry(self):
        """Test that re-ingesting the same email returns the existing artifact."""
        # First ingestion
        email1 = self.service.ingest_email(
            connection=self.connection,
            external_message_id="msg-12345",
            thread_id="thread-abc",
            from_address="sender@example.com",
            to_addresses="recipient@example.com",
            cc_addresses="",
            subject="Test Subject",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            body_preview="This is a test email",
        )

        # Second ingestion with same external_message_id (simulates retry)
        email2 = self.service.ingest_email(
            connection=self.connection,
            external_message_id="msg-12345",  # Same ID
            thread_id="thread-abc",
            from_address="sender@example.com",
            to_addresses="recipient@example.com",
            cc_addresses="",
            subject="Test Subject",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            body_preview="This is a test email",
        )

        # Should return the same artifact
        self.assertEqual(email1.email_artifact_id, email2.email_artifact_id)
        self.assertEqual(EmailArtifact.objects.filter(connection=self.connection).count(), 1)

        # Both attempts should be logged
        attempts = IngestionAttempt.objects.filter(email_artifact=email1, operation="fetch")
        self.assertEqual(attempts.count(), 2)
        self.assertTrue(all(a.status == "success" for a in attempts))


class EmailMappingSuggestionTest(TestCase):
    """Test mapping suggestion logic per docs/15 section 3."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )
        self.account = Account.objects.create(
            firm=self.firm, name="Test Account", status="active", created_by=self.user
        )
        self.contact = Contact.objects.create(
            firm=self.firm,
            account=self.account,
            name="John Doe",
            email="john@example.com",
            created_by=self.user,
        )
        self.service = EmailMappingService()

    def test_mapping_suggestion_from_sender_email(self):
        """Test that emails from known contacts are mapped to their accounts."""
        email = EmailArtifact.objects.create(
            firm=self.firm,
            connection=self.connection,
            provider="gmail",
            external_message_id="msg-123",
            from_address="john@example.com",  # Matches contact
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Hello",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        account, engagement, work_item, confidence, reasons = self.service.suggest_mapping(email)

        # Should suggest the account
        self.assertEqual(account, self.account)
        self.assertGreater(confidence, Decimal("0.3"))
        self.assertIn("contact", reasons.lower())

    def test_mapping_determinism(self):
        """Test that mapping suggestions are deterministic given same data."""
        email = EmailArtifact.objects.create(
            firm=self.firm,
            connection=self.connection,
            provider="gmail",
            external_message_id="msg-124",
            from_address="john@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Hello",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        # Run mapping twice
        result1 = self.service.suggest_mapping(email)
        result2 = self.service.suggest_mapping(email)

        # Should be identical
        self.assertEqual(result1[0], result2[0])  # account
        self.assertEqual(result1[3], result2[3])  # confidence
        self.assertEqual(result1[4], result2[4])  # reasons


class EmailTriageBehaviorTest(TestCase):
    """Test triage behavior for ambiguous cases per docs/15 section 4."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )
        self.service = EmailIngestionService()

    def test_low_confidence_goes_to_triage(self):
        """Test that low-confidence mappings are sent to triage."""
        email = self.service.ingest_email(
            connection=self.connection,
            external_message_id="msg-low-conf",
            thread_id=None,
            from_address="unknown@somewhere.com",  # Unknown sender
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Random email",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            body_preview="No clear mapping signals",
        )

        # Should be in triage
        self.assertEqual(email.status, "triage")


class EmailMappingAuditTest(TestCase):
    """Test audit event generation for mapping changes per docs/15 section 5."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )
        self.account = Account.objects.create(
            firm=self.firm, name="Test Account", status="active", created_by=self.user
        )

    def test_confirm_mapping_creates_audit_event(self):
        """Test that confirming a mapping creates an audit event."""
        email = EmailArtifact.objects.create(
            firm=self.firm,
            connection=self.connection,
            provider="gmail",
            external_message_id="msg-audit",
            from_address="sender@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Test",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            status="triage",
        )

        # Confirm mapping
        email.confirm_mapping(account=self.account, user=self.user)

        # Check audit event was created
        audit_events = AuditEvent.objects.filter(
            firm=self.firm,
            event_type="email_mapping_confirmed",
            resource_type="EmailArtifact",
            resource_id=str(email.email_artifact_id),
        )
        self.assertEqual(audit_events.count(), 1)
        self.assertEqual(audit_events.first().actor_user, self.user)

    def test_mark_ignored_creates_audit_event(self):
        """Test that marking as ignored creates an audit event."""
        email = EmailArtifact.objects.create(
            firm=self.firm,
            connection=self.connection,
            provider="gmail",
            external_message_id="msg-ignore",
            from_address="spam@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Spam",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        # Mark ignored
        email.mark_ignored(reason="Spam email", user=self.user)

        # Check audit event was created
        audit_events = AuditEvent.objects.filter(
            firm=self.firm,
            event_type="email_marked_ignored",
            resource_type="EmailArtifact",
            resource_id=str(email.email_artifact_id),
        )
        self.assertEqual(audit_events.count(), 1)
        self.assertEqual(email.status, "ignored")
        self.assertEqual(email.ignored_reason, "Spam email")
