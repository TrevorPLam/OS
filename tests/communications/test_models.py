import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.communications.models import (
    Conversation,
    Participant,
    Message,
    MessageAttachment,
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
def conversation(db, firm, user):
    return Conversation.objects.create(
        firm=firm,
        subject="Test Conversation",
        visibility="internal_only",
        status="active",
        created_by=user,
    )


@pytest.mark.django_db
class TestConversation:
    """Test Conversation model functionality"""

    def test_conversation_creation(self, firm, user):
        """Test basic conversation creation"""
        conversation = Conversation.objects.create(
            firm=firm,
            subject="Project Discussion",
            visibility="internal_only",
            status="active",
            created_by=user,
        )

        assert conversation.subject == "Project Discussion"
        assert conversation.firm == firm
        assert conversation.visibility == "internal_only"
        assert conversation.status == "active"
        assert conversation.message_count == 0

    def test_conversation_visibility_choices(self, firm, user):
        """Test conversation visibility choices"""
        visibilities = ["internal_only", "client_visible"]

        for visibility in visibilities:
            conversation = Conversation.objects.create(
                firm=firm, subject=f"Test {visibility}", visibility=visibility, created_by=user
            )
            assert conversation.visibility == visibility

    def test_conversation_status_choices(self, firm, user):
        """Test conversation status choices"""
        statuses = ["active", "archived"]

        for status in statuses:
            conversation = Conversation.objects.create(
                firm=firm, subject=f"Test {status}", visibility="internal_only", status=status, created_by=user
            )
            assert conversation.status == status

    def test_conversation_primary_object_link(self, firm, user):
        """Test conversation primary object linking"""
        conversation = Conversation.objects.create(
            firm=firm,
            subject="Client Engagement Discussion",
            visibility="client_visible",
            primary_object_type="Engagement",
            primary_object_id=123,
            created_by=user,
        )

        assert conversation.primary_object_type == "Engagement"
        assert conversation.primary_object_id == 123

    def test_conversation_message_tracking(self, firm, user):
        """Test conversation message count and timestamp tracking"""
        conversation = Conversation.objects.create(firm=firm, subject="Test", created_by=user)

        # Update message tracking
        conversation.message_count = 5
        conversation.last_message_at = timezone.now()
        conversation.save()

        assert conversation.message_count == 5
        assert conversation.last_message_at is not None

    def test_conversation_string_representation(self, conversation):
        """Test __str__ method"""
        expected = f"{conversation.subject} ({conversation.visibility})"
        assert str(conversation) == expected

    def test_conversation_without_subject(self, firm, user):
        """Test conversation without subject"""
        conversation = Conversation.objects.create(firm=firm, visibility="internal_only", created_by=user)

        # String representation should show conversation ID when no subject
        assert "Conversation #" in str(conversation)

    def test_conversation_correlation_id(self, firm, user):
        """Test conversation correlation ID tracking"""
        correlation_id = "req-12345-abc"

        conversation = Conversation.objects.create(
            firm=firm, subject="Tracked Request", correlation_id=correlation_id, created_by=user
        )

        assert conversation.correlation_id == correlation_id

    def test_conversation_firm_scoping(self, firm, user):
        """Test conversation tenant isolation"""
        firm2 = Firm.objects.create(name="Firm 2", slug="firm-2", status="active")

        conv1 = Conversation.objects.create(firm=firm, subject="Conv 1", created_by=user)
        conv2 = Conversation.objects.create(firm=firm2, subject="Conv 2", created_by=user)

        assert conv1.firm != conv2.firm


@pytest.mark.django_db
class TestParticipant:
    """Test Participant model functionality"""

    def test_participant_creation_staff(self, conversation, user):
        """Test staff participant creation"""
        participant = Participant.objects.create(conversation=conversation, user=user, participant_type="staff")

        assert participant.conversation == conversation
        assert participant.user == user
        assert participant.participant_type == "staff"

    def test_participant_types(self, conversation, user):
        """Test different participant types"""
        # Staff participant
        staff_participant = Participant.objects.create(
            conversation=conversation, user=user, participant_type="staff"
        )
        assert staff_participant.participant_type == "staff"

        # Portal participant (for client_visible conversations)
        portal_conversation = Conversation.objects.create(
            firm=conversation.firm, subject="Client Conv", visibility="client_visible", created_by=user
        )
        portal_participant = Participant.objects.create(
            conversation=portal_conversation, user=user, participant_type="portal"
        )
        assert portal_participant.participant_type == "portal"

    def test_participant_notification_preferences(self, conversation, user):
        """Test participant notification preferences"""
        participant = Participant.objects.create(
            conversation=conversation,
            user=user,
            participant_type="staff",
            notifications_enabled=True,
        )

        assert participant.notifications_enabled is True

        participant.notifications_enabled = False
        participant.save()

        assert participant.notifications_enabled is False


@pytest.mark.django_db
class TestMessage:
    """Test Message model functionality"""

    def test_message_creation(self, conversation, user):
        """Test basic message creation"""
        message = Message.objects.create(
            conversation=conversation, sender=user, message_type="text", content="Hello, this is a test message."
        )

        assert message.conversation == conversation
        assert message.sender == user
        assert message.message_type == "text"
        assert message.content == "Hello, this is a test message."

    def test_message_types(self, conversation, user):
        """Test different message types"""
        message_types = ["text", "system_event", "attachment", "action"]

        for msg_type in message_types:
            message = Message.objects.create(
                conversation=conversation, sender=user, message_type=msg_type, content=f"Message of type {msg_type}"
            )
            assert message.message_type == msg_type

    def test_message_system_event(self, conversation, user):
        """Test system event message"""
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            message_type="system_event",
            content="User joined the conversation",
        )

        assert message.message_type == "system_event"

    def test_message_edited_tracking(self, conversation, user):
        """Test message edit tracking"""
        message = Message.objects.create(
            conversation=conversation, sender=user, message_type="text", content="Original content"
        )

        # Edit message
        message.is_edited = True
        message.edited_at = timezone.now()
        message.content = "Edited content"
        message.save()

        assert message.is_edited is True
        assert message.edited_at is not None
        assert message.content == "Edited content"

    def test_message_metadata(self, conversation, user):
        """Test message metadata storage"""
        metadata = {"action": "status_change", "from": "open", "to": "closed"}

        message = Message.objects.create(
            conversation=conversation, sender=user, message_type="action", content="Status changed", metadata=metadata
        )

        assert message.metadata["action"] == "status_change"
        assert message.metadata["from"] == "open"


@pytest.mark.django_db
class TestMessageAttachment:
    """Test MessageAttachment model functionality"""

    def test_message_attachment_creation(self, conversation, user):
        """Test message attachment creation"""
        from modules.documents.models import Document

        # Create document
        document = Document.objects.create(
            firm=conversation.firm, name="test-file.pdf", file_type="pdf", uploaded_by=user
        )

        # Create message with attachment
        message = Message.objects.create(
            conversation=conversation, sender=user, message_type="attachment", content="See attached file"
        )

        attachment = MessageAttachment.objects.create(message=message, document=document)

        assert attachment.message == message
        assert attachment.document == document

    def test_multiple_attachments(self, conversation, user):
        """Test message with multiple attachments"""
        from modules.documents.models import Document

        message = Message.objects.create(
            conversation=conversation, sender=user, message_type="attachment", content="Multiple files attached"
        )

        # Create multiple attachments
        doc1 = Document.objects.create(
            firm=conversation.firm, name="file1.pdf", file_type="pdf", uploaded_by=user
        )
        doc2 = Document.objects.create(
            firm=conversation.firm, name="file2.jpg", file_type="image", uploaded_by=user
        )

        attachment1 = MessageAttachment.objects.create(message=message, document=doc1)
        attachment2 = MessageAttachment.objects.create(message=message, document=doc2)

        assert message.attachments.count() == 2


@pytest.mark.django_db
class TestConversationWorkflow:
    """Test conversation workflow scenarios"""

    def test_internal_conversation_workflow(self, firm, user, db):
        """Test internal-only conversation workflow"""
        # Create internal conversation
        conversation = Conversation.objects.create(
            firm=firm, subject="Internal Project Sync", visibility="internal_only", status="active", created_by=user
        )

        # Add staff participants
        staff1 = User.objects.create_user(username="staff1", email="staff1@example.com", ******)
        staff2 = User.objects.create_user(username="staff2", email="staff2@example.com", ******)

        Participant.objects.create(conversation=conversation, user=staff1, participant_type="staff")
        Participant.objects.create(conversation=conversation, user=staff2, participant_type="staff")

        # Send messages
        msg1 = Message.objects.create(
            conversation=conversation, sender=staff1, message_type="text", content="Starting the project sync"
        )
        msg2 = Message.objects.create(
            conversation=conversation, sender=staff2, message_type="text", content="I'm ready to discuss"
        )

        # Update conversation tracking
        conversation.message_count = 2
        conversation.last_message_at = timezone.now()
        conversation.save()

        assert conversation.message_count == 2
        assert Participant.objects.filter(conversation=conversation).count() == 2

    def test_client_visible_conversation_workflow(self, firm, user):
        """Test client-visible conversation workflow"""
        # Create client-visible conversation
        conversation = Conversation.objects.create(
            firm=firm,
            subject="Project Updates",
            visibility="client_visible",
            status="active",
            primary_object_type="Engagement",
            primary_object_id=456,
            created_by=user,
        )

        # Add participants (staff and portal)
        Participant.objects.create(conversation=conversation, user=user, participant_type="staff")

        # Send message
        message = Message.objects.create(
            conversation=conversation, sender=user, message_type="text", content="Project update for client"
        )

        assert conversation.visibility == "client_visible"
        assert message.conversation == conversation

    def test_conversation_archive_workflow(self, conversation, user):
        """Test conversation archiving"""
        # Active conversation
        assert conversation.status == "active"

        # Archive conversation
        conversation.status = "archived"
        conversation.save()

        assert conversation.status == "archived"
