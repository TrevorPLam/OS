"""
Square Webhook Handler for payment events (PAY-2, SEC-1: Idempotency tracking).

Handles asynchronous payment confirmations and updates from Square.
"""

import hashlib
import hmac
import json
import logging
from decimal import Decimal

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
from modules.finance.models import Invoice, SquareWebhookEvent

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
@ratelimit(
    key="ip",
    rate=settings.WEBHOOK_RATE_LIMITS["square"],
    method="POST",
    block=False,
)
def square_webhook(request):
    """
    Handle Square webhook events (SEC-1: Idempotency tracking, SEC-2: Rate limiting).

    Verifies webhook signature and processes payment events:
    - payment.created: Log payment initiation
    - payment.updated: Update invoice status based on payment status
    - refund.created: Handle refunds
    - refund.updated: Update refund status
    
    SEC-1: Implements idempotency by checking SquareWebhookEvent before processing.
    SEC-2: Rate limited per settings to prevent webhook flooding.
    """
    rate_limit_response = enforce_webhook_rate_limit(
        request, provider="square", endpoint="square_webhook"
    )
    if rate_limit_response:
        return rate_limit_response

    payload = request.body
    signature = request.META.get("HTTP_X_SQUARE_SIGNATURE")
    webhook_url = settings.SQUARE_WEBHOOK_URL

    # Verify webhook signature
    if not verify_square_signature(payload, signature, webhook_url):
        logger.error("Square webhook signature verification failed")
        log_event(
            "square_webhook_signature_failed",
            provider="square",
        )
        return HttpResponse(status=400)

    try:
        event = json.loads(payload)
    except ValueError as e:
        logger.error("Square webhook invalid payload")
        log_event(
            "square_webhook_invalid_payload",
            provider="square",
            error_class=e.__class__.__name__,
        )
        return HttpResponse(status=400)

    # Extract event metadata
    event_id = event.get("event_id") or event.get("merchant_id", "unknown")  # Square uses event_id
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    
    # SEC-1: Check for duplicate webhook event
    # Try to create webhook event record atomically
    try:
        # Extract firm from event data (if available)
        reference_id = event_data.get("reference_id")  # This should be invoice_id
        firm = None
        
        if reference_id:
            try:
                invoice = Invoice.objects.select_related("firm").get(id=int(reference_id))
                firm = invoice.firm
            except (Invoice.DoesNotExist, ValueError):
                pass
        
        with transaction.atomic():
            # Try to create webhook event record
            webhook_event = SquareWebhookEvent.objects.create(
                firm=firm,  # May be None if we can't determine firm yet
                square_event_id=event_id,
                idempotency_key=event_id,
                event_type=event_type,
                event_data=event,
                processed_successfully=False,  # Will be updated after processing
            )
            
    except IntegrityError:
        # Duplicate webhook delivery - event already processed
        logger.info(f"Duplicate Square webhook event received: {event_id}")
        log_event(
            "square_webhook_duplicate",
            provider="square",
            webhook_type=event_type,
            event_id=event_id,
        )
        log_metric(
            "square_webhook_duplicate",
            provider="square",
            webhook_type=event_type,
        )
        # Return 200 OK without reprocessing (SEC-1 acceptance criteria)
        return HttpResponse(status=200)

    logger.info(f"Received Square webhook: {event_id}")
    log_event(
        "square_webhook_received",
        provider="square",
        webhook_type=event_type,
        event_id=event_id,
    )

    # Process the event
    processing_error = None
    try:
        with track_duration(
            "square_webhook_process",
            provider="square",
            webhook_type=event_type,
        ):
            if event_type == "payment.created":
                handle_payment_created(event_data, webhook_event)
            elif event_type == "payment.updated":
                handle_payment_updated(event_data, webhook_event)
            elif event_type == "refund.created":
                handle_refund_created(event_data, webhook_event)
            elif event_type == "refund.updated":
                handle_refund_updated(event_data, webhook_event)
            elif event_type == "invoice.published":
                handle_invoice_published(event_data, webhook_event)
            elif event_type == "invoice.payment_made":
                handle_invoice_payment_made(event_data, webhook_event)
            elif event_type == "invoice.canceled":
                handle_invoice_canceled(event_data, webhook_event)
            else:
                logger.info(f"Unhandled Square event type: {event_type}")
                log_event(
                    "square_webhook_unhandled",
                    provider="square",
                    webhook_type=event_type,
                )
        
        # Mark webhook event as successfully processed
        webhook_event.processed_successfully = True
        webhook_event.save(update_fields=["processed_successfully"])
        
    except Exception as e:
        processing_error = str(e)
        logger.error(f"Error processing Square webhook: {e}", exc_info=True)
        log_event(
            "square_webhook_failed",
            provider="square",
            webhook_type=event_type,
            error_class=e.__class__.__name__,
        )
        
        # Mark webhook event as failed
        webhook_event.processed_successfully = False
        webhook_event.error_message = processing_error
        webhook_event.save(update_fields=["processed_successfully", "error_message"])
        
        return HttpResponse(status=500)

    log_metric(
        "square_webhook_processed",
        provider="square",
        webhook_type=event_type,
        status="success",
    )
    return HttpResponse(status=200)


def verify_square_signature(payload: bytes, signature: str, webhook_url: str) -> bool:
    """
    Verify Square webhook signature.

    Args:
        payload: Request body
        signature: X-Square-Signature header value
        webhook_url: Webhook notification URL

    Returns:
        bool: True if signature is valid
    """
    if not signature or not settings.SQUARE_WEBHOOK_SIGNATURE_KEY:
        return False

    # Square signature verification
    # Concatenate webhook_url + request body
    string_to_sign = webhook_url + payload.decode("utf-8")

    # HMAC-SHA256 with signature key
    expected_signature = hmac.new(
        settings.SQUARE_WEBHOOK_SIGNATURE_KEY.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def handle_payment_created(payment, webhook_event=None):
    """
    Handle payment.created event.

    Log payment initiation for tracking.
    """
    logger.info("Square payment created")
    log_event(
        "square_payment_created",
        provider="square",
        webhook_type="payment.created",
        payment_id=payment.get("id"),
    )


def handle_payment_updated(payment, webhook_event=None):
    """
    Handle payment.updated event.

    Update invoice status based on payment status.
    """
    payment_id = payment.get("id")
    status = payment.get("status")
    reference_id = payment.get("reference_id")  # This should be invoice_id

    logger.info(f"Square payment updated: {payment_id} - {status}")
    log_event(
        "square_payment_updated",
        provider="square",
        webhook_type="payment.updated",
        payment_id=payment_id,
        payment_status=status,
    )

    if not reference_id:
        logger.warning("Payment missing reference_id (invoice_id)")
        return

    try:
        invoice = Invoice.objects.get(id=int(reference_id))

        if status == "COMPLETED":
            # Payment successful
            amount_paid = Decimal(payment["amount_money"]["amount"]) / 100

            invoice.amount_paid += amount_paid

            if invoice.amount_paid >= invoice.total_amount:
                invoice.status = "paid"
                invoice.paid_date = timezone.now().date()
            else:
                invoice.status = "partial"

            invoice.autopay_status = "succeeded"
            invoice.autopay_next_charge_at = None
            invoice.save()

            # Link webhook event to invoice (SEC-1)
            if webhook_event:
                webhook_event.invoice = invoice
                webhook_event.firm = invoice.firm
                webhook_event.save(update_fields=["invoice", "firm"])

            logger.info(f"Invoice {invoice.id} updated from Square payment")
            log_metric(
                "square_payment_completed",
                provider="square",
                webhook_type="payment.updated",
                status="success",
            )

        elif status == "FAILED":
            # Payment failed
            handle_payment_failure(
                invoice, failure_reason="processor_failure", failure_code=payment.get("processing", [{}])[0].get("code")
            )
            invoice.autopay_status = "failed"
            from datetime import timedelta

            invoice.autopay_next_charge_at = timezone.now() + timedelta(days=3)
            invoice.save()

            logger.warning(f"Invoice {invoice.id} payment failed")
            log_event(
                "square_payment_failed",
                provider="square",
                webhook_type="payment.updated",
                payment_id=payment_id,
            )

        elif status == "CANCELED":
            # Payment canceled
            invoice.autopay_status = "cancelled"
            invoice.save()

            logger.info(f"Invoice {invoice.id} payment canceled")
            log_event(
                "square_payment_canceled",
                provider="square",
                webhook_type="payment.updated",
                payment_id=payment_id,
            )

    except Invoice.DoesNotExist:
        logger.error(f"Invoice not found for Square payment: {reference_id}")
        log_event(
            "square_payment_invoice_missing",
            provider="square",
            webhook_type="payment.updated",
            payment_id=payment_id,
        )
    except Exception as e:
        logger.error(f"Error updating invoice from Square payment: {str(e)}")
        log_event(
            "square_payment_update_failed",
            provider="square",
            webhook_type="payment.updated",
            payment_id=payment_id,
            error_class=e.__class__.__name__,
        )


def handle_refund_created(refund, webhook_event=None):
    """
    Handle refund.created event.

    Update invoice to reflect refund initiation.
    """
    logger.info("Square refund created")
    log_event(
        "square_refund_created",
        provider="square",
        webhook_type="refund.created",
        refund_id=refund.get("id"),
    )


def handle_refund_updated(refund, webhook_event=None):
    """
    Handle refund.updated event.

    Update invoice to reflect completed refund.
    """
    refund_id = refund.get("id")
    status = refund.get("status")
    payment_id = refund.get("payment_id")

    logger.info(f"Square refund updated: {refund_id} - {status}")
    log_event(
        "square_refund_updated",
        provider="square",
        webhook_type="refund.updated",
        refund_id=refund_id,
        refund_status=status,
    )

    if status == "COMPLETED":
        # Find invoice by payment_id (stored in stripe_payment_intent_id)
        try:
            invoice = Invoice.objects.filter(stripe_payment_intent_id=payment_id).first()

            if invoice:
                refund_amount = Decimal(refund["amount_money"]["amount"]) / 100
                invoice.amount_paid -= refund_amount

                if invoice.amount_paid <= 0:
                    invoice.status = "refunded"
                    invoice.amount_paid = Decimal("0.00")
                elif invoice.amount_paid < invoice.total_amount:
                    invoice.status = "partial"

                invoice.save()

                logger.info(f"Invoice {invoice.id} refunded")
                log_metric(
                    "square_refund_completed",
                    provider="square",
                    webhook_type="refund.updated",
                    status="success",
                )
            else:
                logger.warning(f"Invoice not found for Square refund: {payment_id}")

        except Exception as e:
            logger.error(f"Error processing Square refund: {str(e)}")
            log_event(
                "square_refund_update_failed",
                provider="square",
                webhook_type="refund.updated",
                refund_id=refund_id,
                error_class=e.__class__.__name__,
            )


def handle_invoice_published(square_invoice, webhook_event=None):
    """
    Handle invoice.published event.

    Update our invoice status to 'sent'.
    """
    invoice_id = square_invoice.get("id")

    logger.info(f"Square invoice published: {invoice_id}")
    log_event(
        "square_invoice_published",
        provider="square",
        webhook_type="invoice.published",
        square_invoice_id=invoice_id,
    )

    try:
        # Find our invoice by Square invoice ID
        invoice = Invoice.objects.filter(stripe_invoice_id=invoice_id).first()

        if invoice and invoice.status == "draft":
            invoice.status = "sent"
            invoice.save()

            logger.info(f"Invoice {invoice.id} marked as sent")

    except Exception as e:
        logger.error(f"Error updating invoice from Square publish event: {str(e)}")


def handle_invoice_payment_made(square_invoice, webhook_event=None):
    """
    Handle invoice.payment_made event.

    Update invoice to paid status.
    """
    invoice_id = square_invoice.get("id")

    logger.info(f"Square invoice payment made: {invoice_id}")
    log_event(
        "square_invoice_payment_made",
        provider="square",
        webhook_type="invoice.payment_made",
        square_invoice_id=invoice_id,
    )

    try:
        # Find our invoice by Square invoice ID
        invoice = Invoice.objects.filter(stripe_invoice_id=invoice_id).first()

        if invoice:
            invoice.status = "paid"
            invoice.paid_date = timezone.now().date()
            invoice.amount_paid = invoice.total_amount
            invoice.save()

            logger.info(f"Invoice {invoice.id} marked as paid")
            log_metric(
                "square_invoice_payment_made",
                provider="square",
                webhook_type="invoice.payment_made",
                status="success",
            )

    except Exception as e:
        logger.error(f"Error updating invoice from Square payment: {str(e)}")
        log_event(
            "square_invoice_payment_failed",
            provider="square",
            webhook_type="invoice.payment_made",
            square_invoice_id=invoice_id,
            error_class=e.__class__.__name__,
        )


def handle_invoice_canceled(square_invoice, webhook_event=None):
    """
    Handle invoice.canceled event.

    Update invoice to canceled status.
    """
    invoice_id = square_invoice.get("id")

    logger.info(f"Square invoice canceled: {invoice_id}")
    log_event(
        "square_invoice_canceled",
        provider="square",
        webhook_type="invoice.canceled",
        square_invoice_id=invoice_id,
    )

    try:
        # Find our invoice by Square invoice ID
        invoice = Invoice.objects.filter(stripe_invoice_id=invoice_id).first()

        if invoice:
            invoice.status = "cancelled"
            invoice.save()

            logger.info(f"Invoice {invoice.id} marked as canceled")

    except Exception as e:
        logger.error(f"Error updating invoice from Square cancellation: {str(e)}")
