# AGENTS.md — Finance Module (Billing & Payments)

Last Updated: 2026-01-06
Applies To: `src/modules/finance/`

## Purpose

Handles all financial operations: invoicing, billing, payments, and accounting ledger.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Invoice, Bill, LedgerEntry, Payment, PaymentMethod (~2277 LOC) |
| `billing.py` | Billing calculation, invoice generation |
| `billing_ledger.py` | Immutable ledger operations |
| `services.py` | Financial services |
| `square_service.py` | Square payment integration |
| `reconciliation.py` | Payment reconciliation |
| `signals.py` | Post-payment hooks |

## Domain Model

```
Invoice (AR - money owed TO us)
    └── InvoiceLineItem
    └── Payment (partial or full)

Bill (AP - money WE owe)
    └── BillLineItem

LedgerEntry (immutable audit trail)
    └── All financial transactions
```

## Key Models

### Invoice

Accounts Receivable:

```python
class Invoice(models.Model):
    firm: FK[Firm]
    client: FK[Client]
    engagement: FK[ClientEngagement]      # Optional
    
    status: str                           # draft, sent, paid, partial, overdue, etc.
    invoice_number: str                   # Auto-generated
    issue_date: Date
    due_date: Date
    
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    
    # Override tracking
    engagement_override: bool             # Master Admin override
    engagement_override_reason: str
```

### InvoiceLineItem

Individual line items:

```python
class InvoiceLineItem(models.Model):
    invoice: FK[Invoice]
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    tax_rate: Decimal
```

### Payment

Payment against invoice:

```python
class Payment(models.Model):
    invoice: FK[Invoice]
    amount: Decimal
    payment_date: Date
    payment_method: str                  # card, ach, wire, check
    reference_number: str                # External reference
    
    # Square/Stripe integration
    external_payment_id: str
    processor: str                       # square, stripe
```

### BillingLedger

Immutable transaction log:

```python
class BillingLedger(models.Model):
    firm: FK[Firm]
    entry_type: str                      # invoice, payment, refund, adjustment
    reference_type: str                  # invoice, payment
    reference_id: int
    
    debit: Decimal
    credit: Decimal
    running_balance: Decimal
    
    created_at: DateTime                 # Immutable after creation
    
    class Meta:
        # NO update/delete allowed
```

## Payment Processing

### Square Integration

```python
from modules.finance.square_service import SquarePaymentService

service = SquarePaymentService(firm)

# Create payment
result = service.create_payment(
    invoice=invoice,
    amount=Decimal("100.00"),
    source_id="card_nonce_from_frontend",
)

# Handle webhooks
service.handle_webhook(event_type, payload)
```

### Payment States

```
Payment Created
    ↓
Payment Processing
    ↓
Payment Completed  ─or─  Payment Failed
    ↓                         ↓
Invoice Updated          Retry/Manual
```

## Billing Rules

1. **Immutability**: LedgerEntry records cannot be modified or deleted
2. **Balance Tracking**: Invoice.balance_due auto-updated on payment
3. **Overdue Detection**: Cron job marks invoices overdue after due_date
4. **Partial Payments**: Supported, status becomes "partial"

## Reconciliation

`reconciliation.py` handles:
- Matching payments to invoices
- Detecting discrepancies
- Generating reconciliation reports

## Dependencies

- **Depends on**: `firm/`, `clients/`, `projects/`
- **Used by**: Client portal (view invoices/pay)
- **External**: Square SDK, Stripe SDK

## URLs

All routes under `/api/v1/finance/`:

```
# Invoices
GET/POST   /invoices/
GET/PUT    /invoices/{id}/
POST       /invoices/{id}/send/
GET        /invoices/{id}/pdf/

# Payments
GET/POST   /payments/
GET        /payments/{id}/

# Square
POST       /square/create-payment/
POST       /square/webhook/

# Stripe
POST       /stripe/webhook/

# Ledger (read-only)
GET        /ledger/
GET        /ledger/reconciliation-report/
```

## Webhooks

Payment processor webhooks handled in `api/finance/`:
- `square_webhooks.py` — Square payment events
- `webhooks.py` — Stripe payment events
