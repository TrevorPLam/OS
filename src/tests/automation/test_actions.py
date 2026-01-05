from types import SimpleNamespace

import pytest

from django.contrib.auth import get_user_model

from modules.automation.actions import (
    AddToListAction,
    InternalNotificationAction,
    RemoveFromListAction,
    SendEmailAction,
    SendSMSAction,
)
from modules.clients.models import Client, Contact
from modules.firm.models import Firm, FirmMembership
from modules.marketing.models import EmailTemplate, Segment, SegmentMembership
from modules.sms.models import SMSPhoneNumber, SMSMessage


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Automation Firm", slug="automation-firm")


@pytest.fixture
def client(firm):
    return Client.objects.create(
        firm=firm,
        company_name="Automation Client",
        primary_contact_name="Auto Contact",
        primary_contact_email="auto@example.com",
    )


@pytest.fixture
def contact(client):
    return Contact.objects.create(
        client=client,
        first_name="Alex",
        last_name="Automation",
        email="alex@example.com",
        mobile_phone="+15555550123",
    )


def _execution(firm, contact):
    return SimpleNamespace(
        firm=firm,
        contact=contact,
        workflow=SimpleNamespace(name="Test Workflow"),
        trigger_type="manual",
        trigger_data={},
        context_data={},
    )


@pytest.mark.django_db
def test_send_email_action_renders_template(monkeypatch, firm, contact):
    template = EmailTemplate.objects.create(
        firm=firm,
        name="Test Template",
        subject_line="Hello {{ contact_first_name }}",
        html_content="<p>Hello {{ contact_full_name }}</p>",
        plain_text_content="Hello {{ contact_full_name }}",
    )

    sent = {}

    def fake_send(**kwargs):
        sent.update(kwargs)
        return True

    monkeypatch.setattr("modules.core.notifications.EmailNotification.send", fake_send)

    execution = _execution(firm, contact)
    result = SendEmailAction.execute(
        execution,
        node=None,
        config={"template_id": template.id},
    )

    assert result["status"] == "sent"
    assert "Alex" in sent["subject"]


@pytest.mark.django_db
def test_send_sms_action_creates_message(monkeypatch, firm, contact):
    SMSPhoneNumber.objects.create(
        firm=firm,
        phone_number="+15555550100",
        is_default=True,
        status="active",
    )

    def fake_send_sms(self, to_number, message, from_number, media_urls=None):
        return {"success": True, "message_sid": "SM123", "status": "sent"}

    monkeypatch.setattr("modules.sms.twilio_service.TwilioService.send_sms", fake_send_sms)

    execution = _execution(firm, contact)
    result = SendSMSAction.execute(
        execution,
        node=None,
        config={"message": "Hello!"},
    )

    assert result["status"] == "sent"
    assert SMSMessage.objects.filter(firm=firm, to_number=contact.mobile_phone).exists()


@pytest.mark.django_db
def test_list_actions_manage_memberships(firm, contact):
    segment = Segment.objects.create(firm=firm, name="VIP", criteria={})
    execution = _execution(firm, contact)

    added = AddToListAction.execute(execution, node=None, config={"list_id": segment.id})
    assert added["status"] == "added"
    assert SegmentMembership.objects.filter(segment=segment, entity_id=contact.id).exists()

    removed = RemoveFromListAction.execute(execution, node=None, config={"list_id": segment.id})
    assert removed["status"] == "removed"
    assert not SegmentMembership.objects.filter(segment=segment, entity_id=contact.id).exists()


@pytest.mark.django_db
def test_internal_notification_action_sends_email(monkeypatch, firm, contact):
    user = get_user_model().objects.create_user(username="notify", email="notify@example.com")
    FirmMembership.objects.create(firm=firm, user=user, role="staff", is_active=True)

    sent = {}

    def fake_send(**kwargs):
        sent.update(kwargs)
        return True

    monkeypatch.setattr("modules.core.notifications.EmailNotification.send", fake_send)

    execution = _execution(firm, contact)
    result = InternalNotificationAction.execute(
        execution,
        node=None,
        config={"recipient_id": user.id, "message": "Hello"},
    )

    assert result["status"] == "sent"
    assert sent["to"] == user.email
