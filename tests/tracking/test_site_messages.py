import uuid

from unittest import mock

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from modules.firm.models import Firm
from modules.tracking.models import SiteMessage, SiteMessageImpression


@pytest.mark.django_db
def test_site_message_targeting_enforces_segments_and_frequency():
    # Freeze time so frequency-cap logic based on "today" is deterministic
    fixed_now = timezone.now()

    with mock.patch("django.utils.timezone.now", return_value=fixed_now):
        firm = Firm.objects.create(name="Targeted Firm", slug="targeted-firm")
        visitor_id = uuid.uuid4()
        session_id = uuid.uuid4()

        message = SiteMessage.objects.create(
            firm=firm,
            name="Segmented Banner",
            message_type="banner",
            status="published",
            targeting_rules={"segments": ["vip"]},
            content={"headline": "Welcome VIP"},
            frequency_cap=1,
        )

        client = APIClient()
        payload = {
            "firm_slug": firm.slug,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "url": "https://example.com/pricing",
            "segments": ["vip"],
        }

        response = client.post("/api/v1/tracking/site-messages/display/", payload, format="json")
        assert response.status_code == 200
        data = response.json().get("messages", [])
        assert len(data) == 1
        delivery_id = data[0]["delivery_id"]

        # Record a view to exhaust the frequency cap within the same day window
        SiteMessageImpression.objects.create(
            firm=firm,
            site_message=message,
            visitor_id=visitor_id,
            session=None,
            delivery_id=uuid.UUID(delivery_id),
            kind="view",
            occurred_at=fixed_now,
    )

    response = client.post("/api/v1/tracking/site-messages/display/", payload, format="json")
    assert response.status_code == 200
    assert response.json().get("messages") == []


@pytest.mark.django_db
def test_site_message_impression_logging_links_to_delivery():
    firm = Firm.objects.create(name="Logging Firm", slug="logging-firm")
    visitor_id = uuid.uuid4()
    session_id = uuid.uuid4()

    SiteMessage.objects.create(
        firm=firm,
        name="Click Me",
        message_type="modal",
        status="published",
        targeting_rules={"audience": {"allow_known": True}},
        content={"headline": "Test message"},
    )

    client = APIClient()
    display_payload = {
        "firm_slug": firm.slug,
        "visitor_id": visitor_id,
        "session_id": session_id,
        "url": "https://example.com/home",
    }
    display_response = client.post("/api/v1/tracking/site-messages/display/", display_payload, format="json")
    assert display_response.status_code == 200
    messages = display_response.json().get("messages", [])
    assert messages, "Expected at least one message"

    delivery_id = messages[0]["delivery_id"]
    impression_payload = {"delivery_id": delivery_id, "event": "click", "url": "https://example.com/home"}
    log_response = client.post("/api/v1/tracking/site-messages/impressions/", impression_payload, format="json")
    assert log_response.status_code == 201

    recorded = SiteMessageImpression.objects.filter(delivery_id=delivery_id, kind="click").first()
    assert recorded is not None
    assert str(recorded.visitor_id) == str(visitor_id)
