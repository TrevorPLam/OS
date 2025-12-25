# Tier 4: Credit Ledger System

**Status**: 📋 DOCUMENTED (Implementation: In Progress)
**Created**: 2025-12-25

## Overview

The Credit Ledger system tracks client credits in a structured, auditable way. Credits must be tracked in a ledger (not ad-hoc fields) to ensure:
- Every credit creation is auditable
- Every credit application is auditable
- Credit balance always reconciles
- No "lost" or "phantom" credits

## Principles

1. **Ledger-Based**: Credits tracked as ledger entries (debits/credits), not balance fields
2. **Immutable**: Credit entries cannot be modified after creation
3. **Auditable**: Every credit operation creates an audit event
4. **Reconcilable**: Balance can always be calculated from ledger entries

## Credit Types

### Credit Sources (How credits are created)

1. **Overpayment**: Client pays more than invoice total
2. **Refund**: Refund issued for cancelled service
3. **Goodwill**: Manual credit issued by firm (requires reason)
4. **Promotional**: Marketing promotion or discount
5. **Correction**: Billing error correction

### Credit Uses (How credits are applied)

1. **Invoice Payment**: Applied to outstanding invoice
2. **Partial Payment**: Applied to partially pay invoice
3. **Expired**: Credit expired (if credits have expiration policy)
4. **Refunded**: Credit converted back to cash refund

## Credit Ledger Model

**File**: `src/modules/finance/models.py`

```python
class CreditLedgerEntry(models.Model):
    """
    Credit ledger entry for client credits.

    Tracks creation and application of credits in an immutable ledger.
    Credits are ADDED via positive entries, APPLIED via negative entries.

    TIER 4: All credit operations must go through this ledger.
    """
    ENTRY_TYPE_CHOICES = [
        ('credit', 'Credit Added'),
        ('debit', 'Credit Applied/Used'),
    ]

    SOURCE_CHOICES = [
        ('overpayment', 'Overpayment'),
        ('refund', 'Refund'),
        ('goodwill', 'Goodwill Credit'),
        ('promotional', 'Promotional Credit'),
        ('correction', 'Billing Correction'),
    ]

    USE_CHOICES = [
        ('invoice_payment', 'Applied to Invoice'),
        ('partial_payment', 'Partial Payment'),
        ('expired', 'Credit Expired'),
        ('refunded', 'Refunded to Client'),
    ]

    # Tenant Context
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='credit_ledger',
        help_text="Firm this credit belongs to"
    )

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='credit_ledger',
        help_text="Client this credit belongs to"
    )

    # Entry Details
    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPE_CHOICES,
        help_text="Credit (added) or Debit (used)"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount of credit (always positive)"
    )

    # For Credits (entry_type='credit')
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        blank=True,
        help_text="How credit was created (for credit entries)"
    )

    source_invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_sources',
        help_text="Invoice that generated this credit (if applicable)"
    )

    # For Debits (entry_type='debit')
    use = models.CharField(
        max_length=20,
        choices=USE_CHOICES,
        blank=True,
        help_text="How credit was used (for debit entries)"
    )

    applied_to_invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_applications',
        help_text="Invoice this credit was applied to (if applicable)"
    )

    # Metadata
    description = models.TextField(
        help_text="Description of credit creation or use"
    )

    reason = models.TextField(
        blank=True,
        help_text="Reason for credit (required for goodwill/correction credits)"
    )

    # Authorization
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_credits',
        help_text="Who created this credit entry"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_credits',
        help_text="Who approved this credit (for goodwill/correction)"
    )

    # Expiration (if credits expire)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this credit expires (if applicable)"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)

    # Audit Event Link
    audit_event_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Link to audit event for this credit operation"
    )

    class Meta:
        db_table = 'finance_credit_ledger'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'client', '-created_at']),
            models.Index(fields=['client', 'entry_type', '-created_at']),
            models.Index(fields=['source_invoice']),
            models.Index(fields=['applied_to_invoice']),
        ]

    def save(self, *args, **kwargs):
        """Enforce credit ledger invariants."""
        from django.core.exceptions import ValidationError

        # Goodwill/correction credits require reason
        if self.entry_type == 'credit' and self.source in ['goodwill', 'correction']:
            if not self.reason:
                raise ValidationError(
                    f"Reason required for {self.source} credits"
                )
            if not self.approved_by:
                raise ValidationError(
                    f"Approval required for {self.source} credits"
                )

        # Credits must have source, debits must have use
        if self.entry_type == 'credit' and not self.source:
            raise ValidationError("Source required for credit entries")
        if self.entry_type == 'debit' and not self.use:
            raise ValidationError("Use required for debit entries")

        # Prevent modifications (immutable)
        if self.pk:
            raise ValidationError("Credit ledger entries are immutable")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of credit entries."""
        raise ValidationError(
            "Credit ledger entries cannot be deleted. "
            "Create a reversing entry instead."
        )

    def __str__(self):
        return f"{self.entry_type.upper()}: ${self.amount} - {self.client.company_name}"
```

## Client Credit Balance

Calculate balance from ledger entries:

```python
# In Client model or helper utility
def get_credit_balance(client):
    """
    Calculate client's current credit balance from ledger.

    Returns:
        Decimal: Current credit balance (sum of credits - sum of debits)
    """
    from modules.finance.models import CreditLedgerEntry
    from decimal import Decimal

    credits = CreditLedgerEntry.objects.filter(
        client=client,
        entry_type='credit'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    debits = CreditLedgerEntry.objects.filter(
        client=client,
        entry_type='debit'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    return credits - debits
```

## Credit Operations

### Creating a Credit

```python
from modules.finance.models import CreditLedgerEntry
from modules.firm.audit import audit

def create_credit(
    firm,
    client,
    amount,
    source,
    description,
    created_by,
    source_invoice=None,
    reason='',
    approved_by=None,
    expires_at=None
):
    """Create a credit for a client."""
    # Create ledger entry
    entry = CreditLedgerEntry.objects.create(
        firm=firm,
        client=client,
        entry_type='credit',
        amount=amount,
        source=source,
        source_invoice=source_invoice,
        description=description,
        reason=reason,
        created_by=created_by,
        approved_by=approved_by,
        expires_at=expires_at,
    )

    # Create audit event
    audit_event = audit.log_billing_event(
        firm=firm,
        action='credit_created',
        actor=created_by,
        metadata={
            'entry_id': entry.id,
            'client_id': client.id,
            'amount': float(amount),
            'source': source,
            'reason': reason,
        }
    )

    entry.audit_event_id = audit_event.id
    entry.save(update_fields=['audit_event_id'])

    return entry
```

### Applying a Credit

```python
def apply_credit(
    client,
    amount,
    applied_to_invoice,
    created_by,
    description='Credit applied to invoice'
):
    """Apply client credit to an invoice."""
    from django.core.exceptions import ValidationError

    # Check available balance
    balance = get_credit_balance(client)
    if balance < amount:
        raise ValidationError(
            f"Insufficient credit balance. Available: ${balance}, Requested: ${amount}"
        )

    # Create debit entry
    entry = CreditLedgerEntry.objects.create(
        firm=client.firm,
        client=client,
        entry_type='debit',
        amount=amount,
        use='invoice_payment',
        applied_to_invoice=applied_to_invoice,
        description=description,
        created_by=created_by,
    )

    # Create audit event
    audit_event = audit.log_billing_event(
        firm=client.firm,
        action='credit_applied',
        actor=created_by,
        metadata={
            'entry_id': entry.id,
            'client_id': client.id,
            'amount': float(amount),
            'invoice_id': applied_to_invoice.id,
        }
    )

    entry.audit_event_id = audit_event.id
    entry.save(update_fields=['audit_event_id'])

    return entry
```

## Reconciliation

### Daily Reconciliation Report

```python
def generate_credit_reconciliation_report(firm, date):
    """
    Generate daily credit reconciliation report.

    Returns:
        dict: {
            'total_credits_issued': Decimal,
            'total_credits_applied': Decimal,
            'net_change': Decimal,
            'total_outstanding_balance': Decimal,
            'entries': QuerySet
        }
    """
    from modules.finance.models import CreditLedgerEntry
    from decimal import Decimal

    entries = CreditLedgerEntry.objects.filter(
        firm=firm,
        created_at__date=date
    )

    credits_issued = entries.filter(entry_type='credit').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')

    credits_applied = entries.filter(entry_type='debit').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')

    # Calculate total outstanding balance across all clients
    all_entries = CreditLedgerEntry.objects.filter(firm=firm)
    total_credits = all_entries.filter(entry_type='credit').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')
    total_debits = all_entries.filter(entry_type='debit').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')

    return {
        'total_credits_issued': credits_issued,
        'total_credits_applied': credits_applied,
        'net_change': credits_issued - credits_applied,
        'total_outstanding_balance': total_credits - total_debits,
        'entries': entries,
    }
```

## Implementation Status

- [ ] Create CreditLedgerEntry model
- [ ] Add migration for credit ledger
- [ ] Implement create_credit() helper
- [ ] Implement apply_credit() helper
- [ ] Implement get_credit_balance() helper
- [ ] Add credit operations to invoice payment workflow
- [ ] Create reconciliation utilities
- [ ] Add tests for credit ledger

## Next Steps

1. Implement CreditLedgerEntry model in finance/models.py
2. Create migration
3. Add helper utilities in finance/utils.py or finance/credit_ledger.py
4. Integrate with invoice payment workflow
5. Add API endpoints for credit management
6. Add tests
