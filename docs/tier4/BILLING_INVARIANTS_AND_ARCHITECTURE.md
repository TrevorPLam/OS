# Tier 4: Billing Invariants & Architecture

**Status**: 📋 DOCUMENTED (Implementation: In Progress)
**Created**: 2025-12-25

## Overview

Tier 4 ensures money, scope, and incentives align correctly through enforced billing invariants, approval gates, and proper financial tracking.

## Core Requirements (from NOTES_TO_CLAUDE.md)

> Rule: Tier 4 ensures money, scope, and incentives align.

Key principles:
- Invoice must belong to Client
- Invoice links to Engagement by default
- Engagement defines pricing mode (package, hourly, or mixed)
- Time entries are NOT billable by default
- Approval required before billing time entries
- Master Admin can override engagement linkage

## Task 4.1: Billing Invariants

### Required Model Enhancements

#### Invoice Model Enhancements
**File**: `src/modules/finance/models.py`

Add fields to Invoice:
```python
# Link to Engagement (default, can be overridden by Master Admin)
engagement = models.ForeignKey(
    'clients.ClientEngagement',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='invoices',
    help_text="Engagement this invoice belongs to (Master Admin can override)"
)

# Override tracking
engagement_override = models.BooleanField(
    default=False,
    help_text="True if Master Admin overrode default engagement linkage"
)

engagement_override_reason = models.TextField(
    blank=True,
    help_text="Reason for engagement override (required if overridden)"
)

engagement_override_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='invoice_engagement_overrides',
    help_text="Master Admin who overrode engagement"
)
```

**Validation**:
- Invoice MUST have a client
- Invoice SHOULD have an engagement (unless Master Admin override)
- If engagement_override=True, must have reason and override_by

#### ClientEngagement Model Enhancements
**File**: `src/modules/clients/models.py`

Add pricing mode fields:
```python
# Pricing Mode
PRICING_MODE_CHOICES = [
    ('package', 'Package/Fixed Fee'),
    ('hourly', 'Hourly/Time & Materials'),
    ('mixed', 'Mixed (Package + Hourly)'),
]

pricing_mode = models.CharField(
    max_length=20,
    choices=PRICING_MODE_CHOICES,
    default='package',
    help_text="Pricing model for this engagement"
)

# Package Fee (if pricing_mode = 'package' or 'mixed')
package_fee = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    null=True,
    blank=True,
    validators=[MinValueValidator(Decimal('0.01'))],
    help_text="Fixed package fee (required for package/mixed mode)"
)

package_fee_schedule = models.CharField(
    max_length=50,
    blank=True,
    help_text="Payment schedule (e.g., 'Monthly', 'Quarterly', 'One-time')"
)

# Hourly Billing (if pricing_mode = 'hourly' or 'mixed')
allow_hourly_billing = models.BooleanField(
    default=False,
    help_text="Allow hourly billing for this engagement"
)

hourly_rate_default = models.DecimalField(
    max_digits=8,
    decimal_places=2,
    null=True,
    blank=True,
    validators=[MinValueValidator(Decimal('0.01'))],
    help_text="Default hourly rate (if hourly billing allowed)"
)

# Firm FK (for tenant isolation)
firm = models.ForeignKey(
    'firm.Firm',
    on_delete=models.CASCADE,
    related_name='client_engagements',
    help_text="Firm this engagement belongs to"
)
```

**Validation**:
- If pricing_mode='package' or 'mixed': package_fee required
- If pricing_mode='hourly' or 'mixed': hourly_rate_default required
- If pricing_mode='mixed': both package_fee AND hourly_rate required

### Billing Invariants to Enforce

#### Invariant 1: Invoice → Client (Always)
```python
# In Invoice.save()
if not self.client:
    raise ValidationError("Invoice must belong to a Client")
```

#### Invariant 2: Invoice → Engagement (Default)
```python
# In Invoice.save()
if not self.engagement and not self.engagement_override:
    # Auto-link to active engagement
    active_engagement = self.client.engagements.filter(
        status='current'
    ).first()

    if active_engagement:
        self.engagement = active_engagement
    else:
        raise ValidationError(
            "Client has no active engagement. Master Admin override required."
        )
```

#### Invariant 3: Master Admin Override Validation
```python
# In Invoice.save()
if self.engagement_override:
    if not self.engagement_override_reason:
        raise ValidationError("Override reason required")
    if not self.engagement_override_by:
        raise ValidationError("Override by (Master Admin) required")
    # TODO: Verify engagement_override_by is Master Admin
```

#### Invariant 4: Pricing Mode Consistency
```python
# In Invoice creation
if engagement:
    if engagement.pricing_mode == 'package':
        # Package-only: line items should be package fees
        pass
    elif engagement.pricing_mode == 'hourly':
        # Hourly-only: line items should be time entries
        pass
    elif engagement.pricing_mode == 'mixed':
        # Both allowed
        pass
```

## Task 4.2: Package Fee Invoicing

### Requirements
- Package fees defined at engagement creation
- Package invoices auto-generated on schedule
- Package fees survive renewals correctly
- No duplicate invoices

### Implementation Approach

#### Auto-Invoice Generation (Celery Task)
```python
# In modules/finance/tasks.py (future)
from celery import shared_task
from modules.clients.models import ClientEngagement
from modules.finance.models import Invoice

@shared_task
def generate_package_invoices():
    """
    Daily task: Generate package fee invoices for active engagements.

    For each engagement with pricing_mode='package' or 'mixed':
    - Check if invoice due based on package_fee_schedule
    - Create invoice if not already exists for period
    - Mark as auto-generated
    """
    engagements = ClientEngagement.objects.filter(
        status='current',
        pricing_mode__in=['package', 'mixed']
    )

    for engagement in engagements:
        # Check if invoice needed
        if should_generate_package_invoice(engagement):
            create_package_invoice(engagement)
```

#### Invoice Creation Helper
```python
def create_package_invoice(engagement):
    """Create package fee invoice for engagement."""
    from modules.firm.audit import audit

    invoice = Invoice.objects.create(
        firm=engagement.firm,
        client=engagement.client,
        engagement=engagement,
        status='draft',
        subtotal=engagement.package_fee,
        tax_amount=calculate_tax(engagement.package_fee),
        total_amount=engagement.package_fee + tax,
        issue_date=today(),
        due_date=today() + timedelta(days=30),
        line_items=[{
            'description': f'Package Fee - {engagement.contract.title}',
            'quantity': 1,
            'rate': float(engagement.package_fee),
            'amount': float(engagement.package_fee),
            'type': 'package_fee'
        }]
    )

    # Audit event
    audit.log_billing_event(
        firm=engagement.firm,
        action='package_invoice_auto_generated',
        metadata={
            'invoice_id': invoice.id,
            'engagement_id': engagement.id,
            'amount': float(engagement.package_fee)
        }
    )

    return invoice
```

### Duplicate Prevention
- Check for existing invoices for same engagement + period
- Use unique constraint: (engagement, period_start_date)
- Log if duplicate detected (audit event)

## Task 4.3: Hourly Billing with Approval Gates

See: [TIME_ENTRY_APPROVAL_SYSTEM.md](./TIME_ENTRY_APPROVAL_SYSTEM.md)

Summary:
- Time entries NOT billable by default
- Staff/Admin approval required before billing
- Client approval optional (future)
- Only approved time entries on invoices

## Task 4.4: Mixed Billing

### Requirements
- Engagement can specify mixed billing
- Package and hourly line items are distinct
- Reporting clearly separates the two

### Invoice Line Item Structure
```json
{
  "line_items": [
    {
      "type": "package_fee",
      "description": "Monthly Retainer - Strategy Consulting",
      "quantity": 1,
      "rate": 5000.00,
      "amount": 5000.00
    },
    {
      "type": "hourly",
      "description": "Additional Consulting Hours (10h @ $150/hr)",
      "quantity": 10,
      "rate": 150.00,
      "amount": 1500.00,
      "time_entry_ids": [123, 124, 125]
    }
  ]
}
```

### Mixed Invoice Generation
1. Generate package fee line item (if applicable)
2. Query approved, unbilled time entries
3. Group by rate, add as hourly line items
4. Calculate totals: package_total + hourly_total
5. Apply tax
6. Create invoice

## Task 4.5: Credit Ledger

See: [CREDIT_LEDGER_SYSTEM.md](./CREDIT_LEDGER_SYSTEM.md)

Summary:
- Credits tracked in ledger (not ad-hoc fields)
- Credit creation and application auditable
- Credit balance always reconciles

## Task 4.6: Recurring Payments (Autopay)

### Requirements
- Recurring payments auto-pay invoices as issued
- Recurring payments do NOT generate invoices themselves
- Autopay can be disabled per client

### Model Enhancement
**File**: `src/modules/clients/models.py`

Add to Client model:
```python
# Autopay Settings
autopay_enabled = models.BooleanField(
    default=False,
    help_text="Enable automatic payment of invoices"
)

autopay_payment_method_id = models.CharField(
    max_length=255,
    blank=True,
    help_text="Stripe payment method ID for autopay"
)

autopay_activated_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text="When autopay was enabled"
)

autopay_activated_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='autopay_activations',
    help_text="Who enabled autopay"
)
```

### Autopay Workflow
1. Invoice created (draft status)
2. Invoice sent to client (sent status)
3. Check if client.autopay_enabled
4. If yes: Trigger payment via Stripe
5. If payment succeeds: Mark invoice as paid
6. If payment fails: See Task 4.7

## Task 4.7: Payment Failures, Disputes, Chargebacks

See: [PAYMENT_FAILURE_HANDLING.md](./PAYMENT_FAILURE_HANDLING.md)

Summary:
- Payment failures are first-class events (audited)
- Disputes and chargebacks tracked explicitly
- Platform retains dispute metadata only

## Task 4.8: Renewal Billing Behavior

### Requirements
- Renewals create new engagements
- Old engagement invoices remain untouched
- New billing terms apply only going forward

### Renewal Process
1. Current engagement ends (status='completed')
2. New engagement created (parent_engagement=old_engagement)
3. New pricing terms apply (can differ from old)
4. Old invoices: Keep status, amounts unchanged
5. New invoices: Generated from new engagement

### Continuity Without Mutation
```python
# In ClientEngagement.renew()
def renew(self, new_package_fee=None, new_hourly_rate=None):
    """
    Create renewal engagement.

    Args:
        new_package_fee: New package fee (if changing)
        new_hourly_rate: New hourly rate (if changing)

    Returns:
        New ClientEngagement instance
    """
    # Mark current as completed
    self.status = 'completed'
    self.save()

    # Create new engagement
    renewal = ClientEngagement.objects.create(
        firm=self.firm,
        client=self.client,
        contract=self.contract,  # Same or new contract
        parent_engagement=self,
        version=self.version + 1,
        pricing_mode=self.pricing_mode,
        package_fee=new_package_fee or self.package_fee,
        hourly_rate_default=new_hourly_rate or self.hourly_rate_default,
        start_date=self.end_date + timedelta(days=1),
        end_date=self.end_date + timedelta(days=365),  # 1 year renewal
        status='current'
    )

    # Audit event
    from modules.firm.audit import audit
    audit.log_billing_event(
        firm=self.firm,
        action='engagement_renewed',
        metadata={
            'old_engagement_id': self.id,
            'new_engagement_id': renewal.id,
            'old_package_fee': float(self.package_fee or 0),
            'new_package_fee': float(renewal.package_fee or 0)
        }
    )

    return renewal
```

## Database Migrations Required

### Migration 1: Enhance Invoice Model
- Add engagement FK
- Add engagement_override fields
- Add indexes

### Migration 2: Enhance ClientEngagement Model
- Add firm FK
- Add pricing_mode fields
- Add package_fee, hourly_rate fields
- Add indexes

### Migration 3: Enhance Client Model
- Add autopay fields

### Migration 4: Create CreditLedger Model
See: CREDIT_LEDGER_SYSTEM.md

### Migration 5: Enhance TimeEntry Model
See: TIME_ENTRY_APPROVAL_SYSTEM.md

## Implementation Priority

1. **High Priority** (Tier 4 Core):
   - TimeEntry approval fields (Task 4.3)
   - Invoice → Engagement link (Task 4.1)
   - ClientEngagement pricing mode (Task 4.1)
   - Credit Ledger model (Task 4.5)

2. **Medium Priority** (Tier 4 Complete):
   - Package invoice generation (Task 4.2)
   - Mixed billing support (Task 4.4)
   - Autopay fields (Task 4.6)

3. **Documentation** (Tier 4):
   - Payment failure handling (Task 4.7)
   - Renewal workflows (Task 4.8)

## Next Steps

1. Create TIME_ENTRY_APPROVAL_SYSTEM.md
2. Create CREDIT_LEDGER_SYSTEM.md
3. Create PAYMENT_FAILURE_HANDLING.md
4. Implement model enhancements
5. Create migrations
6. Add validation logic
7. Add helper utilities
8. Test billing workflows
