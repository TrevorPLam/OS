# Recurring Payments / Autopay Workflow - Implementation Status

## ✅ Implementation Complete

The core autopay workflow is fully implemented and tested:

### Core Components

1. **Autopay Execution** (`billing.py`)
   - `execute_autopay_for_invoice()` - Immediate autopay on invoice creation
   - `schedule_autopay()` - Schedule invoice for future autopay
   - `_charge_invoice()` - Charge via Stripe payment intent
   - `process_recurring_invoices()` - Process all due invoices
   - `handle_payment_failure()` - Track failures and schedule retries

2. **Management Command**
   ```bash
   python manage.py process_recurring_charges [--dry-run]
   ```
   - Processes all invoices marked for autopay
   - Dry-run mode to preview charges
   - Automatic retry on failure (3, 7, 14 day schedule)

3. **Stripe Integration**
   - `StripeService.create_payment_intent()` - Process payments
   - Webhook handlers (`/api/finance/webhooks/`)
     - `payment_intent.succeeded` - Mark invoice paid
     - `payment_intent.payment_failed` - Log failure
     - `invoice.payment_succeeded` - Update status
     - `charge.refunded` - Handle refunds

4. **Client Model Fields**
   - `autopay_enabled` - Enable/disable autopay per client
   - `autopay_payment_method_id` - Stripe payment method ID
   - `autopay_activated_at` - When autopay was enabled

5. **Invoice Model Fields**
   - `autopay_opt_in` - Invoice enrolled in autopay
   - `autopay_status` - Status: scheduled/processing/succeeded/failed/cancelled
   - `autopay_payment_method_id` - Payment method for this invoice
   - `autopay_next_charge_at` - When to attempt next charge
   - `autopay_last_attempt_at` - Last charge attempt timestamp
   - `autopay_cadence` - Charging frequency: monthly/quarterly/on_due

### Test Coverage

- ✅ Successful recurring charge (`test_successful_recurring_charge`)
- ✅ Retry on payment failure (`test_retry_on_failure`)
- ✅ Autopay cancellation when disabled (`test_autopay_cancelled_when_client_disabled`)
- ✅ Autopay execution without duplication (`test_autopay_execution_pays_invoice_without_duplication`)

### How It Works

**Workflow:**
1. Invoice created with `autopay_opt_in=True` (from client settings)
2. `schedule_autopay()` sets `autopay_next_charge_at` based on cadence
3. Cron job runs `process_recurring_charges` daily
4. System finds invoices where `autopay_next_charge_at <= now()`
5. For each invoice:
   - Verify client has `autopay_enabled=True`
   - Get payment method from invoice or client
   - Create Stripe PaymentIntent
   - On success: Mark paid, log audit event
   - On failure: Log failure, schedule retry (+3 days)

**Failure Handling:**
- Retry schedule: 3, 7, 14 days
- After 3 failures: Mark `overdue`, notify admin
- Tracks failure reason and code from Stripe
- Audit log for all payment attempts

### Deployment

**Cron Setup:**
```cron
# Process recurring charges daily at 3 AM
0 3 * * * cd /home/user/OS && python src/manage.py process_recurring_charges >> /var/log/autopay.log 2>&1
```

**Environment Variables:**
```bash
# In .env or production config
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Stripe Webhook Configuration:**
```
Webhook URL: https://your-domain.com/api/webhooks/stripe/
Events to subscribe:
- payment_intent.succeeded
- payment_intent.payment_failed
- invoice.payment_succeeded
- invoice.payment_failed
- charge.refunded
```

---

## 🔜 Future Enhancements (Post-Tier 4)

These are "nice-to-have" features that improve user experience but aren't required for core functionality:

### 1. Payment Method Setup Flow

**Current State:** Admins manually add payment method IDs via Django admin

**Enhancement:** Client-facing payment method setup

```python
# In modules/clients/views.py
from modules.finance.services import StripeService

@action(detail=True, methods=['post'])
def setup_autopay(self, request, pk=None):
    """
    Create Stripe SetupIntent for client to add payment method.

    Returns:
        {
            "client_secret": "seti_xxx",
            "setup_intent_id": "seti_xxx"
        }
    """
    client = self.get_object()

    setup_intent = StripeService.create_setup_intent(
        customer_id=client.stripe_customer_id,
        metadata={'client_id': client.id}
    )

    return Response({
        'client_secret': setup_intent.client_secret,
        'setup_intent_id': setup_intent.id,
    })
```

**Frontend:**
- Use Stripe Elements to collect payment method
- Confirm SetupIntent
- Save payment method ID to `client.autopay_payment_method_id`

### 2. Stripe Checkout Integration

**Current State:** `generate_payment_link()` returns placeholder URL

**Enhancement:** Real Stripe Checkout sessions

```python
@action(detail=True, methods=['post'])
def generate_payment_link(self, request, pk=None):
    """Generate real Stripe Checkout session."""
    invoice = self.get_object()

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'Invoice {invoice.invoice_number}',
                },
                'unit_amount': int(invoice.balance_due * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f'https://portal.example.com/invoices/{invoice.id}/success',
        cancel_url=f'https://portal.example.com/invoices/{invoice.id}',
        metadata={'invoice_id': invoice.id},
    )

    return Response({
        'payment_url': session.url,
        'session_id': session.id,
    })
```

### 3. Celery Task Integration

Replace cron with Celery beat:

```python
# In modules/finance/tasks.py
from celery import shared_task
from modules.finance.billing import process_recurring_invoices

@shared_task
def process_autopay_invoices():
    """Celery task to process autopay invoices."""
    return process_recurring_invoices()
```

```python
# In celerybeat_schedule
'process-autopay': {
    'task': 'modules.finance.tasks.process_autopay_invoices',
    'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
},
```

---

## Summary

✅ **Core autopay workflow is production-ready**
- Automatic invoice charging
- Retry on failure
- Audit logging
- Webhook handling
- Comprehensive tests

🔜 **Future enhancements improve UX but aren't blockers**
- Client-facing payment method setup (currently admin-only)
- Real Stripe Checkout URLs (currently placeholders)
- Celery integration (currently cron-based)

**Status:** COMPLETE for Tier 4 requirements
