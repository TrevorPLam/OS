"""
Finance Models: Invoice, Bill, LedgerEntry.

Implements basic accounting for management consulting:
- Invoice: Accounts Receivable (AR) - client billing
- Bill: Accounts Payable (AP) - vendor payments
- LedgerEntry: Double-entry bookkeeping for P&L

TIER 0: All financial records MUST belong to exactly one Firm for tenant isolation.
"""
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from modules.projects.models import Project
from modules.firm.utils import FirmScopedManager


class Invoice(models.Model):
    """
    Invoice entity (Accounts Receivable).

    Represents money owed to us by post-sale clients.
    Can be linked to Projects for Time & Materials billing.

    TIER 0: Belongs to a Firm through Client relationship.
    Direct firm FK included for efficient queries.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Client'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="Firm (workspace) this invoice belongs to"
    )

    # Relationships - UPDATED to reference clients.Client
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="The post-sale client being invoiced"
    )

    # TIER 4: Link to Engagement (default, can be overridden by Master Admin)
    engagement = models.ForeignKey(
        'clients.ClientEngagement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text="Engagement this invoice belongs to (Master Admin can override)"
    )

    # TIER 4: Override tracking for engagement linkage
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

    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text="Optional: link to specific project"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices'
    )

    # Invoice Details
    invoice_number = models.CharField(max_length=50)  # TIER 0: Unique per firm (see Meta)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Financial Amounts
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total amount received from client"
    )
    currency = models.CharField(max_length=3, default='USD')

    # Payment Terms
    issue_date = models.DateField()
    due_date = models.DateField()
    payment_terms = models.CharField(
        max_length=50,
        default='Net 30',
        help_text="e.g., Net 30, Due on Receipt"
    )

    # Payment Tracking
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when invoice was fully paid"
    )

    # Invoice Content
    line_items = models.JSONField(
        default=list,
        help_text="List of line items: [{description, quantity, rate, amount}, ...]"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes visible to client on invoice"
    )

    # Payment Integration
    stripe_invoice_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Stripe Invoice ID if using Stripe billing"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'finance_invoices'
        ordering = ['-issue_date', '-created_at']
        indexes = [
            models.Index(fields=['firm', 'status']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'client', 'status']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'invoice_number']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'due_date']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', '-issue_date']),  # TIER 0: Firm scoping
        ]
        # TIER 0: Invoice numbers must be unique within a firm (not globally)
        unique_together = [['firm', 'invoice_number']]

    def save(self, *args, **kwargs):
        """
        Enforce TIER 4 billing invariants before saving.

        Invariants:
        1. Invoice MUST have a client
        2. Invoice SHOULD have an engagement (unless Master Admin override)
        3. If engagement_override=True, must have reason and override_by
        4. Auto-link to active engagement if none provided
        """
        from django.core.exceptions import ValidationError

        # Invariant 1: Invoice must belong to a Client
        if not self.client_id:
            raise ValidationError("Invoice must belong to a Client")

        # Invariant 3: Master Admin override validation
        if self.engagement_override:
            if not self.engagement_override_reason:
                raise ValidationError(
                    "Override reason required when engagement is overridden"
                )
            if not self.engagement_override_by_id:
                raise ValidationError(
                    "Override by (Master Admin) required when engagement is overridden"
                )

        # Invariant 2: Invoice should link to engagement (auto-link if not provided)
        if not self.engagement_id and not self.engagement_override and self.client_id:
            # Try to auto-link to active engagement
            from modules.clients.models import ClientEngagement
            active_engagement = ClientEngagement.objects.filter(
                client_id=self.client_id,
                status='current'
            ).first()

            if active_engagement:
                self.engagement = active_engagement
            else:
                raise ValidationError(
                    f"Client has no active engagement. Master Admin override required. "
                    f"Set engagement_override=True, provide reason, and specify override_by."
                )

        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        """Calculate remaining balance."""
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        from django.utils import timezone
        return self.status in ['sent', 'partial'] and self.due_date < timezone.now().date()

    def get_package_revenue(self):
        """
        Calculate total package fee revenue on this invoice (TIER 4: Task 4.4).

        Returns:
            Decimal: Total amount from package fee line items
        """
        total = Decimal('0.00')
        for item in self.line_items:
            if item.get('type') == 'package_fee':
                total += Decimal(str(item.get('amount', 0)))
        return total

    def get_hourly_revenue(self):
        """
        Calculate total hourly billing revenue on this invoice (TIER 4: Task 4.4).

        Returns:
            Decimal: Total amount from hourly line items
        """
        total = Decimal('0.00')
        for item in self.line_items:
            if item.get('type') == 'hourly':
                total += Decimal(str(item.get('amount', 0)))
        return total

    def get_billing_breakdown(self):
        """
        Get mixed billing breakdown for this invoice (TIER 4: Task 4.4).

        Separates package fees from hourly billing for clear reporting.

        Returns:
            dict: {
                'package_revenue': Decimal,
                'hourly_revenue': Decimal,
                'other_revenue': Decimal,
                'total_revenue': Decimal,
                'package_items': list,
                'hourly_items': list,
                'other_items': list
            }
        """
        package_items = []
        hourly_items = []
        other_items = []

        for item in self.line_items:
            item_type = item.get('type', 'other')
            if item_type == 'package_fee':
                package_items.append(item)
            elif item_type == 'hourly':
                hourly_items.append(item)
            else:
                other_items.append(item)

        package_revenue = sum(Decimal(str(item.get('amount', 0))) for item in package_items)
        hourly_revenue = sum(Decimal(str(item.get('amount', 0))) for item in hourly_items)
        other_revenue = sum(Decimal(str(item.get('amount', 0))) for item in other_items)

        return {
            'package_revenue': package_revenue,
            'hourly_revenue': hourly_revenue,
            'other_revenue': other_revenue,
            'total_revenue': package_revenue + hourly_revenue + other_revenue,
            'package_items': package_items,
            'hourly_items': hourly_items,
            'other_items': other_items,
            'package_count': len(package_items),
            'hourly_count': len(hourly_items),
            'other_count': len(other_items),
        }

    def __str__(self):
        return f"{self.invoice_number} - {self.client.company_name} (${self.total_amount})"


class Bill(models.Model):
    """
    Bill entity (Accounts Payable).

    Represents money we owe to vendors/suppliers.
    Used for expense tracking and cash flow management.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('disputed', 'Disputed'),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='bills',
        help_text="Firm (workspace) this bill belongs to"
    )

    # Vendor Information
    vendor_name = models.CharField(max_length=255)
    vendor_email = models.EmailField(blank=True)

    # Optional Project Link (for project expenses)
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bills',
        help_text="Optional: link to project if this is a project expense"
    )

    # Bill Details
    bill_number = models.CharField(
        max_length=50,
        help_text="Vendor's bill/invoice number"
    )
    reference_number = models.CharField(
        max_length=50,
        help_text="Our internal reference number (unique per firm)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')

    # Financial Amounts
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total amount paid to vendor"
    )
    currency = models.CharField(max_length=3, default='USD')

    # Dates
    bill_date = models.DateField(
        help_text="Date on vendor's bill"
    )
    due_date = models.DateField()
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when bill was fully paid"
    )

    # Categorization
    expense_category = models.CharField(
        max_length=100,
        help_text="e.g., Software, Travel, Office Supplies"
    )

    # Bill Content
    description = models.TextField(blank=True)
    line_items = models.JSONField(
        default=list,
        help_text="List of line items: [{description, quantity, rate, amount}, ...]"
    )

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_bills'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'finance_bills'
        ordering = ['-bill_date', '-created_at']
        indexes = [
            models.Index(fields=['firm', 'status']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'vendor_name', 'status']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'reference_number']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'due_date']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', '-bill_date']),  # TIER 0: Firm scoping
        ]
        # TIER 0: Reference numbers must be unique within a firm (not globally)
        unique_together = [['firm', 'reference_number']]

    @property
    def balance_due(self):
        """Calculate remaining balance."""
        return self.total_amount - self.amount_paid

    def __str__(self):
        return f"{self.reference_number} - {self.vendor_name} (${self.total_amount})"


class LedgerEntry(models.Model):
    """
    LedgerEntry entity (General Ledger).

    Implements double-entry bookkeeping for P&L reporting.
    Every transaction creates TWO entries (debit and credit).

    Example: When we receive payment for an invoice:
    - Entry 1: Debit "Cash" (asset increase)
    - Entry 2: Credit "Accounts Receivable" (asset decrease)

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Invoice/Bill references, but included directly for efficiency.
    """
    ENTRY_TYPE_CHOICES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    ACCOUNT_CHOICES = [
        # Assets
        ('cash', 'Cash'),
        ('accounts_receivable', 'Accounts Receivable'),
        ('equipment', 'Equipment'),

        # Liabilities
        ('accounts_payable', 'Accounts Payable'),
        ('loans_payable', 'Loans Payable'),

        # Equity
        ('owners_equity', "Owner's Equity"),
        ('retained_earnings', 'Retained Earnings'),

        # Revenue
        ('consulting_revenue', 'Consulting Revenue'),
        ('other_income', 'Other Income'),

        # Expenses
        ('salaries_expense', 'Salaries Expense'),
        ('software_expense', 'Software Expense'),
        ('travel_expense', 'Travel Expense'),
        ('office_expense', 'Office Supplies'),
        ('other_expense', 'Other Expense'),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='ledger_entries',
        help_text="Firm (workspace) this ledger entry belongs to"
    )

    # Core Double-Entry Fields
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    account = models.CharField(max_length=50, choices=ACCOUNT_CHOICES)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Transaction Metadata
    transaction_date = models.DateField()
    description = models.CharField(max_length=255)

    # Reference Links (for audit trail)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ledger_entries'
    )
    bill = models.ForeignKey(
        Bill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ledger_entries'
    )

    # Grouping (to link debit and credit entries together)
    transaction_group_id = models.CharField(
        max_length=50,
        help_text="UUID to group related debit/credit entries"
    )

    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ledger_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'finance_ledger_entries'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['firm', 'account', 'transaction_date']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'transaction_group_id']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', '-transaction_date']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'entry_type']),  # TIER 0: Firm scoping
        ]
        verbose_name_plural = 'Ledger Entries'

    def __str__(self):
        return f"{self.entry_type.upper()}: {self.account} - ${self.amount} ({self.transaction_date})"


class CreditLedgerEntry(models.Model):
    """
    Credit ledger entry for client credits (TIER 4).

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
        Invoice,
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
        Invoice,
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

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'finance_credit_ledger'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'client', '-created_at']),
            models.Index(fields=['client', 'entry_type', '-created_at']),
            models.Index(fields=['source_invoice']),
            models.Index(fields=['applied_to_invoice']),
        ]
        verbose_name_plural = 'Credit Ledger Entries'

    def save(self, *args, **kwargs):
        """Enforce credit ledger invariants."""
        from django.core.exceptions import ValidationError

        # Goodwill/correction credits require reason and approval
        if self.entry_type == 'credit' and self.source in ['goodwill', 'correction']:
            if not self.reason:
                raise ValidationError(
                    f"Reason required for {self.source} credits"
                )
            if not self.approved_by_id:
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
        from django.core.exceptions import ValidationError
        raise ValidationError(
            "Credit ledger entries cannot be deleted. "
            "Create a reversing entry instead."
        )

    def __str__(self):
        return f"{self.entry_type.upper()}: ${self.amount} - {self.client.company_name}"
