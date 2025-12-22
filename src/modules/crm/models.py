"""
CRM Models: Lead, Prospect, Proposal, Contract, Campaign.

This module handles PRE-SALE operations only (Marketing & Sales).
Post-sale Client management moved to modules.clients.

Workflow: Lead → Prospect → Proposal → (Accepted) → Client (in modules.clients)
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Lead(models.Model):
    """
    Marketing-captured prospect (Pre-Sale).

    Represents initial contact before qualification.
    When qualified, converts to Prospect for sales pipeline.
    """
    STATUS_CHOICES = [
        ('new', 'New Lead'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified - Moving to Sales'),
        ('converted', 'Converted to Prospect'),
        ('lost', 'Lost'),
    ]

    SOURCE_CHOICES = [
        ('website', 'Website Form'),
        ('referral', 'Referral'),
        ('campaign', 'Marketing Campaign'),
        ('cold_outreach', 'Cold Outreach'),
        ('event', 'Event/Conference'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ]

    # Company Information
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    # Contact Information
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    contact_title = models.CharField(max_length=100, blank=True)

    # Lead Tracking
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='website'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    lead_score = models.IntegerField(
        default=0,
        help_text="Automated or manual lead scoring (0-100)"
    )

    # Campaign Tracking
    campaign = models.ForeignKey(
        'Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        help_text="Marketing campaign that generated this lead"
    )

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_leads',
        help_text="Sales rep assigned to this lead"
    )

    # Timeline
    captured_date = models.DateField(auto_now_add=True)
    first_contacted = models.DateField(null=True, blank=True)
    qualified_date = models.DateField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['campaign']),
        ]

    def __str__(self):
        return f"{self.company_name} - {self.get_status_display()}"


class Prospect(models.Model):
    """
    Sales pipeline prospect (Pre-Sale).

    Active sales opportunity after lead qualification.
    Can have multiple proposals. Converts to Client when won.
    """
    STAGE_CHOICES = [
        ('discovery', 'Discovery'),
        ('needs_analysis', 'Needs Analysis'),
        ('proposal', 'Proposal Sent'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won - Converting to Client'),
        ('lost', 'Lost'),
    ]

    # Origin
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prospects',
        help_text="Original lead that created this prospect"
    )

    # Company Information
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated annual revenue"
    )

    # Contact Information
    primary_contact_name = models.CharField(max_length=255)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=50, blank=True)
    primary_contact_title = models.CharField(max_length=100, blank=True)

    # Address
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='USA')

    # Pipeline Tracking
    pipeline_stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default='discovery'
    )
    probability = models.IntegerField(
        default=50,
        help_text="Win probability percentage (0-100)"
    )

    # Financial Forecast
    estimated_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Estimated deal value"
    )
    close_date_estimate = models.DateField(
        help_text="Expected close date"
    )

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_prospects',
        help_text="Account executive assigned"
    )

    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_date = models.DateField(null=True, blank=True)
    won_date = models.DateField(null=True, blank=True)
    lost_date = models.DateField(null=True, blank=True)

    # Loss Tracking
    lost_reason = models.CharField(max_length=255, blank=True)

    # Audit
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_prospects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['pipeline_stage']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['close_date_estimate']),
        ]

    def __str__(self):
        return f"{self.company_name} - {self.get_pipeline_stage_display()}"


class Campaign(models.Model):
    """
    Marketing & Sales Campaign tracking.

    Tracks campaigns for both new business acquisition AND existing client engagement:
    - Lead generation (new prospects)
    - Client renewals and upsells
    - Client annual reviews
    """
    TYPE_CHOICES = [
        ('email', 'Email Campaign'),
        ('webinar', 'Webinar'),
        ('content', 'Content Marketing'),
        ('event', 'Event/Conference'),
        ('social', 'Social Media'),
        ('partnership', 'Partnership'),
        ('renewal', 'Renewal Campaign'),
        ('annual_review', 'Annual Review'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]

    # Campaign Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning'
    )

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()

    # Budget
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Target Audience - Can target BOTH prospects AND clients
    targeted_clients = models.ManyToManyField(
        'clients.Client',
        blank=True,
        related_name='targeted_campaigns',
        help_text="Existing clients targeted by this campaign (renewals, upsells, etc.)"
    )

    # Performance Metrics - New Business
    target_leads = models.IntegerField(
        default=0,
        help_text="Target number of new leads"
    )
    leads_generated = models.IntegerField(
        default=0,
        help_text="Auto-calculated from Lead.campaign foreign key"
    )
    opportunities_created = models.IntegerField(
        default=0,
        help_text="Number of Prospects created from campaign leads"
    )

    # Performance Metrics - Client Engagement
    clients_contacted = models.IntegerField(
        default=0,
        help_text="Number of existing clients contacted"
    )
    renewal_proposals_sent = models.IntegerField(
        default=0,
        help_text="Number of renewal/upsell proposals generated"
    )
    renewals_won = models.IntegerField(
        default=0,
        help_text="Number of successful renewals/upsells"
    )

    # Financial Metrics
    revenue_generated = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Revenue from won deals (new + renewal) attributed to this campaign"
    )

    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_campaigns'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_campaigns'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Proposal(models.Model):
    """
    Proposal (Quote/Engagement Letter) entity.

    Handles both new business and existing client proposals:
    - prospective_client: New business (links to Prospect)
    - update_client: Expansion/upsell to existing Client
    - renewal_client: Renewal for existing Client

    When accepted, becomes an Engagement Letter (Contract).
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    TYPE_CHOICES = [
        ('prospective_client', 'Prospective Client - New Business'),
        ('update_client', 'Update Client - Expansion/Upsell'),
        ('renewal_client', 'Renewal Client - Contract Renewal'),
    ]

    # Proposal Type
    proposal_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='prospective_client',
        help_text="Type of proposal: new business, expansion, or renewal"
    )

    # Relationships - EITHER prospect OR client (based on type)
    prospect = models.ForeignKey(
        Prospect,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='proposals',
        help_text="For prospective_client proposals (new business)"
    )
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='proposals',
        help_text="For update_client or renewal_client proposals"
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

    # Conversion Tracking (when accepted)
    converted_to_engagement = models.BooleanField(
        default=False,
        help_text="Whether this proposal has been converted to engagement/contract"
    )
    auto_create_project = models.BooleanField(
        default=True,
        help_text="Auto-create initial project when accepted"
    )
    enable_portal_on_acceptance = models.BooleanField(
        default=True,
        help_text="Enable client portal when proposal accepted (for prospective_client only)"
    )

    # Audit Fields
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_proposals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['proposal_type', 'status']),
            models.Index(fields=['prospect', 'status']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['proposal_number']),
        ]

    def clean(self):
        """Validate that proposal has either prospect OR client based on type."""
        from django.core.exceptions import ValidationError

        if self.proposal_type == 'prospective_client':
            if not self.prospect:
                raise ValidationError("Prospective client proposals must have a prospect.")
            if self.client:
                raise ValidationError("Prospective client proposals cannot have a client.")
        else:  # update_client or renewal_client
            if not self.client:
                raise ValidationError(f"{self.get_proposal_type_display()} proposals must have a client.")
            if self.prospect:
                raise ValidationError(f"{self.get_proposal_type_display()} proposals cannot have a prospect.")

    def __str__(self):
        if self.proposal_type == 'prospective_client' and self.prospect:
            return f"{self.proposal_number} - {self.prospect.company_name} (New Business)"
        elif self.client:
            return f"{self.proposal_number} - {self.client.company_name} ({self.get_proposal_type_display()})"
        return f"{self.proposal_number}"


class Contract(models.Model):
    """
    Contract (Signed Agreement) entity.

    Represents a signed contract with a client.
    Created from an accepted Proposal. Links CRM (pre-sale) to Clients (post-sale).
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

    # Relationships - UPDATED to reference clients.Client
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='contracts',
        help_text="The post-sale client this contract is with"
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
