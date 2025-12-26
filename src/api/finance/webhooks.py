"""
Stripe Webhook Handler for payment events.

Handles asynchronous payment confirmations and updates.
"""

import logging
from datetime import timedelta

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from modules.core.telemetry import log_event, log_metric, track_duration
from modules.finance.billing import handle_payment_failure
from modules.finance.models import Invoice

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events.

    Verifies webhook signature and processes payment events:
    - payment_intent.succeeded: Mark invoice as paid
    - payment_intent.payment_failed: Log failure
    - invoice.payment_succeeded: Update invoice status
    - charge.refunded: Handle refunds
    """
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

    # Handle the event
    event_type = event["type"]
    event_data = event["data"]["object"]

    logger.info("Received Stripe webhook")
    log_event(
        "stripe_webhook_received",
        provider="stripe",
        webhook_type=event_type,
    )

    try:
        with track_duration(
            "stripe_webhook_process",
            provider="stripe",
            webhook_type=event_type,
        ):
            if event_type == "payment_intent.succeeded":
                handle_payment_intent_succeeded(event_data)
            elif event_type == "payment_intent.payment_failed":
                handle_payment_intent_failed(event_data)
            elif event_type == "invoice.payment_succeeded":
                handle_invoice_payment_succeeded(event_data)
            elif event_type == "invoice.payment_failed":
                handle_invoice_payment_failed(event_data)
            elif event_type == "charge.refunded":
                handle_charge_refunded(event_data)
            else:
                logger.info("Unhandled Stripe event type")
                log_event(
                    "stripe_webhook_unhandled",
                    provider="stripe",
                    webhook_type=event_type,
                )
    except Exception as e:
        logger.error("Error processing Stripe webhook")
        log_event(
            "stripe_webhook_failed",
            provider="stripe",
            webhook_type=event_type,
            error_class=e.__class__.__name__,
        )
        return HttpResponse(status=500)

    log_metric(
        "stripe_webhook_processed",
        provider="stripe",
        webhook_type=event_type,
        status="success",
    )
    return HttpResponse(status=200)


def handle_payment_intent_succeeded(payment_intent):
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


def handle_payment_intent_failed(payment_intent):
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
        except Invoice.DoesNotExist:
            pass


def handle_invoice_payment_succeeded(stripe_invoice):
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


def handle_invoice_payment_failed(stripe_invoice):
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
        except Invoice.DoesNotExist:
            logger.error("Invoice not found for Stripe invoice failure")
            log_event(
                "stripe_invoice_payment_failure_invoice_missing",
                provider="stripe",
                webhook_type="invoice.payment_failed",
            )


def handle_charge_refunded(charge):
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
