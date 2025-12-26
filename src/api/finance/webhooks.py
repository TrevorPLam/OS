"""
Stripe Webhook Handler for payment events.

Handles asynchronous payment confirmations and updates.
"""
import stripe
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from decimal import Decimal
from modules.finance.models import Invoice
from modules.finance import billing
from django.utils import timezone
import json

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
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Stripe webhook invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Stripe webhook signature verification failed: {e}")
        return HttpResponse(status=400)

    # Handle the event
    event_type = event['type']
    event_data = event['data']['object']

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == 'payment_intent.succeeded':
            handle_payment_intent_succeeded(event_data)
        elif event_type == 'payment_intent.payment_failed':
            handle_payment_intent_failed(event_data)
        elif event_type == 'invoice.payment_succeeded':
            handle_invoice_payment_succeeded(event_data)
        elif event_type == 'invoice.payment_failed':
            handle_invoice_payment_failed(event_data)
        elif event_type == 'charge.refunded':
            handle_charge_refunded(event_data)
        elif event_type == 'charge.dispute.created':
            handle_charge_dispute_created(event_data)
        elif event_type in ['charge.dispute.closed', 'charge.dispute.funds_reinstated', 'charge.dispute.funds_withdrawn']:
            handle_charge_dispute_closed(event_data)
        else:
            logger.info(f"Unhandled Stripe event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}", exc_info=True)
        return HttpResponse(status=500)

    return HttpResponse(status=200)


def handle_payment_intent_succeeded(payment_intent):
    """
    Handle successful payment intent.
    Update invoice status to paid.
    """
    metadata = payment_intent.get('metadata', {})
    invoice_id = metadata.get('invoice_id')

    if not invoice_id:
        logger.warning(f"Payment intent {payment_intent['id']} has no invoice_id in metadata")
        return

    try:
        invoice = Invoice.objects.get(id=invoice_id)

        # Calculate amount received (in cents, convert to dollars)
        amount_received = payment_intent['amount_received'] / 100

        # Update invoice
        invoice.amount_paid += amount_received

        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = 'paid'
            invoice.paid_date = timezone.now().date()
        else:
            invoice.status = 'partial'

        invoice.save()

        logger.info(f"Invoice {invoice.invoice_number} updated from payment intent {payment_intent['id']}")

    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} not found for payment intent {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error updating invoice {invoice_id}: {e}", exc_info=True)


def handle_payment_intent_failed(payment_intent):
    """
    Handle failed payment intent.
    Log the failure for manual review.
    """
    metadata = payment_intent.get('metadata', {})
    invoice_id = metadata.get('invoice_id')

    failure_message = payment_intent.get('last_payment_error', {}).get('message')
    failure_code = payment_intent.get('last_payment_error', {}).get('code')
    amount_attempted = Decimal(str(payment_intent.get('amount', 0))) / 100

    logger.warning(
        f"Payment failed for invoice {invoice_id}, "
        f"payment_intent: {payment_intent['id']}, "
        f"failure_message: {failure_message}"
    )

    if invoice_id:
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            billing.handle_payment_failure(
                invoice,
                failure_reason=failure_message or 'unknown_error',
                failure_code=failure_code,
                amount_attempted=amount_attempted,
                stripe_payment_intent_id=payment_intent['id'],
                stripe_error_code=failure_code,
            )
        except Invoice.DoesNotExist:
            logger.error(f"Invoice {invoice_id} not found for failed payment intent {payment_intent['id']}")


def handle_invoice_payment_succeeded(stripe_invoice):
    """
    Handle successful Stripe invoice payment.
    """
    metadata = stripe_invoice.get('metadata', {})
    invoice_id = metadata.get('invoice_id')

    if not invoice_id:
        logger.warning(f"Stripe invoice {stripe_invoice['id']} has no invoice_id in metadata")
        return

    try:
        invoice = Invoice.objects.get(id=invoice_id)
        amount_paid = stripe_invoice['amount_paid'] / 100

        invoice.amount_paid += amount_paid
        invoice.status = 'paid'
        invoice.paid_date = timezone.now().date()
        invoice.save()

        logger.info(f"Invoice {invoice.invoice_number} marked as paid from Stripe invoice {stripe_invoice['id']}")

    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} not found for Stripe invoice {stripe_invoice['id']}")


def handle_invoice_payment_failed(stripe_invoice):
    """
    Handle failed Stripe invoice payment.
    """
    metadata = stripe_invoice.get('metadata', {})
    invoice_id = metadata.get('invoice_id')

    logger.warning(
        f"Invoice payment failed for invoice {invoice_id}, "
        f"stripe_invoice: {stripe_invoice['id']}"
    )


def handle_charge_refunded(charge):
    """
    Handle refunded charge.
    Update invoice to reflect refund.
    """
    metadata = charge.get('metadata', {})
    invoice_id = metadata.get('invoice_id')

    if not invoice_id:
        return

    try:
        invoice = Invoice.objects.get(id=invoice_id)
        refund_amount = charge['amount_refunded'] / 100

        invoice.amount_paid -= refund_amount

        if invoice.amount_paid <= 0:
            invoice.status = 'cancelled'
            invoice.amount_paid = 0
        elif invoice.amount_paid < invoice.total_amount:
            invoice.status = 'partial'

        invoice.save()

        logger.info(f"Invoice {invoice.invoice_number} refunded ${refund_amount}")

    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} not found for refund")


def handle_charge_dispute_created(dispute):
    """Persist dispute metadata for downstream remediation workflows."""
    try:
        billing.handle_dispute_opened(
            {
                'id': dispute['id'],
                'invoice_id': dispute.get('invoice') or dispute.get('invoice_id'),
                'charge_id': dispute.get('charge'),
                'reason': dispute.get('reason', 'general'),
                'amount': Decimal(str(dispute.get('amount', 0))) / 100,
                'respond_by': dispute.get('evidence_details', {}).get('due_by'),
            }
        )
    except Exception:
        logger.exception("Failed to record payment dispute metadata")


def handle_charge_dispute_closed(dispute):
    """Close dispute and record chargeback metadata."""
    try:
        billing.handle_dispute_closed(
            {
                'id': dispute['id'],
                'status': dispute.get('status', ''),
                'reason': dispute.get('reason', ''),
                'amount': Decimal(str(dispute.get('amount', 0))) / 100,
                'charge': dispute.get('charge'),
                'invoice_id': dispute.get('invoice') or dispute.get('invoice_id'),
            }
        )
    except Exception:
        logger.exception("Failed to close dispute/chargeback")
