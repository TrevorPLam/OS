from datetime import date, timedelta
from decimal import Decimal
import contextlib

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from api.finance import webhooks
from api.finance.stripe_schema import ValidationError, validate_stripe_event_payload
from modules.clients.models import Client
from modules.finance.models import Invoice, StripeWebhookEvent
from modules.firm.models import Firm


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="stripe-user", password="pass1234")


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Stripe Firm", slug="stripe-firm")


@pytest.fixture
def client(firm, user):
    return Client.objects.create(
        company_name="Webhook Co",
        primary_contact_name="Ava Payee",
        primary_contact_email="ava@example.com",
        firm=firm,
        client_since=date.today(),
        account_manager=user,
        status="active",
    )


@pytest.fixture
def invoice(client):
    return Invoice.objects.create(
        firm=client.firm,
        client=client,
        invoice_number="INV-WEBHOOK-1",
        status="sent",
        subtotal=Decimal("500.00"),
        total_amount=Decimal("500.00"),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        line_items=[],
    )


def test_validate_stripe_event_payload_happy():
    # Happy path: minimal Stripe payload with required fields validates cleanly.
    payload = {
        "id": "evt_123",
        "type": "payment_intent.succeeded",
        "data": {"object": {"amount_received": 5000}},
    }

    result = validate_stripe_event_payload(payload)

    assert result.id == "evt_123"
    assert result.type == "payment_intent.succeeded"
    assert result.data.object["amount_received"] == 5000


def test_validate_stripe_event_payload_empty_data():
    # Edge case: empty data block should fail because object is required.
    payload = {"id": "evt_123", "type": "payment_intent.succeeded", "data": {}}

    with pytest.raises(ValidationError):
        validate_stripe_event_payload(payload)


def test_validate_stripe_event_payload_error_type():
    # Error case: non-mapping payloads should raise a clear validation error.
    with pytest.raises(ValueError):
        validate_stripe_event_payload("not-a-mapping")


@pytest.mark.django_db
def test_stripe_webhook_duplicate_event_returns_ok(monkeypatch, invoice):
    # Replay test: duplicate webhook IDs should be acknowledged without reprocessing.
    payload = {
        "id": "evt_replay_123",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "metadata": {"invoice_id": str(invoice.id)},
                "amount_received": 50000,
            }
        },
    }

    def fake_construct_event(*_args, **_kwargs):
        return payload

    def null_duration(*_args, **_kwargs):
        return contextlib.nullcontext()

    monkeypatch.setattr(webhooks.stripe.Webhook, "construct_event", fake_construct_event)
    monkeypatch.setattr(webhooks, "enforce_webhook_rate_limit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(webhooks, "track_duration", null_duration)

    factory = APIRequestFactory()
    request = factory.post("/api/v1/finance/webhooks/stripe/", data=b"{}", content_type="application/json")
    request.META["HTTP_STRIPE_SIGNATURE"] = "test-signature"

    first_response = webhooks.stripe_webhook(request)
    second_response = webhooks.stripe_webhook(request)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert StripeWebhookEvent.objects.filter(stripe_event_id="evt_replay_123").count() == 1
