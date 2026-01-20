import copy

from api.finance.webhooks import REDACTION_TOKEN, sanitize_webhook_payload


def test_sanitize_webhook_payload_redacts_sensitive_fields():
    """Ensure Stripe webhook payloads remove PII before storage."""
    payload = {
        "data": {
            "object": {
                "billing_details": {
                    "email": "ada@example.com",
                    "phone": "+1 (415) 555-1234",
                },
                "payment_method_details": {
                    "card": {"number": "4242 4242 4242 4242", "cvc": "123"}
                },
            }
        },
        "metadata": {"note": "call me at 415-555-9999"},
    }

    sanitized = sanitize_webhook_payload(payload)

    assert sanitized["data"]["object"]["billing_details"]["email"] == REDACTION_TOKEN
    assert sanitized["data"]["object"]["billing_details"]["phone"] == REDACTION_TOKEN
    assert sanitized["data"]["object"]["payment_method_details"]["card"]["number"] == REDACTION_TOKEN
    assert sanitized["data"]["object"]["payment_method_details"]["card"]["cvc"] == REDACTION_TOKEN
    assert sanitized["metadata"]["note"] == REDACTION_TOKEN


def test_sanitize_webhook_payload_preserves_non_sensitive_fields():
    """Non-sensitive fields should remain intact after sanitization."""
    payload = {
        "id": "evt_123",
        "type": "payment_intent.succeeded",
        "data": {"object": {"amount": 5000, "currency": "usd"}},
    }

    sanitized = sanitize_webhook_payload(payload)

    assert sanitized["id"] == "evt_123"
    assert sanitized["type"] == "payment_intent.succeeded"
    assert sanitized["data"]["object"]["amount"] == 5000
    assert sanitized["data"]["object"]["currency"] == "usd"


def test_sanitize_webhook_payload_does_not_mutate_input():
    """Ensure sanitization returns a new structure without mutating the original."""
    payload = {"customer_email": "grace@example.com"}
    original = copy.deepcopy(payload)

    _ = sanitize_webhook_payload(payload)

    assert payload == original
