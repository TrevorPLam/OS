"""
Stripe Webhook Handler for payment events (SEC-1: Idempotency tracking).

Handles asynchronous payment confirmations and updates.
"""

import logging
import re
from collections.abc import Mapping
from datetime import timedelta

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from config.sentry import add_webhook_breadcrumb
from .stripe_schema import ValidationError, validate_stripe_event_payload
from modules.core.rate_limiting import enforce_webhook_rate_limit
from modules.core.telemetry import log_event, log_metric, track_duration
from modules.finance.billing import handle_payment_failure
from modules.finance.models import Invoice, StripeWebhookEvent

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

REDACTION_TOKEN = "[REDACTED]"
CARD_NUMBER_KEYS = {
    "card_number",
    "cardnumber",
    "number",
    "pan",
    "primary_account_number",
    "account_number",
}
CVV_KEYS = {"cvc", "cvv", "cvc2", "card_cvc", "security_code"}
EMAIL_KEYS = {"email", "receipt_email", "billing_email", "customer_email"}
PHONE_KEYS = {"phone", "phone_number", "billing_phone", "customer_phone", "mobile"}

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")
CARD_PATTERN = re.compile(r"(?:\d[ -]*?){12,19}")


def _normalize_key(raw_key: str) -> str:
    """Normalize keys for consistent redaction checks."""
    return re.sub(r"[^a-z0-9]+", "_", raw_key.lower()).strip("_")


def _is_luhn_valid(candidate: str) -> bool:
    """Check card-number candidates with a Luhn checksum to avoid false positives."""
    digits = [int(char) for char in re.sub(r"\D", "", candidate)]
    if len(digits) < 12:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _should_redact_value(key: str | None, value: object) -> bool:
    """Determine whether a value should be redacted based on key or content."""
    if key:
        normalized = _normalize_key(str(key))
        if normalized in CARD_NUMBER_KEYS | CVV_KEYS | EMAIL_KEYS | PHONE_KEYS:
            return True

    if isinstance(value, str):
        if EMAIL_PATTERN.search(value):
            return True
        if PHONE_PATTERN.search(value):
            return True
        if CARD_PATTERN.search(value) and _is_luhn_valid(value):
            return True
    return False


def sanitize_webhook_payload(payload: object, key: str | None = None) -> object:
    """Return a redacted copy of webhook payloads for safe audit storage.

    Meta-commentary:
    - Mapping: Applies SEC-PII redaction rules before persisting Stripe webhook payloads.
    - Reasoning: Stripe payloads can contain card data, emails, and phone numbers.
    - Limitation: Redaction is pattern-based and errs on the side of removing PII.
    """
    if _should_redact_value(key, payload):
        return REDACTION_TOKEN
    if isinstance(payload, Mapping):
        return {
            child_key: sanitize_webhook_payload(child_value, child_key)
            for child_key, child_value in payload.items()
        }
    if isinstance(payload, list):
        return [sanitize_webhook_payload(item, key) for item in payload]
    return payload


@csrf_exempt
@require_POST
@ratelimit(
    key="ip",
    rate=settings.WEBHOOK_RATE_LIMITS["stripe"],
    method="POST",
    block=False,
)
def stripe_webhook(request):
    """
    Handle incoming Stripe webhook HTTP POST requests by enforcing rate limits and idempotency, verifying the Stripe signature, validating the payload schema, dispatching the event to the appropriate handler, and persisting a redacted audit record.
    
    Returns:
        HttpResponse: 200 when the event is accepted or a duplicate delivery is detected, 400 for invalid payloads or signature/schema validation failures, 500 for internal processing errors.
    
    Notes:
        - Side effects include creating a StripeWebhookEvent audit record (with PII redacted) and updating related Invoice records depending on event type.
    """
    rate_limit_response = enforce_webhook_rate_limit(
        request, provider="stripe", endpoint="stripe_webhook"
    )
    if rate_limit_response:
        return rate_limit_response

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        # Verify webhook signature before any processing to reject forged payloads early.
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        logger.error("Stripe webhook invalid payload")
        log_event(
            "stripe_webhook_invalid_payload",
            provider="stripe",
            error_class=e.__class__.__name__,
        )
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error("Stripe webhook signature verification failed")
        log_event(
            "stripe_webhook_signature_failed",
            provider="stripe",
            error_class=e.__class__.__name__,
        )
        return HttpResponse(status=400)

    try:
        # Validate payload shape to avoid downstream KeyError/TypeError crashes.
        validated_event = validate_stripe_event_payload(event)
    except (ValidationError, ValueError) as exc:
        logger.error("Stripe webhook schema validation failed")
        log_event(
            "stripe_webhook_schema_invalid",
            provider="stripe",
            error_class=exc.__class__.__name__,
        )
        return HttpResponse(status=400)

    # Extract event metadata after validation to keep downstream logic deterministic.
    event_id = validated_event.id
    event_type = validated_event.type
    event_data = validated_event.data.object
    # SECURITY: Persist a redacted event payload to avoid storing PII in audit logs.
    sanitized_event = sanitize_webhook_payload(validated_event.model_dump())

    add_webhook_breadcrumb(
        message="Stripe webhook received",
        level="info",
        event_id=event_id,
        event_type=event_type,
    )
    
    # SEC-1: Check for duplicate webhook event
    # Try to create webhook event record atomically
    try:
        # Extract firm from event metadata (if available)
        metadata = event_data.get("metadata", {})
        invoice_id = metadata.get("invoice_id")
        firm = None
        
        if invoice_id:
            try:
                invoice = Invoice.objects.select_related("firm").get(id=invoice_id)
                firm = invoice.firm
            except Invoice.DoesNotExist:
                pass
        
        with transaction.atomic():
            # Try to create webhook event record
            webhook_event = StripeWebhookEvent.objects.create(
                firm=firm,  # May be None if we can't determine firm yet
                stripe_event_id=event_id,
                idempotency_key=event_id,
                event_type=event_type,
                event_data=sanitized_event,
                processed_successfully=False,  # Will be updated after processing
            )
            
    except IntegrityError:
        # Duplicate webhook delivery - event already processed
        logger.info(f"Duplicate Stripe webhook event received: {event_id}")
        add_webhook_breadcrumb(
            message="Stripe webhook duplicate",
            level="warning",
            event_id=event_id,
            event_type=event_type,
        )
        log_event(
            "stripe_webhook_duplicate",
            provider="stripe",
            webhook_type=event_type,
            event_id=event_id,
        )
        log_metric(
            "stripe_webhook_duplicate",
            provider="stripe",
            webhook_type=event_type,
        )
        # Return 200 OK without reprocessing (SEC-1 acceptance criteria)
        return HttpResponse(status=200)

    logger.info(f"Received Stripe webhook: {event_id}")
    log_event(
        "stripe_webhook_received",
        provider="stripe",
        webhook_type=event_type,
        event_id=event_id,
    )

    # Process the event
    processing_error = None
    try:
        with track_duration(
            "stripe_webhook_process",
            provider="stripe",
            webhook_type=event_type,
        ):
            if event_type == "checkout.session.completed":
                handle_checkout_session_completed(event_data, webhook_event)
            elif event_type == "payment_intent.succeeded":
                handle_payment_intent_succeeded(event_data, webhook_event)
            elif event_type == "payment_intent.payment_failed":
                handle_payment_intent_failed(event_data, webhook_event)
            elif event_type == "invoice.payment_succeeded":
                handle_invoice_payment_succeeded(event_data, webhook_event)
            elif event_type == "invoice.payment_failed":
                handle_invoice_payment_failed(event_data, webhook_event)
            elif event_type == "charge.refunded":
                handle_charge_refunded(event_data, webhook_event)
            else:
                logger.info(f"Unhandled Stripe event type: {event_type}")
                add_webhook_breadcrumb(
                    message="Stripe webhook unhandled",
                    level="info",
                    event_id=event_id,
                    event_type=event_type,
                )
                log_event(
                    "stripe_webhook_unhandled",
                    provider="stripe",
                    webhook_type=event_type,
                )
        
        # Mark webhook event as successfully processed
        webhook_event.processed_successfully = True
        webhook_event.save(update_fields=["processed_successfully"])
        
    except Exception as e:
        processing_error = str(e)
        logger.error(f"Error processing Stripe webhook: {e}", exc_info=True)
        add_webhook_breadcrumb(
            message="Stripe webhook processing failed",
            level="error",
            event_id=event_id,
            event_type=event_type,
            extra_data={"error_class": e.__class__.__name__},
        )
        log_event(
            "stripe_webhook_failed",
            provider="stripe",
            webhook_type=event_type,
            error_class=e.__class__.__name__,
        )
        
        # Mark webhook event as failed
        webhook_event.processed_successfully = False
        webhook_event.error_message = processing_error
        webhook_event.save(update_fields=["processed_successfully", "error_message"])
        
        return HttpResponse(status=500)

    log_metric(
        "stripe_webhook_processed",
        provider="stripe",
        webhook_type=event_type,
        status="success",
    )
    add_webhook_breadcrumb(
        message="Stripe webhook processed",
        level="info",
        event_id=event_id,
        event_type=event_type,
    )
    return HttpResponse(status=200)


def handle_payment_intent_succeeded(payment_intent, webhook_event=None):
    """
    Handle successful payment intent.
    Update invoice status to paid.
    """
    metadata = payment_intent.get("metadata", {})
    invoice_id = metadata.get("invoice_id")

    if not invoice_id:
        logger.warning("Payment intent missing invoice metadata")
        log_event(
            "stripe_payment_intent_missing_invoice_id",
            provider="stripe",
            webhook_type="payment_intent.succeeded",
        )
        return

    try:
        invoice = Invoice.objects.get(id=invoice_id)

        # SECURITY: Validate amount_received is numeric before arithmetic
        # See: FORENSIC_AUDIT.md Issue #1.3
        amount_received_cents = payment_intent.get("amount_received")
        if not isinstance(amount_received_cents, (int, float)):
            logger.error(
                "Invalid amount_received type from Stripe",
                extra={
                    "type": type(amount_received_cents).__name__,
                    "value": amount_received_cents,
                    "invoice_id": invoice_id,
                }
            )
            raise ValueError(f"Invalid amount_received type: {type(amount_received_cents).__name__}")
        
        if amount_received_cents < 0:
            logger.error(
                "Negative amount_received from Stripe",
                extra={"amount": amount_received_cents, "invoice_id": invoice_id}
            )
            raise ValueError(f"Negative amount_received: {amount_received_cents}")

        # Calculate amount received (in cents, convert to dollars)
        amount_received = amount_received_cents / 100

        # Update invoice
        invoice.amount_paid += amount_received

        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = "paid"
            invoice.paid_date = timezone.now().date()
        else:
            invoice.status = "partial"

        invoice.autopay_status = "succeeded"
        invoice.autopay_next_charge_at = None
        invoice.save(update_fields=["amount_paid", "status", "paid_date", "autopay_status", "autopay_next_charge_at"])

        # Link webhook event to invoice (SEC-1)
        if webhook_event:
            webhook_event.invoice = invoice
            webhook_event.firm = invoice.firm
            webhook_event.save(update_fields=["invoice", "firm"])

        logger.info("Invoice updated from payment intent")
        log_metric(
            "stripe_payment_intent_succeeded",
            provider="stripe",
            webhook_type="payment_intent.succeeded",
            status="success",
        )

    except Invoice.DoesNotExist:
        logger.error("Invoice not found for payment intent")
        log_event(
            "stripe_payment_intent_invoice_missing",
            provider="stripe",
            webhook_type="payment_intent.succeeded",
        )
    except Exception as e:
        logger.error("Error updating invoice from payment intent")
        log_event(
            "stripe_payment_intent_update_failed",
            provider="stripe",
            webhook_type="payment_intent.succeeded",
            error_class=e.__class__.__name__,
        )


def handle_payment_intent_failed(payment_intent, webhook_event=None):
    """
    Handle failed payment intent.
    Log the failure for manual review.
    """
    metadata = payment_intent.get("metadata", {})
    invoice_id = metadata.get("invoice_id")

    logger.warning("Payment intent reported failure")
    log_event(
        "stripe_payment_intent_failed",
        provider="stripe",
        webhook_type="payment_intent.payment_failed",
        status="failed",
    )

    if invoice_id:
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            handle_payment_failure(
                invoice,
                failure_reason=payment_intent.get("last_payment_error", {}).get("message", "payment_failed"),
                failure_code=payment_intent.get("last_payment_error", {}).get("code"),
            )
            invoice.autopay_status = "failed"
            invoice.autopay_next_charge_at = timezone.now() + timedelta(days=3)
            invoice.save(update_fields=["autopay_status", "autopay_next_charge_at"])
            
            # Link webhook event to invoice (SEC-1)
            if webhook_event:
                webhook_event.invoice = invoice
                webhook_event.firm = invoice.firm
                webhook_event.save(update_fields=["invoice", "firm"])
                
        except Invoice.DoesNotExist:
            pass


def handle_invoice_payment_succeeded(stripe_invoice, webhook_event=None):
    """
    Handle successful Stripe invoice payment.
    """
    metadata = stripe_invoice.get("metadata", {})
    invoice_id = metadata.get("invoice_id")

    if not invoice_id:
        logger.warning("Stripe invoice missing invoice metadata")
        log_event(
            "stripe_invoice_missing_invoice_id",
            provider="stripe",
            webhook_type="invoice.payment_succeeded",
        )
        return

    try:
        invoice = Invoice.objects.get(id=invoice_id)
        amount_paid = stripe_invoice["amount_paid"] / 100

        invoice.amount_paid += amount_paid
        invoice.status = "paid"
        invoice.paid_date = timezone.now().date()
        invoice.autopay_status = "succeeded"
        invoice.autopay_next_charge_at = None
        invoice.save(update_fields=["amount_paid", "status", "paid_date", "autopay_status", "autopay_next_charge_at"])

        # Link webhook event to invoice (SEC-1)
        if webhook_event:
            webhook_event.invoice = invoice
            webhook_event.firm = invoice.firm
            webhook_event.save(update_fields=["invoice", "firm"])

        logger.info("Invoice marked as paid from Stripe invoice")
        log_metric(
            "stripe_invoice_payment_succeeded",
            provider="stripe",
            webhook_type="invoice.payment_succeeded",
            status="success",
        )

    except Invoice.DoesNotExist:
        logger.error("Invoice not found for Stripe invoice")
        log_event(
            "stripe_invoice_payment_invoice_missing",
            provider="stripe",
            webhook_type="invoice.payment_succeeded",
        )


def handle_invoice_payment_failed(stripe_invoice, webhook_event=None):
    """
    Handle failed Stripe invoice payment.
    """
    metadata = stripe_invoice.get("metadata", {})
    invoice_id = metadata.get("invoice_id")

    logger.warning("Stripe invoice payment failed")
    log_event(
        "stripe_invoice_payment_failed",
        provider="stripe",
        webhook_type="invoice.payment_failed",
        status="failed",
    )

    if invoice_id:
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            handle_payment_failure(invoice, failure_reason="processor_failure")
            invoice.autopay_status = "failed"
            invoice.autopay_next_charge_at = timezone.now() + timedelta(days=3)
            invoice.save(update_fields=["autopay_status", "autopay_next_charge_at"])
            
            # Link webhook event to invoice (SEC-1)
            if webhook_event:
                webhook_event.invoice = invoice
                webhook_event.firm = invoice.firm
                webhook_event.save(update_fields=["invoice", "firm"])
                
        except Invoice.DoesNotExist:
            logger.error("Invoice not found for Stripe invoice failure")
            log_event(
                "stripe_invoice_payment_failure_invoice_missing",
                provider="stripe",
                webhook_type="invoice.payment_failed",
            )


def handle_charge_refunded(charge, webhook_event=None):
    """
    Handle refunded charge.
    Update invoice to reflect refund.
    """
    metadata = charge.get("metadata", {})
    invoice_id = metadata.get("invoice_id")

    if not invoice_id:
        return

    try:
        invoice = Invoice.objects.get(id=invoice_id)
        refund_amount = charge["amount_refunded"] / 100

        invoice.amount_paid -= refund_amount

        if invoice.amount_paid <= 0:
            invoice.status = "cancelled"
            invoice.amount_paid = 0
        elif invoice.amount_paid < invoice.total_amount:
            invoice.status = "partial"

        invoice.save()

        # Link webhook event to invoice (SEC-1)
        if webhook_event:
            webhook_event.invoice = invoice
            webhook_event.firm = invoice.firm
            webhook_event.save(update_fields=["invoice", "firm"])

        logger.info("Invoice refunded")
        log_metric(
            "stripe_charge_refunded",
            provider="stripe",
            webhook_type="charge.refunded",
            status="success",
        )

    except Invoice.DoesNotExist:
        logger.error("Invoice not found for refund")
        log_event(
            "stripe_refund_invoice_missing",
            provider="stripe",
            webhook_type="charge.refunded",
        )


def handle_checkout_session_completed(session, webhook_event=None):
    """
    Handle completed Stripe Checkout session.

    This is triggered when a customer successfully completes payment
    through the Stripe Checkout hosted page.
    """
    metadata = session.get("metadata", {})
    invoice_id = metadata.get("invoice_id")

    if not invoice_id:
        logger.warning("Checkout session missing invoice metadata")
        log_event(
            "stripe_checkout_session_missing_invoice_id",
            provider="stripe",
            webhook_type="checkout.session.completed",
        )
        return

    try:
        invoice = Invoice.objects.get(id=invoice_id)

        # Get payment amount (in cents, convert to dollars)
        amount_paid = session["amount_total"] / 100

        # Update invoice
        invoice.amount_paid += amount_paid

        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = "paid"
            invoice.paid_date = timezone.now().date()
        else:
            invoice.status = "partial"

        invoice.save(update_fields=["amount_paid", "status", "paid_date"])

        # Link webhook event to invoice (SEC-1)
        if webhook_event:
            webhook_event.invoice = invoice
            webhook_event.firm = invoice.firm
            webhook_event.save(update_fields=["invoice", "firm"])

        logger.info("Invoice updated from checkout session")
        log_metric(
            "stripe_checkout_session_completed",
            provider="stripe",
            webhook_type="checkout.session.completed",
            status="success",
        )

    except Invoice.DoesNotExist:
        logger.error("Invoice not found for checkout session")
        log_event(
            "stripe_checkout_session_invoice_missing",
            provider="stripe",
            webhook_type="checkout.session.completed",
        )
    except Exception as e:
        logger.error("Error updating invoice from checkout session")
        log_event(
            "stripe_checkout_session_update_failed",
            provider="stripe",
            webhook_type="checkout.session.completed",
            error_class=e.__class__.__name__,
        )