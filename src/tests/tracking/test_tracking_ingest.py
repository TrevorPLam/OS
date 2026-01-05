import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from modules.automation.triggers import TriggerDetector
from modules.clients.models import Client, Contact
from modules.firm.models import Firm, FirmMembership
from modules.tracking.models import SiteMessage, TrackingAbuseEvent, TrackingEvent, TrackingKey, TrackingSession


@pytest.mark.django_db
def test_tracking_collect_creates_event_and_triggers_automation(settings, monkeypatch):
    firm = Firm.objects.create(name="Acme Corp", slug="acme")
    client = Client.objects.create(firm=firm, company_name="ACME LLC", primary_contact_name="Test")
    contact = Contact.objects.create(client=client, first_name="Test", last_name="User", email="test@example.com")
    key, secret = TrackingKey.issue(firm=firm)

    triggered = {}

    def fake_detect(firm, trigger_type, event_data, contact=None):
        triggered["firm"] = firm
        triggered["trigger_type"] = trigger_type
        triggered["event_name"] = event_data.get("event_name")
        triggered["contact"] = contact
        return []

    monkeypatch.setattr(TriggerDetector, "detect_and_trigger", fake_detect)

    payload = {
        "events": [
          {
              "tracking_key": secret,
              "tracking_key_id": str(key.public_id),
              "firm_slug": firm.slug,
              "event_type": "page_view",
              "name": "Homepage View",
              "url": "https://example.com/",
              "referrer": "",
              "properties": {"utm_source": "test"},
              "consent_state": "granted",
              "visitor_id": "00000000-0000-4000-8000-000000000001",
              "session_id": "10000000-0000-4000-8000-000000000001",
              "contact_id": contact.id,
          }
        ]
    }

    api_client = APIClient()
    response = api_client.post("/api/v1/tracking/collect/", payload, format="json")

    assert response.status_code == 201
    assert TrackingEvent.objects.filter(firm=firm, name="Homepage View").count() == 1
    event = TrackingEvent.objects.get(firm=firm, name="Homepage View")
    assert event.session.session_id.hex == "10000000000040008000000000000001"
    assert event.tracking_key == key
    assert event.used_fallback_key is False
    assert triggered["trigger_type"] == "site_page_view"
    assert triggered["event_name"] == "Homepage View"
    assert triggered["contact"] == contact


@pytest.mark.django_db
def test_tracking_summary_requires_membership(settings):
    firm = Firm.objects.create(name="Acme Corp", slug="acme")
    user = get_user_model().objects.create_user(username="tracker", password="password")
    FirmMembership.objects.create(firm=firm, user=user, role="firm_admin", is_active=True)

    session = TrackingSession.objects.create(firm=firm)
    TrackingEvent.objects.create(
        firm=firm,
        session=session,
        event_type="page_view",
        name="Dashboard",
        url="/dashboard",
        referrer="",
        properties={"utm_source": "email"},
    )

    api_client = APIClient()
    api_client.force_authenticate(user=user)

    response = api_client.get("/api/v1/tracking/summary/", HTTP_HOST="acme.example.com")

    assert response.status_code == 200
    data = response.json()
    assert data["page_views"] == 1
    assert data["unique_visitors"] == 1
    assert data["window_days"] == 30
    assert data["time_series"]


@pytest.mark.django_db
def test_tracking_collect_rate_limits(settings):
    settings.TRACKING_INGEST_RATE_LIMIT_PER_MINUTE = 1
    firm = Firm.objects.create(name="Acme Corp", slug="acme")
    key, secret = TrackingKey.issue(firm=firm)
    payload = {
        "events": [
            {
                "tracking_key": secret,
                "firm_slug": firm.slug,
                "event_type": "page_view",
                "name": "Homepage View",
                "url": "https://example.com/",
                "referrer": "",
                "properties": {},
                "consent_state": "granted",
                "visitor_id": "00000000-0000-4000-8000-000000000001",
                "session_id": "10000000-0000-4000-8000-000000000001",
            },
            {
                "tracking_key": secret,
                "firm_slug": firm.slug,
                "event_type": "page_view",
                "name": "Second View",
                "url": "https://example.com/pricing",
                "referrer": "",
                "properties": {},
                "consent_state": "granted",
                "visitor_id": "00000000-0000-4000-8000-000000000002",
                "session_id": "20000000-0000-4000-8000-000000000002",
            },
        ]
    }

    api_client = APIClient()
    response = api_client.post("/api/v1/tracking/collect/", payload, format="json")

    assert response.status_code == 429
    assert TrackingAbuseEvent.objects.filter(firm=firm, reason="rate_limited").exists()


@pytest.mark.django_db
def test_site_message_builder_create_and_update():
    firm = Firm.objects.create(name="Acme Corp", slug="acme")
    user = get_user_model().objects.create_user(username="builder", password="password")
    FirmMembership.objects.create(firm=firm, user=user, role="firm_admin", is_active=True)

    client = APIClient()
    client.force_authenticate(user=user)
    create_resp = client.post(
        "/api/v1/tracking/site-messages/",
        {
            "name": "Promo Modal",
            "message_type": "modal",
            "status": "draft",
            "targeting_rules": {"segments": ["new_visitors"]},
            "content": {"headline": "Save 10%", "body": "Sign up for early access"},
            "personalization_tokens": ["contact.first_name"],
            "form_schema": {"fields": [{"name": "email", "type": "email"}]},
        },
        format="json",
        HTTP_HOST="acme.example.com",
    )
    assert create_resp.status_code == 201
    message_id = create_resp.json()["id"]
    update_resp = client.patch(
        f"/api/v1/tracking/site-messages/{message_id}/",
        {"status": "published", "frequency_cap": 3},
        format="json",
        HTTP_HOST="acme.example.com",
    )
    assert update_resp.status_code == 200
    assert SiteMessage.objects.get(id=message_id).status == "published"
