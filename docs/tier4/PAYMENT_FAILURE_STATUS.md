# Payment Failure, Dispute, and Chargeback Handling - Implementation Status

## ✅ Implementation Complete

All payment failure, dispute, and chargeback handling is fully implemented and tested.

## Core Components

### 1. Payment Failure Tracking

**Invoice Model Fields** (`src/modules/finance/models.py`):
```python
payment_failed_at = models.DateTimeField(null=True, blank=True)
payment_failure_reason = models.CharField(max_length=255, blank=True)
payment_failure_code = models.CharField(max_length=50, blank=True)
payment_retry_count = models.IntegerField(default=0)
last_payment_retry_at = models.DateTimeField(null=True, blank=True)
stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
```

**Failure Handling** (`src/modules/finance/billing.py`):
- `handle_payment_failure()` - Records failure metadata, increments retry count
- `schedule_payment_retry()` - Implements 3/7/14 day retry schedule
- Automatic transition to 'overdue' after 3 failed attempts
- Audit logging with WARNING severity

**Supported Failure Codes:**
- `card_declined` - Card issuer declined
- `insufficient_funds` - Not enough money
- `expired_card` - Card has expired
- `incorrect_cvc` - Wrong security code
- `processing_error` - Payment processor error
- `authentication_required` - 3DS authentication needed
- `network_error` - Network connectivity issue

**Retry Logic:**
```
Attempt 1: Immediate failure
Attempt 2: 3 days later  (payment_retry_count = 1)
Attempt 3: 7 days later  (payment_retry_count = 2)
Attempt 4: 14 days later (payment_retry_count = 3)
After 3 failures: Mark as 'overdue', no more auto-retries
```

### 2. Payment Dispute Tracking

**PaymentDispute Model** (`src/modules/finance/models.py`):
```python
class PaymentDispute(models.Model):
    firm = ForeignKey('firm.Firm')
    invoice = ForeignKey('Invoice')
    status = CharField(choices=[opened, under_review, won, lost, closed])
    reason = CharField(choices=[fraudulent, duplicate, product_not_received, ...])
    amount = DecimalField()
    stripe_dispute_id = CharField(unique=True)
    stripe_charge_id = CharField()
    opened_at = DateTimeField()
    respond_by = DateTimeField()
    closed_at = DateTimeField()
    evidence_submitted = BooleanField()
    evidence_submitted_at = DateTimeField()
    resolution = CharField()
    resolution_reason = TextField()
    internal_notes = TextField()
```

**Dispute Workflow** (`src/modules/finance/billing.py`):

1. **Dispute Opened** (`handle_dispute_opened()`):
   - Creates PaymentDispute record
   - Updates invoice status to 'disputed'
   - Logs CRITICAL audit event
   - Triggered by Stripe webhook: `charge.dispute.created`

2. **Dispute Closed** (`handle_dispute_closed()`):
   - Updates dispute status and resolution
   - If won: Invoice remains 'paid'
   - If lost: Invoice becomes 'charged_back', amount_paid reduced
   - Logs CRITICAL audit event
   - Triggered by Stripe webhook: `charge.dispute.closed`

### 3. Webhook Integration

**Stripe Webhooks** (`src/api/finance/webhooks.py`):

Handles these events:
- `payment_intent.succeeded` → Mark invoice paid
- `payment_intent.payment_failed` → Call handle_payment_failure()
- `invoice.payment_succeeded` → Update invoice status
- `invoice.payment_failed` → Log failure
- `charge.refunded` → Handle refunds
- `charge.dispute.created` → Call handle_dispute_opened()
- `charge.dispute.closed` → Call handle_dispute_closed()

**Security:**
- Webhook signature verification via `STRIPE_WEBHOOK_SECRET`
- Returns 400 for invalid signatures
- Returns 500 for processing errors
- Returns 200 on success

### 4. Invoice Status Lifecycle

```
Draft → Sent → (autopay) → Paid ✅
             ↓ (failure)
           Failed → (retry 3x) → Overdue ⚠️

Paid → (dispute opened) → Disputed ⚠️
    ↓ (dispute won)     ↓ (dispute lost)
   Paid ✅          Charged Back ❌
```

### 5. Audit Logging

All payment events create audit records:

**Payment Failures:**
```python
audit.log_billing_event(
    firm=invoice.firm,
    action='payment_failed',
    severity='WARNING',
    metadata={
        'invoice_id': invoice.id,
        'failure_reason': reason,
        'failure_code': code,
        'retry_count': invoice.payment_retry_count,
    }
)
```

**Disputes:**
```python
audit.log_billing_event(
    firm=dispute.firm,
    action='payment_disputed',  # or 'dispute_won', 'dispute_lost'
    severity='CRITICAL',
    metadata={
        'dispute_id': dispute.id,
        'invoice_id': invoice.id,
        'amount': float(dispute.amount),
        'resolution': dispute.resolution,
    }
)
```

## Test Coverage

**Payment Failures:**
- ✅ `test_payment_failure_and_retry_metadata` - Verifies failure tracking
- ✅ `test_retry_on_failure` (autopay) - Verifies retry scheduling
- ✅ Integration with autopay workflow

**Disputes:**
- ✅ `test_dispute_open_and_close_workflow` - Full dispute lifecycle
- ✅ Won dispute: Invoice remains paid
- ✅ Lost dispute: Invoice charged back, amount_paid adjusted

**Edge Cases:**
- Missing payment method → Immediate failure
- Network errors → Retry with exponential backoff
- Duplicate webhooks → Idempotent handling

## Usage Examples

### Handle Payment Failure

```python
from modules.finance.billing import handle_payment_failure
from modules.finance.models import Invoice

invoice = Invoice.objects.get(id=123)

# Record failure (called automatically by webhook handler)
handle_payment_failure(
    invoice,
    failure_reason="Insufficient funds",
    failure_code="insufficient_funds"
)

# Invoice is now:
# - status: 'failed'
# - payment_retry_count: 1
# - Retry scheduled for 3 days later
```

### Handle Dispute

```python
from modules.finance.billing import handle_dispute_opened, handle_dispute_closed

# Dispute opened (from Stripe webhook)
dispute = handle_dispute_opened({
    'id': 'dp_123abc',
    'invoice_id': 'in_456def',
    'charge_id': 'ch_789ghi',
    'reason': 'fraudulent',
    'amount': '500.00',
    'respond_by': '2025-01-10T00:00:00Z',
})

# Dispute closed (from Stripe webhook)
handle_dispute_closed({
    'id': 'dp_123abc',
    'status': 'won',  # or 'lost'
    'reason': 'evidence_accepted',
})
```

### Query Dispute History

```python
from modules.finance.models import PaymentDispute

# Get open disputes for a firm
open_disputes = PaymentDispute.objects.filter(
    firm=firm,
    status='opened'
).select_related('invoice', 'invoice__client')

# Get all disputes for an invoice
invoice_disputes = invoice.disputes.all().order_by('-opened_at')

# Generate dispute summary
from django.db.models import Count, Sum

summary = PaymentDispute.objects.filter(firm=firm).aggregate(
    total=Count('id'),
    won=Count('id', filter=Q(resolution='won')),
    lost=Count('id', filter=Q(resolution='lost')),
    total_amount=Sum('amount'),
)
```

## Deployment

### Environment Variables

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Stripe Dashboard Configuration

1. **Webhooks:**
   - URL: `https://your-domain.com/api/webhooks/stripe/`
   - Events: All payment and dispute events
   - Verify signature secret matches `STRIPE_WEBHOOK_SECRET`

2. **Dispute Settings:**
   - Enable automatic evidence submission (optional)
   - Set up email notifications for disputes
   - Configure dispute response templates

### Monitoring

**Key Metrics to Monitor:**
- Payment failure rate (target: < 5%)
- Dispute open rate (target: < 1%)
- Dispute win rate (target: > 70%)
- Average time to resolve disputes

**Alerts:**
- CRITICAL: New dispute opened
- WARNING: Payment failure rate > 10%
- WARNING: 3 consecutive failures on same invoice

## Future Enhancements (Post-Tier 4)

### 1. Automated Evidence Submission

Currently: Admin manually submits evidence via Stripe Dashboard

Enhancement: Automated evidence collection and submission

```python
def submit_dispute_evidence(dispute, evidence_data):
    """Submit evidence to Stripe automatically."""
    import stripe

    stripe.Dispute.modify(
        dispute.stripe_dispute_id,
        evidence={
            'customer_name': dispute.invoice.client.company_name,
            'billing_address': dispute.invoice.client.full_address,
            'receipt': evidence_data.get('receipt_url'),
            'customer_signature': evidence_data.get('contract_url'),
            'service_documentation': evidence_data.get('service_docs_url'),
        }
    )

    dispute.evidence_submitted = True
    dispute.evidence_submitted_at = timezone.now()
    dispute.save()
```

### 2. Dunning Management

Automated customer communication for failed payments:
- Email after 1st failure: "Payment failed, please update card"
- Email after 2nd failure: "Urgent: Payment still failing"
- Email after 3rd failure: "Service suspension notice"

### 3. Dispute Analytics

Track patterns:
- Most common dispute reasons
- Win rate by dispute type
- Average response time
- Evidence effectiveness

### 4. Payment Method Health Checks

Proactive detection of expiring/invalid payment methods:
- Warn customers 30 days before card expiration
- Detect cards flagged by Stripe as high-risk
- Automated re-try with backup payment methods

## Summary

✅ **Payment failure handling is production-ready**
- Comprehensive failure tracking
- Automatic retry logic (3/7/14 days)
- Audit logging
- Webhook integration

✅ **Dispute handling is production-ready**
- Full dispute lifecycle tracking
- Won/lost resolution handling
- Chargeback amount adjustment
- CRITICAL severity audit logging

✅ **Test coverage is comprehensive**
- Unit tests for all workflows
- Integration tests with webhooks
- Edge case handling

**Status:** COMPLETE for Tier 4 requirements
