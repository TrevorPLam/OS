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
    """
    Create and return a Django test user for use in database-backed tests.
    
    Creates a user with username "stripe-user" and password "pass1234".
    
    Returns:
        django.contrib.auth.models.User: The created user instance.
    """
    return get_user_model().objects.create_user(username="stripe-user", password="pass1234")


@pytest.fixture
def firm(db):
    """
    Create and return a test Firm with name "Stripe Firm" and slug "stripe-firm".
    
    Returns:
        Firm: The created Firm instance with name "Stripe Firm" and slug "stripe-firm".
    """
    return Firm.objects.create(name="Stripe Firm", slug="stripe-firm")


@pytest.fixture
def client(firm, user):
    """
    Create and return a Client test instance associated with the given firm and user.
    
    Parameters:
    	firm (Firm): Firm to associate the client with.
    	user (User): Account manager for the client.
    
    Returns:
    	client (Client): Persisted Client with company_name "Webhook Co", primary contact "Ava Payee" (ava@example.com), client_since set to today, status "active", and linked firm and account_manager.
    """
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
    """
    Create and persist a sample Invoice for the given client.
    
    Parameters:
        client (Client): Client model instance; its associated Firm will be used for the invoice.
    
    Returns:
        Invoice: The newly created Invoice instance with invoice_number "INV-WEBHOOK-1", status "sent", subtotal and total_amount of 500.00, issue_date set to today, and due_date 30 days from today.
    """
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
        """
        Test stub that returns a predefined Stripe event payload.
        
        Ignores all positional and keyword arguments and returns the `payload` variable from the enclosing scope.
        
        Returns:
            mapping: The predefined event payload (the `payload` dict) used by tests.
        """
        return payload

    def null_duration(*_args, **_kwargs):
        """
        Return a no-op context manager; any passed positional or keyword arguments are ignored.
        
        Parameters:
            *_args: Ignored positional arguments.
            **_kwargs: Ignored keyword arguments.
        
        Returns:
            context_manager: A context manager (contextlib.nullcontext) that performs no setup or teardown.
        """
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