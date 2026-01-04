"""
Stripe Webhook Handler for payment events (SEC-1: Idempotency tracking).

Handles asynchronous payment confirmations and updates.
"""

import logging
from datetime import timedelta

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from modules.core.rate_limiting import enforce_webhook_rate_limit
from modules.core.telemetry import log_event, log_metric, track_duration
from modules.finance.billing import handle_payment_failure
from modules.finance.models import Invoice, StripeWebhookEvent

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


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
    Handle Stripe webhook events (SEC-1: Idempotency tracking, SEC-2: Rate limiting).

    Verifies webhook signature and processes payment events:
    - payment_intent.succeeded: Mark invoice as paid
    - payment_intent.payment_failed: Log failure
    - invoice.payment_succeeded: Update invoice status
    - charge.refunded: Handle refunds
    
    SEC-1: Implements idempotency by checking StripeWebhookEvent before processing.
    SEC-2: Rate limited per settings to prevent webhook flooding.
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
        # Verify webhook signature
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

    # Extract event metadata
    event_id = event["id"]
    event_type = event["type"]
    event_data = event["data"]["object"]
    
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
                event_data=event,
                processed_successfully=False,  # Will be updated after processing
            )
            
    except IntegrityError:
        # Duplicate webhook delivery - event already processed
        logger.info(f"Duplicate Stripe webhook event received: {event_id}")
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

        # Calculate amount received (in cents, convert to dollars)
        amount_received = payment_intent["amount_received"] / 100

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
