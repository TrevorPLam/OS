import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.email_ingestion.models import (
    EmailConnection,
    EmailArtifact,
)
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", ******)


@pytest.fixture
def email_connection(db, firm, user):
    return EmailConnection.objects.create(
        firm=firm,
        name="Main Gmail",
        provider="gmail",
        email_address="support@example.com",
        is_active=True,
        created_by=user,
    )


@pytest.mark.django_db
class TestEmailConnection:
    """Test EmailConnection model functionality"""

    def test_email_connection_creation(self, firm, user):
        """Test basic email connection creation"""
        connection = EmailConnection.objects.create(
            firm=firm,
            name="Support Inbox",
            provider="gmail",
            email_address="support@testfirm.com",
            is_active=True,
            created_by=user,
        )

        assert connection.name == "Support Inbox"
        assert connection.provider == "gmail"
        assert connection.email_address == "support@testfirm.com"
        assert connection.is_active is True
        assert connection.firm == firm

    def test_email_connection_providers(self, firm, user):
        """Test different email providers"""
        providers = ["gmail", "outlook", "other"]

        for provider in providers:
            connection = EmailConnection.objects.create(
                firm=firm, name=f"{provider} Connection", provider=provider, email_address=f"test@{provider}.com", created_by=user
            )
            assert connection.provider == provider

    def test_email_connection_active_status(self, email_connection):
        """Test email connection active/inactive status"""
        assert email_connection.is_active is True

        # Deactivate connection
        email_connection.is_active = False
        email_connection.save()

        assert email_connection.is_active is False

    def test_email_connection_sync_tracking(self, email_connection):
        """Test email connection sync timestamp tracking"""
        assert email_connection.last_sync_at is None

        # Update sync timestamp
        sync_time = timezone.now()
        email_connection.last_sync_at = sync_time
        email_connection.save()

        assert email_connection.last_sync_at == sync_time

    def test_email_connection_credentials_storage(self, firm, user):
        """Test encrypted credentials storage"""
        connection = EmailConnection.objects.create(
            firm=firm,
            name="Secure Connection",
            provider="gmail",
            email_address="secure@example.com",
            credentials_encrypted="encrypted_oauth_token_here",
            created_by=user,
        )

        assert connection.credentials_encrypted == "encrypted_oauth_token_here"

    def test_email_connection_string_representation(self, email_connection):
        """Test __str__ method"""
        expected = f"{email_connection.name} ({email_connection.email_address})"
        assert str(email_connection) == expected

    def test_email_connection_firm_scoping(self, firm, user):
        """Test email connection tenant isolation"""
        firm2 = Firm.objects.create(name="Firm 2", slug="firm-2", status="active")

        conn1 = EmailConnection.objects.create(
            firm=firm, name="Conn 1", provider="gmail", email_address="conn1@example.com", created_by=user
        )
        conn2 = EmailConnection.objects.create(
            firm=firm2, name="Conn 2", provider="gmail", email_address="conn2@example.com", created_by=user
        )

        assert conn1.firm != conn2.firm


@pytest.mark.django_db
class TestEmailArtifact:
    """Test EmailArtifact model functionality"""

    def test_email_artifact_creation(self, email_connection):
        """Test basic email artifact creation"""
        sent_at = timezone.now() - timedelta(hours=2)
        received_at = timezone.now() - timedelta(hours=1)

        artifact = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-123456",
            from_address="sender@example.com",
            to_addresses="recipient@testfirm.com",
            subject="Test Email",
            sent_at=sent_at,
            received_at=received_at,
            status="ingested",
        )

        assert artifact.connection == email_connection
        assert artifact.external_message_id == "msg-123456"
        assert artifact.from_address == "sender@example.com"
        assert artifact.subject == "Test Email"
        assert artifact.status == "ingested"

    def test_email_artifact_status_choices(self, email_connection):
        """Test email artifact status choices"""
        statuses = ["ingested", "mapped", "triage", "ignored"]

        for i, status in enumerate(statuses):
            artifact = EmailArtifact.objects.create(
                firm=email_connection.firm,
                connection=email_connection,
                provider="gmail",
                external_message_id=f"msg-{status}-{i}",
                from_address="test@example.com",
                to_addresses="recipient@example.com",
                subject=f"Email {status}",
                sent_at=timezone.now(),
                received_at=timezone.now(),
                status=status,
            )
            assert artifact.status == status

    def test_email_artifact_multiple_recipients(self, email_connection):
        """Test email artifact with multiple recipients"""
        artifact = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-multi-recipient",
            from_address="sender@example.com",
            to_addresses="recipient1@example.com, recipient2@example.com, recipient3@example.com",
            cc_addresses="cc1@example.com, cc2@example.com",
            subject="Multi-recipient Email",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        assert "recipient1@example.com" in artifact.to_addresses
        assert "recipient2@example.com" in artifact.to_addresses
        assert "cc1@example.com" in artifact.cc_addresses

    def test_email_artifact_thread_tracking(self, email_connection):
        """Test email artifact thread/conversation tracking"""
        thread_id = "thread-xyz-789"

        artifact1 = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-thread-1",
            thread_id=thread_id,
            from_address="user1@example.com",
            to_addresses="user2@example.com",
            subject="Thread Test",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        artifact2 = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-thread-2",
            thread_id=thread_id,
            from_address="user2@example.com",
            to_addresses="user1@example.com",
            subject="Re: Thread Test",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        # Both messages in same thread
        assert artifact1.thread_id == artifact2.thread_id

    def test_email_artifact_body_preview(self, email_connection):
        """Test email artifact body preview"""
        preview = "This is a preview of the email body content. It should be limited to 500 characters..."

        artifact = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-preview",
            from_address="sender@example.com",
            to_addresses="recipient@example.com",
            subject="Email with Preview",
            body_preview=preview,
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        assert artifact.body_preview == preview
        assert len(artifact.body_preview) <= 500

    def test_email_artifact_storage_reference(self, email_connection, user):
        """Test email artifact document storage reference"""
        from modules.documents.models import Document

        # Create document for email storage
        document = Document.objects.create(
            firm=email_connection.firm, name="email-msg-123.eml", file_type="eml", uploaded_by=user
        )

        artifact = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-with-storage",
            from_address="sender@example.com",
            to_addresses="recipient@example.com",
            subject="Email with Full Storage",
            storage_ref=document,
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        assert artifact.storage_ref == document

    def test_email_artifact_mapping_workflow(self, email_connection):
        """Test email artifact mapping workflow"""
        # Create ingested artifact
        artifact = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-mapping-test",
            from_address="client@example.com",
            to_addresses="support@testfirm.com",
            subject="Support Request",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            status="ingested",
        )

        assert artifact.status == "ingested"

        # Map to client/engagement
        artifact.status = "mapped"
        artifact.save()

        assert artifact.status == "mapped"

    def test_email_artifact_triage_workflow(self, email_connection):
        """Test email artifact triage workflow"""
        artifact = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-triage",
            from_address="unknown@example.com",
            to_addresses="info@testfirm.com",
            subject="Unknown Sender",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            status="ingested",
        )

        # Needs triage
        artifact.status = "triage"
        artifact.save()

        assert artifact.status == "triage"

        # After review, ignore
        artifact.status = "ignored"
        artifact.save()

        assert artifact.status == "ignored"

    def test_email_artifact_sent_received_timestamps(self, email_connection):
        """Test email artifact timestamp handling"""
        sent_at = timezone.now() - timedelta(hours=3)
        received_at = timezone.now() - timedelta(hours=2)

        artifact = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-timestamps",
            from_address="sender@example.com",
            to_addresses="recipient@example.com",
            subject="Timestamp Test",
            sent_at=sent_at,
            received_at=received_at,
        )

        # Received should be after sent
        assert artifact.received_at > artifact.sent_at


@pytest.mark.django_db
class TestEmailIngestionWorkflow:
    """Test complete email ingestion workflow scenarios"""

    def test_complete_ingestion_workflow(self, firm, user):
        """Test complete email ingestion workflow"""
        # Create email connection
        connection = EmailConnection.objects.create(
            firm=firm,
            name="Sales Inbox",
            provider="gmail",
            email_address="sales@testfirm.com",
            is_active=True,
            created_by=user,
        )

        # Ingest email
        artifact = EmailArtifact.objects.create(
            firm=firm,
            connection=connection,
            provider="gmail",
            external_message_id="msg-complete-001",
            from_address="prospect@example.com",
            to_addresses="sales@testfirm.com",
            subject="Interested in your services",
            body_preview="I would like to learn more about...",
            sent_at=timezone.now() - timedelta(hours=1),
            received_at=timezone.now(),
            status="ingested",
        )

        # Process and map
        artifact.status = "mapped"
        artifact.save()

        # Update connection sync time
        connection.last_sync_at = timezone.now()
        connection.save()

        assert artifact.status == "mapped"
        assert connection.last_sync_at is not None

    def test_multi_connection_ingestion(self, firm, user):
        """Test ingestion from multiple email connections"""
        # Create multiple connections
        gmail_conn = EmailConnection.objects.create(
            firm=firm, name="Gmail", provider="gmail", email_address="support@gmail.com", created_by=user
        )

        outlook_conn = EmailConnection.objects.create(
            firm=firm, name="Outlook", provider="outlook", email_address="support@outlook.com", created_by=user
        )

        # Ingest from both
        gmail_artifact = EmailArtifact.objects.create(
            firm=firm,
            connection=gmail_conn,
            provider="gmail",
            external_message_id="gmail-msg-001",
            from_address="user1@example.com",
            to_addresses="support@gmail.com",
            subject="Gmail Email",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        outlook_artifact = EmailArtifact.objects.create(
            firm=firm,
            connection=outlook_conn,
            provider="outlook",
            external_message_id="outlook-msg-001",
            from_address="user2@example.com",
            to_addresses="support@outlook.com",
            subject="Outlook Email",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        assert gmail_artifact.connection == gmail_conn
        assert outlook_artifact.connection == outlook_conn
        assert gmail_artifact.provider != outlook_artifact.provider

    def test_email_thread_conversation(self, email_connection):
        """Test email thread/conversation tracking"""
        thread_id = "thread-conversation-123"

        # Initial email
        email1 = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-conv-1",
            thread_id=thread_id,
            from_address="client@example.com",
            to_addresses="consultant@testfirm.com",
            subject="Project Discussion",
            sent_at=timezone.now() - timedelta(hours=3),
            received_at=timezone.now() - timedelta(hours=3),
        )

        # Reply
        email2 = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-conv-2",
            thread_id=thread_id,
            from_address="consultant@testfirm.com",
            to_addresses="client@example.com",
            subject="Re: Project Discussion",
            sent_at=timezone.now() - timedelta(hours=2),
            received_at=timezone.now() - timedelta(hours=2),
        )

        # Follow-up
        email3 = EmailArtifact.objects.create(
            firm=email_connection.firm,
            connection=email_connection,
            provider="gmail",
            external_message_id="msg-conv-3",
            thread_id=thread_id,
            from_address="client@example.com",
            to_addresses="consultant@testfirm.com",
            subject="Re: Project Discussion",
            sent_at=timezone.now() - timedelta(hours=1),
            received_at=timezone.now() - timedelta(hours=1),
        )

        # All in same thread
        thread_messages = EmailArtifact.objects.filter(thread_id=thread_id)
        assert thread_messages.count() == 3
