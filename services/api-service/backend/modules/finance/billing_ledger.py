"""
Billing Ledger Models (DOC-13.1, DOC-13.2).

Implements ledger-first billing per BILLING_LEDGER_SPEC (docs/03-reference/requirements/DOC-13.md).

Key Requirements:
- All money-impacting actions as immutable ledger entries
- Idempotent posting with unique idempotency keys
- Allocations for payment→invoice and retainer→invoice
- Derived balances explainable from ledger
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError


class BillingLedgerEntry(models.Model):
    """
    Immutable billing ledger entry (DOC-13.1).

    Per docs/03-reference/requirements/DOC-13.md Section 2.1: "LedgerEntry MUST NOT be edited after posting.
    Corrections MUST occur via compensating entries."

    Entry Types (docs/03-reference/requirements/DOC-13.md Section 3):
    - invoice_issued: Creates AR for an invoice (amount positive)
    - payment_received: Reduces AR when allocated to invoices (amount positive)
    - retainer_deposit: Increases retainer balance (amount positive)
    - retainer_applied: Moves value from retainer to invoice (via allocation)
    - credit_memo: Reduces AR or adjusts balances (requires reason)
    - adjustment: Balance adjustments (requires reason)
    - write_off: Marks uncollectible AR (requires policy + audit)
    """

    ENTRY_TYPE_CHOICES = [
        ('invoice_issued', 'Invoice Issued'),
        ('payment_received', 'Payment Received'),
        ('retainer_deposit', 'Retainer Deposit'),
        ('retainer_applied', 'Retainer Applied'),
        ('credit_memo', 'Credit Memo'),
        ('adjustment', 'Adjustment'),
        ('write_off', 'Write-Off'),
    ]

    # Tenant context
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='billing_ledger_entries',
        help_text="Firm this ledger entry belongs to"
    )

    # Entry identification
    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPE_CHOICES,
        help_text="Type of billing event"
    )

    # Idempotency (docs/03-reference/requirements/DOC-13.md Section 5)
    idempotency_key = models.CharField(
        max_length=255,
        help_text="Unique key for idempotent posting (required)"
    )

    # Associations (docs/03-reference/requirements/DOC-13.md Section 2.1)
    account = models.ForeignKey(
        'crm.Client',
        on_delete=models.PROTECT,
        related_name='billing_ledger_entries',
        help_text="Account (Client) this entry belongs to"
    )

    invoice = models.ForeignKey(
        'finance.Invoice',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='billing_ledger_entries',
        help_text="Invoice reference (nullable)"
    )

    engagement = models.ForeignKey(
        'crm.Contract',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='billing_ledger_entries',
        help_text="Engagement reference (nullable, Contract=Engagement per DOC-06.1)"
    )

    # Financial details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount (signed; typically positive per spec)"
    )

    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency code (ISO 4217)"
    )

    # Timing (docs/03-reference/requirements/DOC-13.md Section 2.1)
    occurred_at = models.DateTimeField(
        help_text="Business time when the event occurred"
    )

    posted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="System time when entry was posted (immutable)"
    )

    # External reference
    reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="External reference (check number, processor ref, etc.)"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Bounded metadata (reason codes, processor details, etc.)"
    )

    # Audit trail (docs/03-reference/requirements/DOC-13.md Section 2.1)
    created_by_actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_billing_ledger_entries',
        help_text="Actor who created this entry"
    )

    correlation_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Correlation ID for request tracing"
    )

    class Meta:
        db_table = 'billing_ledger_entry'
        ordering = ['-posted_at', '-occurred_at']
        indexes = [
            models.Index(fields=['firm', 'account', '-posted_at']),
            models.Index(fields=['firm', 'entry_type']),
            models.Index(fields=['firm', 'invoice']),
            models.Index(fields=['firm', '-occurred_at']),
            models.Index(fields=['idempotency_key']),
        ]
        # Per docs/03-reference/requirements/DOC-13.md Section 5.2: Uniqueness on idempotency_key scoped to tenant + entry_type
        unique_together = [['firm', 'entry_type', 'idempotency_key']]
        verbose_name = 'Billing Ledger Entry'
        verbose_name_plural = 'Billing Ledger Entries'

    def __str__(self):
        return f"{self.get_entry_type_display()}: {self.account} - {self.currency} {self.amount}"

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        """
        Override save to enforce immutability.

        Per docs/03-reference/requirements/DOC-13.md Section 2.1: "LedgerEntry MUST NOT be edited after posting."
        """
        if self.pk and not force_insert:
            # Entry already exists - prevent updates
            raise ValidationError(
                "BillingLedgerEntry is immutable. "
                "Create a compensating entry instead of updating."
            )

        # Validate on creation
        self.full_clean()

        # Only allow insert
        super().save(force_insert=True, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete to prevent deletion.

        Per docs/03-reference/requirements/DOC-13.md Section 2.1: Ledger entries are immutable.
        """
        raise ValidationError(
            "BillingLedgerEntry cannot be deleted. "
            "Ledger entries are immutable. Create a compensating entry."
        )

    def clean(self):
        """
        Validate ledger entry before posting.

        Per docs/03-reference/requirements/DOC-13.md Section 3: Entry type-specific validations.
        """
        errors = {}

        # Validate idempotency key
        if not self.idempotency_key:
            errors['idempotency_key'] = "Idempotency key is required"

        # Validate amount based on entry type (per docs/03-reference/requirements/DOC-13.md Section 3)
        if self.entry_type in ['invoice_issued', 'payment_received', 'retainer_deposit']:
            if self.amount <= 0:
                errors['amount'] = f"{self.get_entry_type_display()} amount must be positive"

        # Validate required associations
        if self.entry_type == 'invoice_issued' and not self.invoice:
            errors['invoice'] = "invoice_issued entry must reference an invoice"

        if self.entry_type == 'retainer_applied' and not self.invoice:
            errors['invoice'] = "retainer_applied entry must reference an invoice"

        # Validate reason codes for adjustments and write-offs (docs/03-reference/requirements/DOC-13.md Section 3.5, 3.6)
        if self.entry_type in ['credit_memo', 'adjustment', 'write_off']:
            if not self.metadata.get('reason_code'):
                errors['metadata'] = f"{self.get_entry_type_display()} requires reason_code in metadata"

        # Validate currency
        if len(self.currency) != 3:
            errors['currency'] = "Currency must be 3-letter ISO code"

        if errors:
            raise ValidationError(errors)

    def get_unapplied_amount(self) -> Decimal:
        """
        Calculate unapplied amount for this entry.

        Per docs/03-reference/requirements/DOC-13.md Section 2.2: "Sum(allocations from an entry) MUST NOT exceed
        available unapplied amount."

        Returns:
            Decimal: Amount available for allocation
        """
        total_allocated = self.allocations_from.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        return self.amount - total_allocated


class BillingAllocation(models.Model):
    """
    Allocation mapping (DOC-13.2).

    Per docs/03-reference/requirements/DOC-13.md Section 2.2: "Allocations map value from one entry to another
    (e.g., payment applied to invoice; retainer applied to invoice)."

    Examples:
    - Payment → Invoice: from_entry=payment_received, to_entry=invoice_issued
    - Retainer → Invoice: from_entry=retainer_deposit, to_entry=invoice_issued
    - Retainer Application: from_entry=retainer_applied, to_entry=invoice_issued
    """

    # Tenant context
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='billing_allocations',
        help_text="Firm this allocation belongs to"
    )

    # Allocation mapping (docs/03-reference/requirements/DOC-13.md Section 2.2)
    from_entry = models.ForeignKey(
        BillingLedgerEntry,
        on_delete=models.PROTECT,
        related_name='allocations_from',
        help_text="Source ledger entry (payment, retainer deposit, etc.)"
    )

    to_entry = models.ForeignKey(
        BillingLedgerEntry,
        on_delete=models.PROTECT,
        related_name='allocations_to',
        help_text="Target ledger entry (typically invoice_issued)"
    )

    # Allocation amount (docs/03-reference/requirements/DOC-13.md Section 2.2)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount allocated (must be positive)"
    )

    # Audit trail
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When allocation was created"
    )

    created_by_actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_billing_allocations',
        help_text="Actor who created this allocation"
    )

    correlation_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Correlation ID for request tracing"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional allocation metadata"
    )

    class Meta:
        db_table = 'billing_allocation'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'from_entry']),
            models.Index(fields=['firm', 'to_entry']),
            models.Index(fields=['firm', '-created_at']),
        ]
        # Prevent duplicate allocations
        unique_together = [['from_entry', 'to_entry']]
        verbose_name = 'Billing Allocation'
        verbose_name_plural = 'Billing Allocations'

    def __str__(self):
        return f"Allocation: {self.from_entry.entry_type} → {self.to_entry.entry_type} ({self.amount})"

    def clean(self):
        """
        Validate allocation constraints.

        Per docs/03-reference/requirements/DOC-13.md Section 2.2: "Sum(allocations from an entry) MUST NOT exceed
        available unapplied amount."
        """
        errors = {}

        # Validate firm consistency
        if self.from_entry and self.to_entry:
            if self.from_entry.firm_id != self.to_entry.firm_id:
                errors['firm'] = "Allocations must be within same firm"

            if self.from_entry.firm_id != self.firm_id:
                errors['firm'] = "Allocation firm must match entry firm"

        # Validate amount doesn't exceed available
        if self.from_entry:
            unapplied = self.from_entry.get_unapplied_amount()
            # If updating existing allocation, add back current amount
            if self.pk:
                try:
                    existing = BillingAllocation.objects.get(pk=self.pk)
                    unapplied += existing.amount
                except BillingAllocation.DoesNotExist:
                    pass

            if self.amount > unapplied:
                errors['amount'] = (
                    f"Allocation amount ({self.amount}) exceeds available "
                    f"unapplied amount ({unapplied}) on source entry"
                )

        # Validate allocation makes sense for entry types
        if self.from_entry and self.to_entry:
            valid_allocations = {
                'payment_received': ['invoice_issued'],
                'retainer_deposit': ['invoice_issued'],
                'retainer_applied': ['invoice_issued'],
            }

            if self.from_entry.entry_type in valid_allocations:
                if self.to_entry.entry_type not in valid_allocations[self.from_entry.entry_type]:
                    errors['to_entry'] = (
                        f"Cannot allocate {self.from_entry.get_entry_type_display()} "
                        f"to {self.to_entry.get_entry_type_display()}"
                    )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


# Helper functions for ledger operations

def post_invoice_issued(
    firm,
    account,
    invoice,
    amount: Decimal,
    occurred_at,
    idempotency_key: str,
    created_by_actor=None,
    correlation_id: str = '',
    **metadata
) -> BillingLedgerEntry:
    """
    Post invoice_issued entry to ledger.

    Per docs/03-reference/requirements/DOC-13.md Section 3.1: Creates AR for an invoice.

    Args:
        firm: Firm instance
        account: Client instance (account per DOC-06.1)
        invoice: Invoice instance
        amount: Invoice amount (must be positive)
        occurred_at: Business time of invoice issuance
        idempotency_key: Unique key for idempotent posting
        created_by_actor: User who issued invoice
        correlation_id: Correlation ID for tracing
        **metadata: Additional metadata

    Returns:
        BillingLedgerEntry instance

    Raises:
        ValidationError: If validation fails
        IntegrityError: If idempotency key collision (replay)
    """
    entry = BillingLedgerEntry(
        firm=firm,
        entry_type='invoice_issued',
        account=account,
        invoice=invoice,
        amount=amount,
        occurred_at=occurred_at,
        idempotency_key=idempotency_key,
        created_by_actor=created_by_actor,
        correlation_id=correlation_id,
        metadata=metadata
    )
    entry.save()
    return entry


def post_payment_received(
    firm,
    account,
    amount: Decimal,
    occurred_at,
    idempotency_key: str,
    reference: str = '',
    created_by_actor=None,
    correlation_id: str = '',
    **metadata
) -> BillingLedgerEntry:
    """
    Post payment_received entry to ledger.

    Per docs/03-reference/requirements/DOC-13.md Section 3.2: Reduces AR when allocated to invoices.

    Args:
        firm: Firm instance
        account: Client instance
        amount: Payment amount (must be positive)
        occurred_at: Business time of payment receipt
        idempotency_key: Unique key for idempotent posting
        reference: External reference (check number, processor ref, etc.)
        created_by_actor: User who recorded payment
        correlation_id: Correlation ID for tracing
        **metadata: Additional metadata (processor details, etc.)

    Returns:
        BillingLedgerEntry instance
    """
    entry = BillingLedgerEntry(
        firm=firm,
        entry_type='payment_received',
        account=account,
        amount=amount,
        occurred_at=occurred_at,
        idempotency_key=idempotency_key,
        reference=reference,
        created_by_actor=created_by_actor,
        correlation_id=correlation_id,
        metadata=metadata
    )
    entry.save()
    return entry


def allocate_payment_to_invoice(
    payment_entry: BillingLedgerEntry,
    invoice_entry: BillingLedgerEntry,
    amount: Decimal,
    created_by_actor=None,
    correlation_id: str = ''
) -> BillingAllocation:
    """
    Allocate payment to invoice.

    Per docs/03-reference/requirements/DOC-13.md Section 2.2: Creates allocation from payment to invoice.

    Args:
        payment_entry: payment_received ledger entry
        invoice_entry: invoice_issued ledger entry
        amount: Amount to allocate
        created_by_actor: User creating allocation
        correlation_id: Correlation ID for tracing

    Returns:
        BillingAllocation instance

    Raises:
        ValidationError: If allocation violates constraints
    """
    allocation = BillingAllocation(
        firm=payment_entry.firm,
        from_entry=payment_entry,
        to_entry=invoice_entry,
        amount=amount,
        created_by_actor=created_by_actor,
        correlation_id=correlation_id
    )
    allocation.save()
    return allocation


def post_retainer_deposit(
    firm,
    account,
    amount: Decimal,
    occurred_at,
    idempotency_key: str,
    reference: str = '',
    created_by_actor=None,
    correlation_id: str = '',
    **metadata
) -> BillingLedgerEntry:
    """
    Post retainer_deposit entry to ledger.

    Per docs/03-reference/requirements/DOC-13.md Section 3.3: Increases retainer balance.

    Args:
        firm: Firm instance
        account: Client instance
        amount: Retainer deposit amount (must be positive)
        occurred_at: Business time of deposit
        idempotency_key: Unique key for idempotent posting
        reference: External reference (check number, etc.)
        created_by_actor: User who recorded deposit
        correlation_id: Correlation ID for tracing
        **metadata: Additional metadata

    Returns:
        BillingLedgerEntry instance
    """
    entry = BillingLedgerEntry(
        firm=firm,
        entry_type='retainer_deposit',
        account=account,
        amount=amount,
        occurred_at=occurred_at,
        idempotency_key=idempotency_key,
        reference=reference,
        created_by_actor=created_by_actor,
        correlation_id=correlation_id,
        metadata=metadata
    )
    entry.save()
    return entry


def get_ar_balance(firm, account) -> Decimal:
    """
    Calculate AR balance for an account.

    Per docs/03-reference/requirements/DOC-13.md Section 4: AR balance must be derivable from entries + allocations.

    Args:
        firm: Firm instance
        account: Client instance

    Returns:
        Decimal: AR balance (positive = owed to us)
    """
    # Sum invoice_issued entries
    invoiced = BillingLedgerEntry.objects.filter(
        firm=firm,
        account=account,
        entry_type='invoice_issued'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    # Subtract allocated payments
    allocated_payments = BillingAllocation.objects.filter(
        firm=firm,
        to_entry__account=account,
        to_entry__entry_type='invoice_issued',
        from_entry__entry_type='payment_received'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    # Subtract credit memos
    credits = BillingLedgerEntry.objects.filter(
        firm=firm,
        account=account,
        entry_type__in=['credit_memo', 'write_off']
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    return invoiced - allocated_payments - credits


def get_retainer_balance(firm, account) -> Decimal:
    """
    Calculate retainer balance for an account.

    Per docs/03-reference/requirements/DOC-13.md Section 4: Retainer balance must be derivable from entries.

    Args:
        firm: Firm instance
        account: Client instance

    Returns:
        Decimal: Retainer balance (positive = available retainer)
    """
    # Sum retainer deposits
    deposits = BillingLedgerEntry.objects.filter(
        firm=firm,
        account=account,
        entry_type='retainer_deposit'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    # Subtract allocated retainer applications
    applied = BillingAllocation.objects.filter(
        firm=firm,
        from_entry__account=account,
        from_entry__entry_type='retainer_deposit'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    return deposits - applied
