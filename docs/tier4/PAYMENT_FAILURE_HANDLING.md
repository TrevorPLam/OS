# Tier 4: Payment Failure, Dispute, and Chargeback Handling

**Status**: 📋 DOCUMENTED (Implementation: Tier 4 Phase 2)
**Created**: 2025-12-25

## Overview

Payment failures, disputes, and chargebacks must be treated as first-class events in the billing system. This ensures:
- Financial operations are auditable
- Customer disputes are tracked explicitly
- Platform retains only metadata (not customer dispute details)
- Compliance with payment processor requirements

## Core Principles

1. **First-Class Events**: Payment failures are not silent - they create audit events
2. **Metadata-Only Retention**: Platform stores payment metadata, not customer financial details
3. **Processor as Source of Truth**: Stripe/payment processor retains customer payment details
4. **Explicit State Tracking**: Invoice status reflects payment state accurately

## Payment Lifecycle States

### Invoice States

```python
STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent to Client'),
    ('paid', 'Paid'),
    ('partial', 'Partially Paid'),
    ('overdue', 'Overdue'),
    ('cancelled', 'Cancelled'),
    ('failed', 'Payment Failed'),        # NEW: Tier 4
    ('disputed', 'Under Dispute'),       # NEW: Tier 4
    ('refunded', 'Refunded'),            # NEW: Tier 4
    ('charged_back', 'Charged Back'),    # NEW: Tier 4
]
```

## Payment Failure Tracking

### Model Enhancement

**File**: `src/modules/finance/models.py` (Invoice model)

```python
# Payment Failure Tracking (TIER 4)
payment_failed_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text="When payment attempt failed"
)

payment_failure_reason = models.CharField(
    max_length=255,
    blank=True,
    help_text="Reason for payment failure (from processor)"
)

payment_failure_code = models.CharField(
    max_length=50,
    blank=True,
    help_text="Processor error code (e.g., 'insufficient_funds')"
)

payment_retry_count = models.IntegerField(
    default=0,
    help_text="Number of payment retry attempts"
)

last_payment_retry_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text="When last payment retry was attempted"
)

# Stripe Payment Intent ID
stripe_payment_intent_id = models.CharField(
    max_length=255,
    blank=True,
    help_text="Stripe Payment Intent ID for tracking"
)
```

### Payment Failure Event

When a payment fails:

```python
from modules.firm.audit import audit
from modules.finance.models import Invoice

def handle_payment_failure(invoice, failure_reason, failure_code):
    """
    Handle payment failure for an invoice.

    Args:
        invoice: Invoice instance
        failure_reason: Human-readable failure reason
        failure_code: Processor error code
    """
    from django.utils import timezone

    # Update invoice
    invoice.status = 'failed'
    invoice.payment_failed_at = timezone.now()
    invoice.payment_failure_reason = failure_reason
    invoice.payment_failure_code = failure_code
    invoice.payment_retry_count += 1
    invoice.last_payment_retry_at = timezone.now()
    invoice.save()

    # Create audit event
    audit.log_billing_event(
        firm=invoice.firm,
        action='payment_failed',
        actor=None,  # System event
        metadata={
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'amount': float(invoice.total_amount),
            'failure_reason': failure_reason,
            'failure_code': failure_code,
            'retry_count': invoice.payment_retry_count,
            'stripe_payment_intent_id': invoice.stripe_payment_intent_id,
        },
        severity='WARNING'
    )

    # Notify customer (future: email/notification)
    # notify_customer_payment_failed(invoice)

    return invoice
```

### Common Failure Codes (Stripe)

| Code | Meaning | Action |
|------|---------|--------|
| `insufficient_funds` | Not enough money in account | Retry in 3-7 days |
| `card_declined` | Card issuer declined | Ask customer to update card |
| `expired_card` | Card has expired | Request new payment method |
| `invalid_account` | Bank account invalid | Request new payment method |
| `payment_method_not_available` | Payment method unavailable | Use different payment method |

## Dispute Tracking

### Model Enhancement

**File**: `src/modules/finance/models.py` (new model)

```python
class PaymentDispute(models.Model):
    """
    Tracks payment disputes and chargebacks.

    TIER 4: Disputes are first-class entities.
    Platform retains metadata only, not customer dispute details.
    """
    DISPUTE_STATUS_CHOICES = [
        ('opened', 'Opened'),
        ('under_review', 'Under Review'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('closed', 'Closed'),
    ]

    DISPUTE_REASON_CHOICES = [
        ('fraudulent', 'Fraudulent'),
        ('duplicate', 'Duplicate Charge'),
        ('product_not_received', 'Product/Service Not Received'),
        ('product_unacceptable', 'Product/Service Unacceptable'),
        ('credit_not_processed', 'Credit Not Processed'),
        ('general', 'General'),
    ]

    # Tenant Context
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='payment_disputes',
        help_text="Firm this dispute belongs to"
    )

    # Linked Invoice
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.CASCADE,
        related_name='disputes',
        help_text="Invoice being disputed"
    )

    # Dispute Details
    status = models.CharField(
        max_length=20,
        choices=DISPUTE_STATUS_CHOICES,
        default='opened'
    )

    reason = models.CharField(
        max_length=50,
        choices=DISPUTE_REASON_CHOICES,
        help_text="Reason for dispute"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount being disputed"
    )

    # Processor Information (metadata only)
    stripe_dispute_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Stripe Dispute ID"
    )

    stripe_charge_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Stripe Charge ID"
    )

    # Timeline
    opened_at = models.DateTimeField(
        help_text="When dispute was opened"
    )

    respond_by = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deadline to respond to dispute"
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When dispute was closed"
    )

    # Evidence Submission (metadata only)
    evidence_submitted = models.BooleanField(
        default=False,
        help_text="Whether evidence was submitted to processor"
    )

    evidence_submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When evidence was submitted"
    )

    # Resolution
    resolution = models.CharField(
        max_length=20,
        blank=True,
        help_text="Dispute resolution (won/lost)"
    )

    resolution_reason = models.TextField(
        blank=True,
        help_text="Reason for resolution (from processor)"
    )

    # Internal Notes (NOT sent to processor)
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes about dispute (platform use only)"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_payment_dispute'
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['firm', 'status', '-opened_at']),
            models.Index(fields=['invoice', '-opened_at']),
            models.Index(fields=['stripe_dispute_id']),
        ]

    def __str__(self):
        return f"Dispute {self.stripe_dispute_id} - {self.invoice.invoice_number} (${self.amount})"
```

### Dispute Workflow

#### Step 1: Dispute Opened (from Stripe webhook)

```python
def handle_dispute_opened(stripe_dispute_data):
    """
    Handle dispute.created webhook from Stripe.

    Args:
        stripe_dispute_data: Dispute object from Stripe
    """
    from modules.finance.models import Invoice, PaymentDispute
    from modules.firm.audit import audit

    # Find invoice by Stripe charge ID
    invoice = Invoice.objects.get(
        stripe_invoice_id=stripe_dispute_data['charge']['invoice']
    )

    # Create dispute record
    dispute = PaymentDispute.objects.create(
        firm=invoice.firm,
        invoice=invoice,
        status='opened',
        reason=stripe_dispute_data['reason'],
        amount=stripe_dispute_data['amount'] / 100,  # Stripe uses cents
        stripe_dispute_id=stripe_dispute_data['id'],
        stripe_charge_id=stripe_dispute_data['charge']['id'],
        opened_at=timezone.now(),
        respond_by=timezone.fromtimestamp(stripe_dispute_data['evidence_details']['due_by']),
    )

    # Update invoice status
    invoice.status = 'disputed'
    invoice.save()

    # Create audit event
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
        severity='CRITICAL'
    )

    # Notify firm admin
    # notify_firm_admin_dispute_opened(dispute)

    return dispute
```

#### Step 2: Submit Evidence

```python
def submit_dispute_evidence(dispute, evidence_data):
    """
    Submit evidence to Stripe for dispute.

    Args:
        dispute: PaymentDispute instance
        evidence_data: Evidence to submit (contract, communication, etc.)
    """
    import stripe
    from modules.firm.audit import audit

    # Submit to Stripe
    stripe.Dispute.modify(
        dispute.stripe_dispute_id,
        evidence={
            'customer_name': dispute.invoice.client.company_name,
            'customer_email_address': dispute.invoice.client.primary_contact_email,
            'billing_address': f"{dispute.invoice.client.street_address}, {dispute.invoice.client.city}",
            'receipt': evidence_data.get('receipt_url'),
            'customer_signature': evidence_data.get('contract_signature_url'),
            'service_date': str(dispute.invoice.issue_date),
            'service_documentation': evidence_data.get('service_docs_url'),
        }
    )

    # Update dispute
    dispute.evidence_submitted = True
    dispute.evidence_submitted_at = timezone.now()
    dispute.status = 'under_review'
    dispute.save()

    # Audit
    audit.log_billing_event(
        firm=dispute.firm,
        action='dispute_evidence_submitted',
        actor=request.user,
        metadata={
            'dispute_id': dispute.id,
            'stripe_dispute_id': dispute.stripe_dispute_id,
        }
    )
```

#### Step 3: Dispute Resolved (from Stripe webhook)

```python
def handle_dispute_closed(stripe_dispute_data):
    """
    Handle dispute.closed webhook from Stripe.

    Args:
        stripe_dispute_data: Dispute object from Stripe
    """
    from modules.finance.models import PaymentDispute
    from modules.firm.audit import audit

    # Find dispute
    dispute = PaymentDispute.objects.get(
        stripe_dispute_id=stripe_dispute_data['id']
    )

    # Update dispute
    dispute.status = 'closed'
    dispute.resolution = stripe_dispute_data['status']  # 'won' or 'lost'
    dispute.resolution_reason = stripe_dispute_data.get('reason', '')
    dispute.closed_at = timezone.now()
    dispute.save()

    # Update invoice
    if dispute.resolution == 'won':
        # Firm won - invoice remains paid
        dispute.invoice.status = 'paid'
    elif dispute.resolution == 'lost':
        # Firm lost - funds reversed
        dispute.invoice.status = 'charged_back'
        dispute.invoice.amount_paid -= dispute.amount

    dispute.invoice.save()

    # Audit
    audit.log_billing_event(
        firm=dispute.firm,
        action=f'dispute_{dispute.resolution}',
        actor=None,
        metadata={
            'dispute_id': dispute.id,
            'invoice_id': dispute.invoice.id,
            'resolution': dispute.resolution,
            'amount': float(dispute.amount),
        },
        severity='CRITICAL'
    )

    # Notify firm admin
    # notify_firm_admin_dispute_resolved(dispute)
```

## Chargeback Handling

Chargebacks are a type of dispute where the customer's bank reverses the payment. They follow the same workflow as disputes but with stricter timelines.

**Key Differences**:
- Chargebacks have shorter response windows (typically 7-14 days)
- Evidence requirements are stricter
- Losing a chargeback may increase processing fees

**Model**: Use the same `PaymentDispute` model with `reason='fraudulent'` or similar.

## Retry Logic

### Automatic Retry Strategy

```python
def schedule_payment_retry(invoice):
    """
    Schedule automatic payment retry for failed invoice.

    Retry strategy:
    - 1st retry: 3 days after failure
    - 2nd retry: 7 days after failure
    - 3rd retry: 14 days after failure
    - After 3 failures: Mark as overdue, notify customer

    Args:
        invoice: Invoice with failed payment
    """
    from datetime import timedelta

    retry_delays = {
        0: timedelta(days=3),   # 1st retry
        1: timedelta(days=7),   # 2nd retry
        2: timedelta(days=14),  # 3rd retry
    }

    if invoice.payment_retry_count < 3:
        # Schedule retry
        delay = retry_delays.get(invoice.payment_retry_count, timedelta(days=7))
        retry_at = timezone.now() + delay

        # Create Celery task (future implementation)
        # retry_invoice_payment.apply_async(
        #     args=[invoice.id],
        #     eta=retry_at
        # )

        # Audit
        audit.log_billing_event(
            firm=invoice.firm,
            action='payment_retry_scheduled',
            metadata={
                'invoice_id': invoice.id,
                'retry_count': invoice.payment_retry_count + 1,
                'retry_at': str(retry_at),
            }
        )
    else:
        # Max retries reached
        invoice.status = 'overdue'
        invoice.save()

        # Audit
        audit.log_billing_event(
            firm=invoice.firm,
            action='payment_retry_exhausted',
            metadata={
                'invoice_id': invoice.id,
                'total_retries': invoice.payment_retry_count,
            },
            severity='WARNING'
        )

        # Notify customer
        # notify_customer_payment_overdue(invoice)
```

## Refund Handling

### Full Refund

```python
def process_refund(invoice, reason, refunded_by):
    """
    Process full refund for an invoice.

    Args:
        invoice: Invoice to refund
        reason: Reason for refund
        refunded_by: User who authorized refund
    """
    import stripe
    from modules.firm.audit import audit

    # Process refund via Stripe
    refund = stripe.Refund.create(
        payment_intent=invoice.stripe_payment_intent_id,
        reason=reason,
    )

    # Update invoice
    invoice.status = 'refunded'
    invoice.amount_paid = 0
    invoice.save()

    # Create audit event
    audit.log_billing_event(
        firm=invoice.firm,
        action='invoice_refunded',
        actor=refunded_by,
        metadata={
            'invoice_id': invoice.id,
            'amount': float(invoice.total_amount),
            'reason': reason,
            'stripe_refund_id': refund.id,
        }
    )

    # Create credit for customer (optional)
    from modules.finance.models import CreditLedgerEntry
    CreditLedgerEntry.objects.create(
        firm=invoice.firm,
        client=invoice.client,
        entry_type='credit',
        amount=invoice.total_amount,
        source='refund',
        source_invoice=invoice,
        description=f'Refund for {invoice.invoice_number}: {reason}',
        created_by=refunded_by,
    )
```

## Reporting

### Payment Failure Report

```python
def generate_payment_failure_report(firm, date_from, date_to):
    """Generate payment failure report for firm."""
    from modules.finance.models import Invoice

    failures = Invoice.objects.filter(
        firm=firm,
        payment_failed_at__gte=date_from,
        payment_failed_at__lte=date_to
    ).values('payment_failure_code').annotate(
        count=Count('id'),
        total_amount=Sum('total_amount')
    )

    return {
        'period': f'{date_from} to {date_to}',
        'total_failures': failures.aggregate(Sum('count'))['count__sum'] or 0,
        'total_amount_failed': failures.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'by_reason': list(failures),
    }
```

### Dispute Summary

```python
def generate_dispute_summary(firm):
    """Generate dispute summary for firm."""
    from modules.finance.models import PaymentDispute

    disputes = PaymentDispute.objects.filter(firm=firm)

    return {
        'total_disputes': disputes.count(),
        'open_disputes': disputes.filter(status='opened').count(),
        'won_disputes': disputes.filter(resolution='won').count(),
        'lost_disputes': disputes.filter(resolution='lost').count(),
        'total_disputed_amount': disputes.aggregate(Sum('amount'))['amount__sum'] or 0,
    }
```

## Implementation Checklist

- [ ] Add payment failure fields to Invoice model
- [ ] Create PaymentDispute model
- [ ] Implement handle_payment_failure() helper
- [ ] Implement handle_dispute_opened() webhook handler
- [ ] Implement handle_dispute_closed() webhook handler
- [ ] Implement retry logic with Celery tasks
- [ ] Add evidence submission workflow
- [ ] Create reporting queries
- [ ] Add admin notifications
- [ ] Create customer notification templates

## Next Steps

1. Add payment failure fields to Invoice model (migration)
2. Create PaymentDispute model (migration)
3. Set up Stripe webhook handlers
4. Implement retry logic
5. Add admin dashboard for disputes
6. Test dispute workflow with Stripe test mode
