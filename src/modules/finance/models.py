"""
Finance Models: Invoice, Bill, LedgerEntry.

Implements basic accounting for management consulting:
- Invoice: Accounts Receivable (AR) - client billing
- Bill: Accounts Payable (AP) - vendor payments
- LedgerEntry: Double-entry bookkeeping for P&L
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from modules.projects.models import Project


class Invoice(models.Model):
    """
    Invoice entity (Accounts Receivable).

    Represents money owed to us by post-sale clients.
    Can be linked to Projects for Time & Materials billing.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Client'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    # Relationships - UPDATED to reference clients.Client
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="The post-sale client being invoiced"
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices'
    )

    # Invoice Details
    invoice_number = models.CharField(max_length=50, unique=True)
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

    class Meta:
        db_table = 'finance_invoices'
        ordering = ['-issue_date', '-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['due_date']),
        ]

    @property
    def balance_due(self):
        """Calculate remaining balance."""
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        from django.utils import timezone
        return self.status in ['sent', 'partial'] and self.due_date < timezone.now().date()

    def __str__(self):
        return f"{self.invoice_number} - {self.client.company_name} (${self.total_amount})"


class Bill(models.Model):
    """
    Bill entity (Accounts Payable).

    Represents money we owe to vendors/suppliers.
    Used for expense tracking and cash flow management.
    """
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('disputed', 'Disputed'),
    ]

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
        unique=True,
        help_text="Our internal reference number"
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_bills'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_bills'
        ordering = ['-bill_date', '-created_at']
        indexes = [
            models.Index(fields=['vendor_name', 'status']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['due_date']),
        ]

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
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ledger_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_ledger_entries'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['account', 'transaction_date']),
            models.Index(fields=['transaction_group_id']),
        ]
        verbose_name_plural = 'Ledger Entries'

    def __str__(self):
        return f"{self.entry_type.upper()}: {self.account} - ${self.amount} ({self.transaction_date})"
