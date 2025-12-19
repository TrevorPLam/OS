"""
CRM Models: Client, Proposal, Contract.

Implements the "Quote-to-Cash" workflow for management consulting.
All relationships are enforced at the database level with foreign keys.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Client(models.Model):
    """
    Client (Company) entity.

    Represents the organization the consultant works with.
    Each client can have multiple contacts, proposals, and contracts.
    """
    STATUS_CHOICES = [
        ('lead', 'Lead'),
        ('prospect', 'Prospect'),
        ('active', 'Active Client'),
        ('inactive', 'Inactive'),
        ('lost', 'Lost'),
    ]

    # Core Fields
    company_name = models.CharField(max_length=255, unique=True)
    industry = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')

    # Contact Information
    primary_contact_name = models.CharField(max_length=255)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=50, blank=True)

    # Address
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='USA')

    # Business Metadata
    website = models.URLField(blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated annual revenue"
    )

    # Internal Tracking
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="How did we acquire this lead? (e.g., referral, cold outreach)"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_clients',
        help_text="The consultant who owns this relationship"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_clients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return self.company_name


class Proposal(models.Model):
    """
    Proposal (Quote) entity.

    Represents a formal proposal sent to a client.
    Can be converted into a Contract upon acceptance.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Client'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    # Relationships
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_proposals'
    )

    # Proposal Details
    proposal_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(
        help_text="Scope of work, deliverables, timeline"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Financial Terms
    total_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='USD')

    # Timeline
    valid_until = models.DateField(
        help_text="Proposal expiration date"
    )
    estimated_start_date = models.DateField(null=True, blank=True)
    estimated_end_date = models.DateField(null=True, blank=True)

    # Audit Fields
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_proposals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['proposal_number']),
        ]

    def __str__(self):
        return f"{self.proposal_number} - {self.client.company_name}"


class Contract(models.Model):
    """
    Contract (Signed Agreement) entity.

    Represents a signed contract with a client.
    Created from an accepted Proposal or independently.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
        ('on_hold', 'On Hold'),
    ]

    PAYMENT_TERMS_CHOICES = [
        ('net_15', 'Net 15'),
        ('net_30', 'Net 30'),
        ('net_45', 'Net 45'),
        ('net_60', 'Net 60'),
        ('due_on_receipt', 'Due on Receipt'),
        ('milestone', 'Milestone-based'),
    ]

    # Relationships
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='contracts'
    )
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        help_text="The proposal that led to this contract (if applicable)"
    )
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='signed_contracts',
        help_text="The consultant who signed this contract"
    )

    # Contract Details
    contract_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(
        help_text="Statement of work, deliverables, terms"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Financial Terms
    total_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='USD')
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default='net_30'
    )

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    signed_date = models.DateField(null=True, blank=True)

    # Contract Documents
    contract_file_url = models.URLField(
        blank=True,
        help_text="Link to signed contract PDF in S3"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_contracts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['contract_number']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.client.company_name}"
