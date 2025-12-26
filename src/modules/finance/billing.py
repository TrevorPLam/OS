"""
Billing workflows for package invoicing, autopay, and payment recovery.

Implements Tier 4 architecture from docs/tier4/BILLING_INVARIANTS_AND_ARCHITECTURE.md
and PAYMENT_FAILURE_HANDLING.md.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from modules.clients.models import ClientEngagement
from modules.finance.models import Invoice, PaymentDispute
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


def get_package_billing_period(
    engagement: ClientEngagement, reference_date: Optional[date] = None
):
    """Public helper to calculate the billing window for a package engagement."""

    return _period_bounds(engagement, reference_date)


def should_generate_package_invoice(
    engagement: ClientEngagement, reference_date: Optional[date] = None
) -> bool:
    """Determine if a package invoice should be generated for the period."""
    if engagement.status != 'current':
        return False

    if engagement.pricing_mode not in ['package', 'mixed']:
        return False

    if not engagement.package_fee:
        return False

    period_start, _ = get_package_billing_period(engagement, reference_date)

    if engagement.end_date < period_start:
        return False

    return not Invoice.objects.filter(
        engagement=engagement, period_start=period_start, firm=engagement.firm
    ).exists()


def create_package_invoice(engagement: ClientEngagement, issue_date: Optional[date] = None, reference_date: Optional[date] = None) -> Invoice:
    """Create a package-fee invoice for an engagement with duplicate prevention."""
    issue_date = issue_date or timezone.now().date()
    period_start, period_end = get_package_billing_period(engagement, reference_date)

    if engagement.client.firm_id != engagement.firm_id:
        raise ValidationError(
            "Engagement firm must match client firm when generating package invoices."
        )

    with transaction.atomic():
        invoice, created = Invoice.objects.select_for_update().get_or_create(
            engagement=engagement,
            period_start=period_start,
            defaults={
                'firm': engagement.client.firm,
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


def generate_package_invoices(reference_date: Optional[date] = None, firm=None):
    """Generate package invoices for all active engagements.

    Args:
        reference_date: Optional date used to determine the billing window.
        firm: Optional firm to scope invoice generation (tenant isolation).
    """
    engagements = ClientEngagement.objects.filter(
        status='current', pricing_mode__in=['package', 'mixed'], package_fee__isnull=False
    ).select_related('client', 'firm')

    if firm:
        engagements = engagements.filter(firm=firm)

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


def handle_payment_failure(invoice: Invoice, failure_reason: str, failure_code: Optional[str] = None):
    """Record payment failure metadata and schedule retry logic."""
    now = timezone.now()
    invoice.status = 'failed'
    invoice.payment_failed_at = now
    invoice.payment_failure_reason = failure_reason
    invoice.payment_failure_code = failure_code or ''
    invoice.payment_retry_count += 1
    invoice.last_payment_retry_at = now
    invoice.save(
        update_fields=[
            'status',
            'payment_failed_at',
            'payment_failure_reason',
            'payment_failure_code',
            'payment_retry_count',
            'last_payment_retry_at',
        ]
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
        },
        severity='WARNING',
    )

    schedule_payment_retry(invoice)
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


def handle_dispute_opened(stripe_dispute_data: dict) -> PaymentDispute:
    """Create a dispute record and flag invoice as disputed."""
    invoice = Invoice.objects.get(stripe_invoice_id=stripe_dispute_data['invoice_id'])

    dispute = PaymentDispute.objects.create(
        firm=invoice.firm,
        invoice=invoice,
        status='opened',
        reason=stripe_dispute_data.get('reason', 'general'),
        amount=Decimal(str(stripe_dispute_data['amount'])),
        stripe_dispute_id=stripe_dispute_data['id'],
        stripe_charge_id=stripe_dispute_data.get('charge_id', ''),
        opened_at=timezone.now(),
        respond_by=stripe_dispute_data.get('respond_by'),
    )

    invoice.status = 'disputed'
    invoice.save(update_fields=['status'])

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

    dispute.status = 'closed'
    dispute.resolution = stripe_dispute_data.get('status', '')
    dispute.resolution_reason = stripe_dispute_data.get('reason', '')
    dispute.closed_at = timezone.now()
    dispute.save(update_fields=['status', 'resolution', 'resolution_reason', 'closed_at'])

    if dispute.resolution == 'won':
        dispute.invoice.status = 'paid'
    else:
        dispute.invoice.status = 'charged_back'
        dispute.invoice.amount_paid = max(
            Decimal('0.00'), dispute.invoice.amount_paid - dispute.amount
        )

    dispute.invoice.save(update_fields=['status', 'amount_paid'])

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
