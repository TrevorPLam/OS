import pytest

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from modules.firm.models import Firm
from modules.sms.models import (
    SMSCampaign,
    SMSMessage,
    SMSPhoneNumber,
    SMSTemplate,
    SMSWebhookEvent,
)

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.mark.django_db
class TestSMSPhoneNumber:
    """Test SMS phone number validation."""

    def test_default_number_uniqueness(self, firm):
        """Only one default phone number per firm is allowed."""
        SMSPhoneNumber.objects.create(
            firm=firm,
            phone_number="+14155552671",
            is_default=True,
            status="active",
        )

        number = SMSPhoneNumber(
            firm=firm,
            phone_number="+14155552672",
            is_default=True,
            status="active",
        )

        with pytest.raises(ValidationError):
            number.full_clean()


@pytest.mark.django_db
class TestSMSTemplate:
    """Test SMS template rendering."""

    def test_character_count_and_segments(self, firm, user):
        """Templates should compute character count and segments."""
        template = SMSTemplate.objects.create(
            firm=firm,
            name="Reminder",
            template_type="reminder",
            message="a" * 200,
            created_by=user,
        )

        assert template.character_count == 200
        assert template.estimated_segments == 2

    def test_extract_and_render_variables(self, firm, user):
        """Templates should extract and render variables."""
        template = SMSTemplate.objects.create(
            firm=firm,
            name="Hello",
            template_type="notification",
            message="Hello {{name}}",
            created_by=user,
        )

        assert template.extract_variables() == ["name"]
        assert template.render({"name": "Alex"}) == "Hello Alex"


@pytest.mark.django_db
class TestSMSMessage:
    """Test SMS message properties."""

    def test_segment_count(self, firm):
        """Segment counts should reflect message length."""
        message = SMSMessage.objects.create(
            firm=firm,
            from_number=None,
            to_number="+14155552671",
            direction="outbound",
            message_body="a" * 200,
            status="sent",
        )

        assert message.character_count == 200
        assert message.segment_count == 2


@pytest.mark.django_db
class TestSMSCampaign:
    """Test SMS campaign analytics."""

    def test_delivery_and_reply_rates(self, firm, user):
        """Campaign rates should compute correctly."""
        campaign = SMSCampaign.objects.create(
            firm=firm,
            name="Launch",
            message_content="Hello",
            status="completed",
            recipients_total=10,
            messages_sent=10,
            messages_delivered=8,
            replies_received=2,
            created_by=user,
        )

        assert campaign.delivery_rate == 80
        assert campaign.reply_rate == 25


@pytest.mark.django_db
class TestSMSWebhookEvent:
    """Test SMS webhook event constraints."""

    def test_unique_event_constraint(self, firm):
        """Duplicate webhook events should be rejected."""
        SMSWebhookEvent.objects.create(
            firm=firm,
            twilio_message_sid="SM123",
            idempotency_key="id-1",
            event_type="status_callback",
            webhook_type="status",
            message_status="delivered",
        )

        with pytest.raises(IntegrityError):
            SMSWebhookEvent.objects.create(
                firm=firm,
                twilio_message_sid="SM123",
                idempotency_key="id-2",
                event_type="status_callback",
                webhook_type="status",
                message_status="delivered",
            )
