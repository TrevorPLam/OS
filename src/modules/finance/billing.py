"""
Billing workflows for package invoicing, autopay, and payment recovery.

Implements Tier 4 architecture from docs/tier4/BILLING_INVARIANTS_AND_ARCHITECTURE.md
and PAYMENT_FAILURE_HANDLING.md.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from modules.clients.models import ClientEngagement
import uuid

from modules.finance.models import (
    Chargeback,
    Invoice,
    LedgerEntry,
    PaymentDispute,
    PaymentFailure,
)
from modules.finance.services import StripeService
from modules.firm.audit import audit


def _month_start_for(day: date) -> date:
    return day.replace(day=1)


def _month_end_for(day: date) -> date:
    next_month = (day.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def _quarter_start_for(day: date) -> date:
    quarter = (day.month - 1) // 3
    month = quarter * 3 + 1
    return day.replace(month=month, day=1)


def _quarter_end_for(day: date) -> date:
    start = _quarter_start_for(day)
    end_month = start.month + 2
    end_candidate = start.replace(month=end_month)
    return _month_end_for(end_candidate)


def _period_bounds(engagement: ClientEngagement, reference_date: Optional[date] = None):
    reference_date = reference_date or timezone.now().date()
    schedule = (engagement.package_fee_schedule or 'monthly').lower()

    if schedule == 'quarterly':
        start = _quarter_start_for(reference_date)
        end = _quarter_end_for(reference_date)
    elif schedule in ['annual', 'yearly']:
        start = reference_date.replace(month=1, day=1)
        end = reference_date.replace(month=12, day=31)
    elif schedule in ['one-time', 'one_time', 'once']:
        start = engagement.start_date
        end = engagement.end_date
    else:  # default monthly
        start = _month_start_for(reference_date)
        end = _month_end_for(reference_date)

    start = max(start, engagement.start_date)
    end = min(end, engagement.end_date)
    return start, end


def should_generate_package_invoice(engagement: ClientEngagement, reference_date: Optional[date] = None) -> bool:
    """Determine if a package invoice should be generated for the period."""
    if engagement.status != 'current':
        return False

    if engagement.pricing_mode not in ['package', 'mixed']:
        return False

    if not engagement.package_fee:
        return False

    period_start, _ = _period_bounds(engagement, reference_date)

    if engagement.end_date < period_start:
        return False

    return not Invoice.objects.filter(engagement=engagement, period_start=period_start).exists()


def create_package_invoice(engagement: ClientEngagement, issue_date: Optional[date] = None, reference_date: Optional[date] = None) -> Invoice:
    """Create a package-fee invoice for an engagement with duplicate prevention."""
    issue_date = issue_date or timezone.now().date()
    period_start, period_end = _period_bounds(engagement, reference_date)

    with transaction.atomic():
        invoice, created = Invoice.objects.select_for_update().get_or_create(
            engagement=engagement,
            period_start=period_start,
            defaults={
                'firm': engagement.firm,
                'client': engagement.client,
                'status': 'sent',
                'subtotal': engagement.package_fee,
                'tax_amount': Decimal('0.00'),
                'total_amount': engagement.package_fee,
                'issue_date': issue_date,
                'due_date': issue_date + timedelta(days=30),
                'line_items': [
                    {
                        'description': f'Package Fee - {engagement.contract.title}',
                        'quantity': 1,
                        'rate': float(engagement.package_fee),
                        'amount': float(engagement.package_fee),
                        'type': 'package_fee',
                    }
                ],
                'invoice_number': f'PKG-{engagement.id}-{period_start.isoformat()}',
                'is_auto_generated': True,
                'period_end': period_end,
                'autopay_opt_in': engagement.client.autopay_enabled,
                'autopay_payment_method_id': engagement.client.autopay_payment_method_id,
            },
        )

    if created:
        audit.log_billing_event(
            firm=engagement.firm,
            action='package_invoice_auto_generated',
            actor=None,
            metadata={
                'invoice_id': invoice.id,
                'engagement_id': engagement.id,
                'amount': float(engagement.package_fee),
                'period_start': str(period_start),
                'period_end': str(period_end),
            },
        )

    return invoice


def generate_package_invoices(reference_date: Optional[date] = None):
    """Generate package invoices for all active engagements."""
    engagements = ClientEngagement.objects.filter(
        status='current', pricing_mode__in=['package', 'mixed']
    )

    created_invoices = []
    for engagement in engagements:
        if should_generate_package_invoice(engagement, reference_date):
            created_invoices.append(
                create_package_invoice(engagement, reference_date=reference_date)
            )
    return created_invoices


def execute_autopay_for_invoice(invoice: Invoice):
    """
    Autopay execution that pays invoices on issuance without creating new ones.

    If autopay is enabled for the client and a payment method is present, mark the
    invoice as paid. Failures route through payment failure handling to preserve
    retry metadata.
    """

    if not invoice.client.autopay_enabled:
        return invoice

    if not invoice.client.autopay_payment_method_id:
        return handle_payment_failure(
            invoice,
            failure_reason='Missing autopay payment method',
            failure_code='payment_method_missing',
        )

    invoice.amount_paid = invoice.total_amount
    invoice.status = 'paid'
    invoice.paid_date = timezone.now().date()
    invoice.save(update_fields=['amount_paid', 'status', 'paid_date'])

    audit.log_billing_event(
        firm=invoice.firm,
        action='invoice_autopaid',
        actor=None,
        metadata={
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'amount': float(invoice.total_amount),
        },
    )

    return invoice


def schedule_autopay(invoice: Invoice, reference_time: Optional[timezone.datetime] = None):
    """Mark an invoice for autopay execution based on cadence and due date."""

    if not invoice.client.autopay_enabled:
        invoice.autopay_status = 'cancelled'
        invoice.autopay_opt_in = False
        invoice.autopay_next_charge_at = None
        invoice.save(update_fields=['autopay_status', 'autopay_opt_in', 'autopay_next_charge_at'])
        return invoice

    invoice.autopay_opt_in = True
    invoice.autopay_payment_method_id = invoice.autopay_payment_method_id or invoice.client.autopay_payment_method_id
    invoice.autopay_status = 'scheduled'
    reference_time = reference_time or timezone.now()

    if invoice.autopay_cadence == 'monthly':
        scheduled_for = invoice.due_date.replace(day=1)
    elif invoice.autopay_cadence == 'quarterly':
        scheduled_for = invoice.due_date.replace(month=((invoice.due_date.month - 1) // 3) * 3 + 1, day=1)
    else:
        scheduled_for = invoice.due_date

    invoice.autopay_next_charge_at = timezone.make_aware(timezone.datetime.combine(scheduled_for, timezone.datetime.min.time()))
    invoice.save(update_fields=['autopay_status', 'autopay_opt_in', 'autopay_payment_method_id', 'autopay_next_charge_at'])
    return invoice


def _charge_invoice(invoice: Invoice, payment_service=StripeService):
    """Attempt to charge an invoice using the configured payment method."""

    payment_method_id = invoice.autopay_payment_method_id or invoice.client.autopay_payment_method_id
    if not payment_method_id:
        result = handle_payment_failure(
            invoice,
            failure_reason='Missing autopay payment method',
            failure_code='payment_method_missing',
        )
        invoice.autopay_status = 'failed'
        invoice.autopay_next_charge_at = timezone.now() + timedelta(days=3)
        invoice.save(update_fields=['autopay_status', 'autopay_next_charge_at'])
        return result

    invoice.autopay_status = 'processing'
    invoice.autopay_last_attempt_at = timezone.now()
    invoice.save(update_fields=['autopay_status', 'autopay_last_attempt_at'])

    try:
        intent = payment_service.create_payment_intent(
            amount=invoice.total_amount,
            currency=invoice.currency.lower(),
            customer_id=None,
            metadata={'invoice_id': invoice.id},
            payment_method=payment_method_id,
        )
    except Exception as exc:  # pragma: no cover - safety net
        result = handle_payment_failure(invoice, failure_reason=str(exc), failure_code='processor_error')
        invoice.autopay_status = 'failed'
        invoice.autopay_next_charge_at = timezone.now() + timedelta(days=3)
        invoice.save(update_fields=['autopay_status', 'autopay_next_charge_at'])
        return result

    invoice.stripe_payment_intent_id = getattr(intent, 'id', '') or intent.get('id', '') if hasattr(intent, 'get') else ''
    invoice.amount_paid = invoice.total_amount
    invoice.status = 'paid'
    invoice.paid_date = timezone.now().date()
    invoice.autopay_status = 'succeeded'
    invoice.autopay_next_charge_at = None
    invoice.save(
        update_fields=[
            'stripe_payment_intent_id',
            'amount_paid',
            'status',
            'paid_date',
            'autopay_status',
            'autopay_next_charge_at',
        ]
    )
    return invoice


def process_recurring_invoices(reference_time: Optional[timezone.datetime] = None, payment_service=StripeService):
    """Find invoices marked for autopay and execute charges."""

    now = reference_time or timezone.now()
    due_invoices = Invoice.objects.filter(
        autopay_opt_in=True,
        status__in=['sent', 'partial', 'overdue'],
    ).select_related('client')

    processed = []
    for invoice in due_invoices:
        if not invoice.client.autopay_enabled:
            invoice.autopay_status = 'cancelled'
            invoice.autopay_next_charge_at = None
            invoice.autopay_opt_in = False
            invoice.save(update_fields=['autopay_status', 'autopay_next_charge_at', 'autopay_opt_in'])
            continue

        if invoice.autopay_next_charge_at and invoice.autopay_next_charge_at > now:
            continue

        try:
            processed.append(_charge_invoice(invoice, payment_service=payment_service))
        except Exception as exc:  # pragma: no cover - guardrail
            handle_payment_failure(invoice, failure_reason=str(exc), failure_code='processor_error')
            invoice.autopay_status = 'failed'
            invoice.autopay_next_charge_at = now + timedelta(days=3)
            invoice.save(update_fields=['autopay_status', 'autopay_next_charge_at'])

    return processed


def _notify_client_portal(invoice: Invoice, message: str):
    """Append a client-facing message to invoice notes for portal visibility."""
    timestamped = f"[{timezone.now().isoformat()}] {message}"
    invoice.notes = f"{invoice.notes}\n{timestamped}" if invoice.notes else timestamped
    invoice.save(update_fields=['notes'])


def handle_payment_failure(
    invoice: Invoice,
    failure_reason: str,
    failure_code: Optional[str] = None,
    *,
    amount_attempted: Optional[Decimal] = None,
    stripe_payment_intent_id: Optional[str] = None,
    stripe_error_code: Optional[str] = None,
):
    """Record payment failure metadata, remediation, and retry logic."""
    now = timezone.now()
    invoice.status = 'failed'
    invoice.payment_failed_at = now
    invoice.payment_failure_reason = failure_reason
    invoice.payment_failure_code = failure_code or ''
    invoice.payment_retry_count += 1
    invoice.last_payment_retry_at = now
    invoice.stripe_payment_intent_id = stripe_payment_intent_id or invoice.stripe_payment_intent_id
    invoice.save(
        update_fields=[
            'status',
            'payment_failed_at',
            'payment_failure_reason',
            'payment_failure_code',
            'payment_retry_count',
            'last_payment_retry_at',
            'stripe_payment_intent_id',
        ]
    )

    failure = PaymentFailure.objects.create(
        firm=invoice.firm,
        invoice=invoice,
        client=invoice.client,
        amount_attempted=invoice.total_amount if amount_attempted is None else amount_attempted,
        currency=invoice.currency,
        failure_code=failure_code if failure_code in [choice[0] for choice in PaymentFailure.FAILURE_CODE_CHOICES] else 'other',
        failure_message=failure_reason,
        stripe_payment_intent_id=stripe_payment_intent_id or invoice.stripe_payment_intent_id,
        stripe_error_code=stripe_error_code or '',
        retry_count=invoice.payment_retry_count,
    )

    audit.log_billing_event(
        firm=invoice.firm,
        action='payment_failed',
        actor=None,
        metadata={
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'amount': float(invoice.total_amount),
            'failure_reason': failure_reason,
            'failure_code': failure_code,
            'retry_count': invoice.payment_retry_count,
            'stripe_payment_intent_id': invoice.stripe_payment_intent_id,
            'payment_failure_id': failure.id,
        },
        severity='WARNING',
    )

    retry_at = schedule_payment_retry(invoice)
    failure.next_retry_at = retry_at
    failure.customer_notified = True
    failure.notified_at = now
    failure.save(update_fields=['next_retry_at', 'customer_notified', 'notified_at'])

    _notify_client_portal(
        invoice,
        "Payment attempt failed. We will retry automatically and will reach out if action is needed.",
    )

    if invoice.payment_retry_count >= 2:
        invoice.client.status = 'inactive'
        invoice.client.save(update_fields=['status'])

    return invoice


def schedule_payment_retry(invoice: Invoice):
    """Mark retry metadata and hand off to async scheduler (stub)."""
    retry_delays = {
        1: timedelta(days=3),
        2: timedelta(days=7),
        3: timedelta(days=14),
    }

    retry_at = timezone.now() + retry_delays.get(invoice.payment_retry_count, timedelta(days=7))

    audit.log_billing_event(
        firm=invoice.firm,
        action='payment_retry_scheduled',
        metadata={
            'invoice_id': invoice.id,
            'retry_count': invoice.payment_retry_count,
            'retry_at': str(retry_at),
        },
    )

    if invoice.payment_retry_count >= 3:
        invoice.status = 'overdue'
        invoice.save(update_fields=['status'])
        audit.log_billing_event(
            firm=invoice.firm,
            action='payment_retry_exhausted',
            metadata={
                'invoice_id': invoice.id,
                'total_retries': invoice.payment_retry_count,
            },
            severity='WARNING',
        )

    return retry_at


def handle_dispute_opened(stripe_dispute_data: dict) -> PaymentDispute:
    """Create a dispute record and flag invoice as disputed."""
    invoice_ref = stripe_dispute_data.get('invoice_id') or stripe_dispute_data.get('invoice')
    invoice = Invoice.objects.get(stripe_invoice_id=invoice_ref)

    reason = stripe_dispute_data.get('reason', 'general')
    valid_reasons = [choice[0] for choice in PaymentDispute.DISPUTE_REASON_CHOICES]
    if reason not in valid_reasons:
        reason = 'general'

    dispute = PaymentDispute.objects.create(
        firm=invoice.firm,
        invoice=invoice,
        status='opened',
        reason=reason,
        amount=Decimal(str(stripe_dispute_data['amount'])),
        stripe_dispute_id=stripe_dispute_data['id'],
        stripe_charge_id=stripe_dispute_data.get('charge_id', ''),
        opened_at=timezone.now(),
        respond_by=stripe_dispute_data.get('respond_by'),
    )

    invoice.status = 'disputed'
    invoice.save(update_fields=['status'])

    _notify_client_portal(
        invoice,
        "A payment dispute was opened by your bank. Our team is reviewing and will share updates here.",
    )

    audit.log_billing_event(
        firm=invoice.firm,
        action='payment_disputed',
        actor=None,
        metadata={
            'dispute_id': dispute.id,
            'invoice_id': invoice.id,
            'amount': float(dispute.amount),
            'reason': dispute.reason,
            'stripe_dispute_id': dispute.stripe_dispute_id,
        },
        severity='CRITICAL',
    )

    return dispute


def handle_dispute_closed(stripe_dispute_data: dict) -> PaymentDispute:
    """Close dispute and update invoice status accordingly."""
    dispute = PaymentDispute.objects.get(stripe_dispute_id=stripe_dispute_data['id'])
    if dispute.status == 'closed':
        return dispute
    reason = stripe_dispute_data.get('reason', 'general')
    valid_reasons = [choice[0] for choice in PaymentDispute.DISPUTE_REASON_CHOICES]
    if reason not in valid_reasons:
        reason = 'general'

    dispute.status = 'closed'
    dispute.resolution = stripe_dispute_data.get('status', '')
    dispute.resolution_reason = reason
    dispute.closed_at = timezone.now()
    dispute.save(update_fields=['status', 'resolution', 'resolution_reason', 'closed_at'])

    if dispute.resolution == 'won':
        dispute.invoice.status = 'paid'
        dispute.invoice.save(update_fields=['status'])
        _notify_client_portal(
            dispute.invoice,
            "Dispute resolved in our favor. Service will continue uninterrupted.",
        )
    else:
        _record_chargeback(
            dispute.invoice,
            stripe_dispute_data,
            reason=reason,
            amount=dispute.amount,
            initiated_at=dispute.opened_at,
        )
        _reverse_ledger_for_chargeback(dispute.invoice, dispute.amount, dispute.resolution or 'lost')
        dispute.invoice.status = 'charged_back'
        dispute.invoice.amount_paid = max(
            Decimal('0.00'), dispute.invoice.amount_paid - dispute.amount
        )
        dispute.invoice.save(update_fields=['status', 'amount_paid'])
        _notify_client_portal(
            dispute.invoice,
            "We were unable to defend a dispute. Services are paused while we rebill the outstanding balance.",
        )
        dispute.invoice.client.status = 'inactive'
        dispute.invoice.client.save(update_fields=['status'])

    audit.log_billing_event(
        firm=dispute.firm,
        action=f"dispute_{dispute.resolution or 'closed'}",
        actor=None,
        metadata={
            'dispute_id': dispute.id,
            'invoice_id': dispute.invoice.id,
            'resolution': dispute.resolution,
            'amount': float(dispute.amount),
        },
        severity='CRITICAL',
    )

    return dispute


def _reverse_ledger_for_chargeback(invoice: Invoice, amount: Decimal, reason: str):
    """Create double-entry reversal to reflect a chargeback."""
    group_id = uuid.uuid4().hex
    description = f"Chargeback reversal ({reason}) for invoice {invoice.invoice_number}"
    LedgerEntry.objects.create(
        firm=invoice.firm,
        entry_type='debit',
        account='accounts_receivable',
        amount=amount,
        transaction_date=timezone.now().date(),
        description=description,
        invoice=invoice,
        transaction_group_id=group_id,
    )
    LedgerEntry.objects.create(
        firm=invoice.firm,
        entry_type='credit',
        account='cash',
        amount=amount,
        transaction_date=timezone.now().date(),
        description=description,
        invoice=invoice,
        transaction_group_id=group_id,
    )


def _record_chargeback(invoice: Invoice, stripe_dispute_data: dict) -> Chargeback:
    """Persist chargeback metadata from a closed dispute."""
    chargeback, _ = Chargeback.objects.get_or_create(
        amount = stripe_dispute_data.get('amount')
        chargeback, _ = Chargeback.objects.get_or_create(
            stripe_chargeback_id=stripe_dispute_data.get('id'),
            defaults={
                'firm': invoice.firm,
                'invoice': invoice,
                'client': invoice.client,
                'amount': Decimal(str(amount)) if amount is not None else invoice.total_amount,
            'currency': invoice.currency,
            'status': 'lost',
            'reason': stripe_dispute_data.get('reason', 'general'),
            'stripe_charge_id': stripe_dispute_data.get('charge', ''),
            'initiated_at': timezone.now(),
            'respond_by': None,
        },
    )
    chargeback.resolved_at = timezone.now()
    chargeback.funds_reversed = True
    chargeback.save(update_fields=['resolved_at', 'funds_reversed'])
    return chargeback
