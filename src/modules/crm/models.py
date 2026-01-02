"""
CRM Models: Lead, Prospect, Proposal, Contract, Campaign, Pipeline, Deal.

This module handles PRE-SALE operations only (Marketing & Sales).
Post-sale Client management moved to modules.clients.

Workflow: Lead → Prospect → Proposal → (Accepted) → Client (in modules.clients)
Deal Workflow: Deal → (Won) → Project conversion

TIER 0: All CRM entities MUST belong to exactly one Firm for tenant isolation.
"""

from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class Account(models.Model):
    """
    Account represents a company/organization in the CRM system (Task 3.1).
    
    Accounts are pre-sale or active business entities that can have multiple
    contacts, opportunities, and relationships. This is the "company" entity
    in the relationship graph.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    ACCOUNT_TYPE_CHOICES = [
        ("prospect", "Prospect"),
        ("customer", "Customer"),
        ("partner", "Partner"),
        ("vendor", "Vendor"),
        ("competitor", "Competitor"),
        ("other", "Other"),
    ]
    
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ]
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="accounts",
        help_text="Firm (workspace) this account belongs to"
    )
    
    # Company Information
    name = models.CharField(max_length=255, help_text="Company/Organization name")
    legal_name = models.CharField(max_length=255, blank=True, help_text="Legal entity name if different")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default="prospect")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    
    # Business Details
    industry = models.CharField(max_length=100, blank=True, help_text="Industry sector")
    website = models.URLField(blank=True, validators=[validate_safe_url])
    employee_count = models.IntegerField(null=True, blank=True, help_text="Number of employees")
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Annual revenue (if known)"
    )
    
    # Address Information
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    
    # Assignment
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_accounts",
        help_text="Primary account owner/manager"
    )
    
    # Linked entities
    parent_account = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_accounts",
        help_text="Parent account for subsidiary relationships"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_accounts",
        help_text="User who created this account"
    )
    notes = models.TextField(blank=True, help_text="Internal notes about this account")
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_account"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "status"], name="crm_account_firm_status_idx"),
            models.Index(fields=["firm", "account_type"], name="crm_account_firm_type_idx"),
            models.Index(fields=["firm", "owner"], name="crm_account_firm_owner_idx"),
            models.Index(fields=["parent_account"], name="crm_account_parent_idx"),
        ]
        unique_together = [["firm", "name"]]
    
    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"


class AccountContact(models.Model):
    """
    Contact person associated with an Account (Task 3.1).
    
    Represents individuals at an account who are points of contact.
    Similar to clients.Contact but for pre-sale accounts.
    
    TIER 0: Belongs to exactly one Firm (via account relationship).
    """
    
    # Account relationship
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="contacts",
        help_text="Account this contact belongs to"
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100, help_text="Contact's first name")
    last_name = models.CharField(max_length=100, help_text="Contact's last name")
    email = models.EmailField(help_text="Contact's email address")
    phone = models.CharField(max_length=50, blank=True, help_text="Contact's phone number")
    mobile_phone = models.CharField(max_length=50, blank=True, help_text="Contact's mobile phone number")
    
    # Professional Information
    job_title = models.CharField(max_length=200, blank=True, help_text="Job title at the account")
    department = models.CharField(max_length=100, blank=True, help_text="Department within the organization")
    
    # Contact Preferences
    is_primary_contact = models.BooleanField(
        default=False,
        help_text="Whether this is the primary contact for the account"
    )
    is_decision_maker = models.BooleanField(
        default=False,
        help_text="Whether this contact is a decision maker"
    )
    
    # Communication Preferences
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("phone", "Phone"),
            ("sms", "SMS"),
        ],
        default="email",
        help_text="Preferred method of contact"
    )
    opt_out_marketing = models.BooleanField(default=False, help_text="Opted out of marketing communications")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether this contact is active")
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_account_contacts",
        help_text="User who created this contact"
    )
    notes = models.TextField(blank=True, help_text="Internal notes about this contact")
    
    class Meta:
        db_table = "crm_account_contact"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["account", "is_active"], name="crm_acc_contact_acc_act_idx"),
            models.Index(fields=["account", "is_primary_contact"], name="crm_acc_contact_acc_pri_idx"),
            models.Index(fields=["email"], name="crm_acc_contact_email_idx"),
        ]
        unique_together = [["account", "email"]]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.account.name})"
    
    @property
    def full_name(self):
        """Return contact's full name."""
        return f"{self.first_name} {self.last_name}"


class AccountRelationship(models.Model):
    """
    Relationship graph between Accounts (Task 3.1).
    
    Tracks business relationships between different accounts such as
    parent-subsidiary, partner, vendor-client, etc.
    
    TIER 0: Belongs to exactly one Firm (via from_account relationship).
    """
    
    RELATIONSHIP_TYPE_CHOICES = [
        ("parent_subsidiary", "Parent-Subsidiary"),
        ("partnership", "Partnership"),
        ("vendor_client", "Vendor-Client"),
        ("competitor", "Competitor"),
        ("referral_source", "Referral Source"),
        ("strategic_alliance", "Strategic Alliance"),
        ("reseller", "Reseller"),
        ("other", "Other"),
    ]
    
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("ended", "Ended"),
    ]
    
    # Relationship endpoints
    from_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="relationships_from",
        help_text="Source account in the relationship"
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="relationships_to",
        help_text="Target account in the relationship"
    )
    
    # Relationship details
    relationship_type = models.CharField(
        max_length=30,
        choices=RELATIONSHIP_TYPE_CHOICES,
        help_text="Type of relationship"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    
    # Dates
    start_date = models.DateField(null=True, blank=True, help_text="When the relationship started")
    end_date = models.DateField(null=True, blank=True, help_text="When the relationship ended")
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_account_relationships",
        help_text="User who created this relationship"
    )
    notes = models.TextField(blank=True, help_text="Notes about this relationship")
    
    class Meta:
        db_table = "crm_account_relationship"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["from_account", "status"], name="crm_acc_rel_from_status_idx"),
            models.Index(fields=["to_account", "status"], name="crm_acc_rel_to_status_idx"),
            models.Index(fields=["relationship_type"], name="crm_acc_rel_type_idx"),
        ]
        unique_together = [["from_account", "to_account", "relationship_type"]]
    
    def __str__(self):
        return f"{self.from_account.name} - {self.get_relationship_type_display()} - {self.to_account.name}"
    
    def clean(self):
        """Validate relationship data."""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Prevent self-referential relationships
        if self.from_account_id == self.to_account_id:
            errors["to_account"] = "An account cannot have a relationship with itself."
        
        # Ensure both accounts belong to the same firm
        if self.from_account_id and self.to_account_id:
            if hasattr(self, "from_account") and hasattr(self, "to_account"):
                if self.from_account.firm_id != self.to_account.firm_id:
                    errors["to_account"] = "Both accounts must belong to the same firm."
        
        # Validate end_date is after start_date
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date must be after start date."
        
        if errors:
            raise ValidationError(errors)


class Activity(models.Model):
    """
    Activity Timeline entity (Simple feature 1.10).

    Tracks all interactions with leads, prospects, and clients.
    Provides a chronological activity feed for relationship management.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    ACTIVITY_TYPE_CHOICES = [
        ("call", "Phone Call"),
        ("email", "Email"),
        ("meeting", "Meeting"),
        ("note", "Note"),
        ("task", "Task"),
        ("proposal_sent", "Proposal Sent"),
        ("contract_signed", "Contract Signed"),
        ("follow_up", "Follow-up"),
        ("other", "Other"),
    ]

    DIRECTION_CHOICES = [
        ("inbound", "Inbound"),
        ("outbound", "Outbound"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="activities",
        help_text="Firm (workspace) this activity belongs to",
    )

    # Activity Details
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, help_text="Type of activity")
    direction = models.CharField(
        max_length=10, choices=DIRECTION_CHOICES, default="outbound", help_text="Direction of communication"
    )
    subject = models.CharField(max_length=255, help_text="Activity subject/title")
    description = models.TextField(blank=True, help_text="Detailed notes about the activity")
    activity_date = models.DateTimeField(help_text="When the activity occurred")

    # Relationships - Can be linked to Lead, Prospect, or Client
    lead = models.ForeignKey(
        "Lead",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activities",
        help_text="Lead this activity is associated with",
    )
    prospect = models.ForeignKey(
        "Prospect",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activities",
        help_text="Prospect this activity is associated with",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="crm_activities",
        help_text="Client this activity is associated with",
    )

    # Optional links to related objects
    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
        help_text="Campaign this activity is part of",
    )
    proposal = models.ForeignKey(
        "Proposal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
        help_text="Proposal this activity is related to",
    )

    # User tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_activities",
        help_text="User who logged this activity",
    )

    # Duration (for calls/meetings)
    duration_minutes = models.IntegerField(null=True, blank=True, help_text="Duration in minutes (for calls/meetings)")

    # Follow-up
    requires_follow_up = models.BooleanField(default=False, help_text="Whether this activity requires follow-up")
    follow_up_date = models.DateField(null=True, blank=True, help_text="When to follow up")
    follow_up_completed = models.BooleanField(default=False, help_text="Whether follow-up was completed")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "crm_activities"
        ordering = ["-activity_date"]
        indexes = [
            models.Index(fields=["firm", "-activity_date"]),  # TIER 0: Firm scoping, name="crm_fir_act_idx")
            models.Index(fields=["firm", "activity_type"]),  # TIER 0: Firm scoping, name="crm_fir_act_idx")
            models.Index(fields=["lead", "-activity_date"], name="crm_lea_act_idx"),
            models.Index(fields=["prospect", "-activity_date"], name="crm_pro_act_idx"),
            models.Index(fields=["client", "-activity_date"], name="crm_cli_act_idx"),
            models.Index(fields=["created_by", "-activity_date"], name="crm_cre_act_idx"),
        ]
        verbose_name_plural = "Activities"

    def __str__(self) -> str:
        entity = "Unknown"
        if self.lead:
            entity = f"Lead: {self.lead.company_name}"
        elif self.prospect:
            entity = f"Prospect: {self.prospect.company_name}"
        elif self.client:
            entity = f"Client: {self.client.company_name}"
        return f"{self.get_activity_type_display()} - {entity} - {self.activity_date.date()}"

    def clean(self) -> None:
        """Validate that activity is linked to at least one entity."""
        from django.core.exceptions import ValidationError

        if not any([self.lead_id, self.prospect_id, self.client_id]):
            raise ValidationError("Activity must be associated with at least one entity (Lead, Prospect, or Client)")


class Lead(models.Model):
    """
    Marketing-captured prospect (Pre-Sale).

    Represents initial contact before qualification.
    When qualified, converts to Prospect for sales pipeline.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("new", "New Lead"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified - Moving to Sales"),
        ("converted", "Converted to Prospect"),
        ("lost", "Lost"),
    ]

    SOURCE_CHOICES = [
        ("website", "Website Form"),
        ("referral", "Referral"),
        ("campaign", "Marketing Campaign"),
        ("cold_outreach", "Cold Outreach"),
        ("event", "Event/Conference"),
        ("partnership", "Partnership"),
        ("other", "Other"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm", on_delete=models.CASCADE, related_name="leads", help_text="Firm (workspace) this lead belongs to"
    )

    # Company Information
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True, validators=[validate_safe_url])

    # Contact Information
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    contact_title = models.CharField(max_length=100, blank=True)

    # Lead Tracking
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default="website")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    lead_score = models.IntegerField(default=0, help_text="Automated or manual lead scoring (0-100)")

    # Campaign Tracking
    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
        help_text="Marketing campaign that generated this lead",
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_leads",
        help_text="Sales rep assigned to this lead",
    )

    # Timeline
    captured_date = models.DateField(auto_now_add=True)
    first_contacted = models.DateField(null=True, blank=True)
    qualified_date = models.DateField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "crm_leads"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping, name="crm_fir_sta_idx")
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping, name="crm_fir_cre_idx")
            models.Index(fields=["firm", "assigned_to"]),  # TIER 0: Firm scoping, name="crm_fir_ass_idx")
            models.Index(fields=["campaign"], name="crm_cam_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.company_name} - {self.get_status_display()}"

    def calculate_lead_score(self) -> int:
        """
        Calculate lead score based on various factors (0-100).

        Simple scoring algorithm:
        - Has contact email: +20
        - Has phone: +10
        - Has website: +10
        - From campaign: +15
        - Contacted status: +20
        - Qualified status: +25
        - Industry filled: +10
        - Assigned to rep: +10

        Returns:
            int: Calculated lead score (0-100)
        """
        score = 0

        # Contact completeness
        if self.contact_email:
            score += 20
        if self.contact_phone:
            score += 10
        if self.website:
            score += 10
        if self.industry:
            score += 10

        # Campaign source (marketing qualified)
        if self.campaign_id:
            score += 15

        # Status progression
        if self.status == "contacted":
            score += 20
        elif self.status == "qualified":
            score += 25

        # Assignment (shows active pursuit)
        if self.assigned_to_id:
            score += 10

        return min(score, 100)  # Cap at 100

    def update_lead_score(self) -> None:
        """Update and save the lead_score field."""
        self.lead_score = self.calculate_lead_score()
        self.save(update_fields=["lead_score"])


class Prospect(models.Model):
    """
    Sales pipeline prospect (Pre-Sale).

    Active sales opportunity after lead qualification.
    Can have multiple proposals. Converts to Client when won.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STAGE_CHOICES = [
        ("discovery", "Discovery"),
        ("needs_analysis", "Needs Analysis"),
        ("proposal", "Proposal Sent"),
        ("negotiation", "Negotiation"),
        ("won", "Won - Converting to Client"),
        ("lost", "Lost"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="prospects",
        help_text="Firm (workspace) this prospect belongs to",
    )

    # Origin
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prospects",
        help_text="Original lead that created this prospect",
    )

    # Company Information
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True, validators=[validate_safe_url])
    employee_count = models.IntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, help_text="Estimated annual revenue"
    )

    # Contact Information
    primary_contact_name = models.CharField(max_length=255)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=50, blank=True)
    primary_contact_title = models.CharField(max_length=100, blank=True)
    
    # GDPR/Privacy Compliance (ASSESS-L19.2) - For prospects/leads
    marketing_opt_in = models.BooleanField(
        default=False,
        help_text="Has the prospect opted in to receive marketing communications?"
    )
    consent_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When consent was given (GDPR requirement)"
    )
    consent_source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Source of consent (e.g., 'lead_form', 'email_campaign', 'website')"
    )

    # Address
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="USA")

    # Pipeline Tracking
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="discovery", help_text="Current pipeline stage")
    probability = models.IntegerField(default=50, help_text="Win probability percentage (0-100)")

    # Financial Forecast
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, help_text="Estimated deal value")
    close_date_estimate = models.DateField(help_text="Expected close date")

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_prospects",
        help_text="Account executive assigned",
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

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "crm_prospects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "stage"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "assigned_to"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "close_date_estimate"]),  # TIER 0: Firm scoping
        ]
        # SECURITY: Company names must be unique per firm, not globally (ASSESS-D4.4b)
        unique_together = [["firm", "company_name"]]

    def __str__(self) -> str:
        return f"{self.company_name} - {self.get_stage_display()}"


class Campaign(models.Model):
    """
    Marketing & Sales Campaign tracking.

    Tracks campaigns for both new business acquisition AND existing client engagement:
    - Lead generation (new prospects)
    - Client renewals and upsells
    - Client annual reviews

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    TYPE_CHOICES = [
        ("email", "Email Campaign"),
        ("webinar", "Webinar"),
        ("content", "Content Marketing"),
        ("event", "Event/Conference"),
        ("social", "Social Media"),
        ("partnership", "Partnership"),
        ("renewal", "Renewal Campaign"),
        ("annual_review", "Annual Review"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="campaigns",
        help_text="Firm (workspace) this campaign belongs to",
    )

    # Campaign Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planning")

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()

    # Budget
    budget = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # Target Audience - Can target BOTH prospects AND clients
    targeted_clients = models.ManyToManyField(
        "clients.Client",
        blank=True,
        related_name="targeted_campaigns",
        help_text="Existing clients targeted by this campaign (renewals, upsells, etc.)",
    )

    # Performance Metrics - New Business
    target_leads = models.IntegerField(default=0, help_text="Target number of new leads")
    leads_generated = models.IntegerField(default=0, help_text="Auto-calculated from Lead.campaign foreign key")
    opportunities_created = models.IntegerField(default=0, help_text="Number of Prospects created from campaign leads")

    # Performance Metrics - Client Engagement
    clients_contacted = models.IntegerField(default=0, help_text="Number of existing clients contacted")
    renewal_proposals_sent = models.IntegerField(default=0, help_text="Number of renewal/upsell proposals generated")
    renewals_won = models.IntegerField(default=0, help_text="Number of successful renewals/upsells")

    # Financial Metrics
    revenue_generated = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Revenue from won deals (new + renewal) attributed to this campaign",
    )

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="owned_campaigns"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "crm_campaigns"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping, name="crm_fir_sta_idx")
            models.Index(fields=["firm", "-start_date"]),  # TIER 0: Firm scoping, name="crm_fir_sta_idx")
            models.Index(fields=["firm", "type"]),  # TIER 0: Firm scoping, name="crm_fir_typ_idx")
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_type_display()})"


class Proposal(models.Model):
    """
    Proposal (Quote/Engagement Letter) entity.

    Handles both new business and existing client proposals:
    - prospective_client: New business (links to Prospect)
    - update_client: Expansion/upsell to existing Client
    - renewal_client: Renewal for existing Client

    When accepted, becomes an Engagement Letter (Contract).

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("under_review", "Under Review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]

    TYPE_CHOICES = [
        ("prospective_client", "Prospective Client - New Business"),
        ("update_client", "Update Client - Expansion/Upsell"),
        ("renewal_client", "Renewal Client - Contract Renewal"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="proposals",
        help_text="Firm (workspace) this proposal belongs to",
    )

    # Proposal Type
    proposal_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="prospective_client",
        help_text="Type of proposal: new business, expansion, or renewal",
    )

    # Relationships - EITHER prospect OR client (based on type)
    prospect = models.ForeignKey(
        Prospect,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="proposals",
        help_text="For prospective_client proposals (new business)",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="proposals",
        help_text="For update_client or renewal_client proposals",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_proposals"
    )

    # Proposal Details
    proposal_number = models.CharField(max_length=50)  # TIER 0: Unique per firm (see Meta)
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Scope of work, deliverables, timeline")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Financial Terms
    total_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3, default="USD")

    # Timeline
    valid_until = models.DateField(help_text="Proposal expiration date")
    estimated_start_date = models.DateField(null=True, blank=True)
    estimated_end_date = models.DateField(null=True, blank=True)

    # Conversion Tracking (when accepted)
    converted_to_engagement = models.BooleanField(
        default=False, help_text="Whether this proposal has been converted to engagement/contract"
    )
    auto_create_project = models.BooleanField(default=True, help_text="Auto-create initial project when accepted")
    enable_portal_on_acceptance = models.BooleanField(
        default=True, help_text="Enable client portal when proposal accepted (for prospective_client only)"
    )

    # Audit Fields
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "crm_proposals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "proposal_type", "status"]),  # TIER 0: Firm scoping, name="crm_fir_pro_sta_idx")
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping, name="crm_fir_cre_idx")
            models.Index(fields=["firm", "prospect", "status"]),  # TIER 0: Firm scoping, name="crm_fir_pro_sta_idx")
            models.Index(fields=["firm", "client", "status"]),  # TIER 0: Firm scoping, name="crm_fir_cli_sta_idx")
            models.Index(fields=["firm", "proposal_number"]),  # TIER 0: Firm scoping, name="crm_fir_pro_idx")
        ]
        # TIER 0: Proposal numbers must be unique within a firm (not globally)
        unique_together = [["firm", "proposal_number"]]

    def __str__(self) -> str:
        if self.proposal_type == "prospective_client" and self.prospect:
            return f"{self.proposal_number} - {self.prospect.company_name} (New Business)"
        elif self.client:
            return f"{self.proposal_number} - {self.client.company_name} ({self.get_proposal_type_display()})"
        return f"{self.proposal_number}"

    def clean(self) -> None:
        """Validate that proposal has either prospect OR client based on type."""
        from django.core.exceptions import ValidationError

        if self.proposal_type == "prospective_client":
            if not self.prospect:
                raise ValidationError("Prospective client proposals must have a prospect.")
            if self.client:
                raise ValidationError("Prospective client proposals cannot have a client.")
        else:  # update_client or renewal_client
            if not self.client:
                raise ValidationError(f"{self.get_proposal_type_display()} proposals must have a client.")
            if self.prospect:
                raise ValidationError(f"{self.get_proposal_type_display()} proposals cannot have a prospect.")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Prevent changing proposal value once a related contract is signed.
        """
        from django.core.exceptions import ValidationError

        if self.pk:
            previous_value = Proposal.objects.filter(pk=self.pk).values_list("total_value", flat=True).first()
            if previous_value is not None and self.total_value != previous_value:
                if self.contracts.filter(signed_date__isnull=False).exists():
                    raise ValidationError("Cannot modify total value for proposals linked to signed contracts.")

        super().save(*args, **kwargs)


class Contract(models.Model):
    """
    Contract (Signed Agreement) entity.

    Represents a signed contract with a client.
    Created from an accepted Proposal. Links CRM (pre-sale) to Clients (post-sale).

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("terminated", "Terminated"),
        ("on_hold", "On Hold"),
    ]

    PAYMENT_TERMS_CHOICES = [
        ("net_15", "Net 15"),
        ("net_30", "Net 30"),
        ("net_45", "Net 45"),
        ("net_60", "Net 60"),
        ("due_on_receipt", "Due on Receipt"),
        ("milestone", "Milestone-based"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="contracts",
        help_text="Firm (workspace) this contract belongs to",
    )

    # Relationships - UPDATED to reference clients.Client
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="contracts",
        help_text="The post-sale client this contract is with",
    )
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts",
        help_text="The proposal that led to this contract (if applicable)",
    )
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="signed_contracts",
        help_text="The consultant who signed this contract",
    )

    # Contract Details
    contract_number = models.CharField(max_length=50)  # TIER 0: Unique per firm (see Meta)
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Statement of work, deliverables, terms")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Financial Terms
    total_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3, default="USD")
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default="net_30")

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    signed_date = models.DateField(null=True, blank=True)

    # Contract Documents
    contract_file_url = models.URLField(blank=True, help_text="Link to signed contract PDF in S3")

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    def clean(self):
        """
        Validate contract data before saving.

        Ensures that active contracts have required signature information.
        """
        from django.core.exceptions import ValidationError

        super().clean()

        # Active contracts must have signature details
        if self.status == "active":
            if not self.signed_date:
                raise ValidationError({
                    "signed_date": "Active contracts must have a signed date."
                })
            if not self.signed_by:
                raise ValidationError({
                    "signed_by": "Active contracts must have a signer."
                })

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Enforce immutability for signature fields once set.
        """
        from django.core.exceptions import ValidationError

        if self.pk:
            previous = Contract.objects.filter(pk=self.pk).values("signed_date", "signed_by_id").first()
            if previous:
                if previous["signed_date"] and self.signed_date != previous["signed_date"]:
                    raise ValidationError("Signed date is immutable once set.")
                if previous["signed_by_id"] and self.signed_by_id != previous["signed_by_id"]:
                    raise ValidationError("Signed by is immutable once set.")

        super().save(*args, **kwargs)

    class Meta:
        db_table = "crm_contracts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping, name="crm_fir_sta_idx")
            models.Index(fields=["firm", "client", "status"]),  # TIER 0: Firm scoping, name="crm_fir_cli_sta_idx")
            models.Index(fields=["firm", "contract_number"]),  # TIER 0: Firm scoping, name="crm_fir_con_idx")
            models.Index(fields=["firm", "start_date", "end_date"]),  # TIER 0: Firm scoping, name="crm_fir_sta_end_idx")
        ]
        # TIER 0: Contract numbers must be unique within a firm (not globally)
        unique_together = [["firm", "contract_number"]]

    def __str__(self) -> str:
        return f"{self.contract_number} - {self.client.company_name}"


class IntakeForm(models.Model):
    """
    Intake Form for lead qualification (Task 3.4).
    
    Customizable forms to collect information from prospects and qualify them
    based on predefined criteria. Can be embedded on websites or sent as links.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="intake_forms",
        help_text="Firm this form belongs to"
    )
    
    # Form Details
    name = models.CharField(
        max_length=200,
        help_text="Internal name for this form"
    )
    title = models.CharField(
        max_length=255,
        help_text="Form title shown to users"
    )
    description = models.TextField(
        blank=True,
        help_text="Form description/instructions"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )
    
    # Configuration
    qualification_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic lead qualification based on responses"
    )
    qualification_threshold = models.IntegerField(
        default=50,
        help_text="Minimum score (0-100) to qualify as a prospect"
    )
    auto_create_lead = models.BooleanField(
        default=True,
        help_text="Automatically create Lead record from submission"
    )
    auto_create_prospect = models.BooleanField(
        default=False,
        help_text="Automatically create Prospect record if qualified"
    )
    
    # Assignment
    default_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_intake_forms",
        help_text="Default owner for leads created from this form"
    )
    
    # Notifications
    notify_on_submission = models.BooleanField(
        default=True,
        help_text="Send notification when form is submitted"
    )
    notification_emails = models.TextField(
        blank=True,
        help_text="Comma-separated list of emails to notify (in addition to owner)"
    )
    
    # Thank You Page
    thank_you_title = models.CharField(
        max_length=255,
        default="Thank You!",
        help_text="Title shown after submission"
    )
    thank_you_message = models.TextField(
        default="We've received your information and will be in touch soon.",
        help_text="Message shown after submission"
    )
    redirect_url = models.URLField(
        blank=True,
        validators=[validate_safe_url],
        help_text="Optional URL to redirect to after submission"
    )
    
    # Metadata
    submission_count = models.IntegerField(
        default=0,
        help_text="Total number of submissions"
    )
    qualified_count = models.IntegerField(
        default=0,
        help_text="Number of qualified submissions"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_intake_forms",
        help_text="User who created this form"
    )
    
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_intake_forms"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="crm_intake_firm_status_idx"),
            models.Index(fields=["firm", "created_at"], name="crm_intake_firm_created_idx"),
        ]
        verbose_name = "Intake Form"
        verbose_name_plural = "Intake Forms"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class IntakeFormField(models.Model):
    """
    Field definition for IntakeForm (Task 3.4).
    
    Defines individual fields in an intake form with qualification scoring.
    """
    
    FIELD_TYPE_CHOICES = [
        ("text", "Short Text"),
        ("textarea", "Long Text"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("url", "URL"),
        ("number", "Number"),
        ("select", "Single Select"),
        ("multiselect", "Multi Select"),
        ("checkbox", "Checkbox"),
        ("date", "Date"),
        ("file", "File Upload"),
    ]
    
    # Relationships
    form = models.ForeignKey(
        IntakeForm,
        on_delete=models.CASCADE,
        related_name="fields",
        help_text="Form this field belongs to"
    )
    
    # Field Configuration
    label = models.CharField(
        max_length=255,
        help_text="Field label shown to users"
    )
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default="text"
    )
    placeholder = models.CharField(
        max_length=255,
        blank=True,
        help_text="Placeholder text"
    )
    help_text = models.TextField(
        blank=True,
        help_text="Help text shown below field"
    )
    required = models.BooleanField(
        default=False,
        help_text="Is this field required?"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    
    # Options for select/multiselect
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="Options for select/multiselect fields (list of strings)"
    )
    
    # Qualification Scoring
    scoring_enabled = models.BooleanField(
        default=False,
        help_text="Enable qualification scoring for this field"
    )
    scoring_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Scoring rules: {value: points, ...}"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    
    class Meta:
        db_table = "crm_intake_form_fields"
        ordering = ["form", "order", "id"]
        indexes = [
            models.Index(fields=["form", "order"], name="crm_intake_field_order_idx"),
        ]
        verbose_name = "Intake Form Field"
        verbose_name_plural = "Intake Form Fields"
    
    def __str__(self) -> str:
        return f"{self.form.name} - {self.label}"


class IntakeFormSubmission(models.Model):
    """
    Submission of an IntakeForm (Task 3.4).
    
    Stores responses to intake forms along with qualification score
    and automatically creates Lead/Prospect records based on configuration.
    
    TIER 0: Belongs to firm through IntakeForm relationship.
    """
    
    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("qualified", "Qualified"),
        ("disqualified", "Disqualified"),
        ("converted", "Converted to Lead/Prospect"),
        ("spam", "Marked as Spam"),
    ]
    
    # Relationships
    form = models.ForeignKey(
        IntakeForm,
        on_delete=models.CASCADE,
        related_name="submissions",
        help_text="Form that was submitted"
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intake_submissions",
        help_text="Lead created from this submission (if applicable)"
    )
    prospect = models.ForeignKey(
        Prospect,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intake_submissions",
        help_text="Prospect created from this submission (if qualified)"
    )
    
    # Response Data
    responses = models.JSONField(
        default=dict,
        help_text="Field responses: {field_id: value, ...}"
    )
    
    # Qualification
    qualification_score = models.IntegerField(
        default=0,
        help_text="Calculated qualification score (0-100)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    is_qualified = models.BooleanField(
        default=False,
        help_text="Whether submission meets qualification threshold"
    )
    
    # Submitter Information
    submitter_email = models.EmailField(
        blank=True,
        help_text="Email address from submission"
    )
    submitter_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name from submission"
    )
    submitter_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Phone number from submission"
    )
    submitter_company = models.CharField(
        max_length=255,
        blank=True,
        help_text="Company name from submission"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of submitter"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    referrer = models.URLField(
        blank=True,
        validators=[validate_safe_url],
        help_text="Referring URL"
    )
    
    # Review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_intake_submissions",
        help_text="User who reviewed this submission"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When submission was reviewed"
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Internal notes from review"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    
    class Meta:
        db_table = "crm_intake_form_submissions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["form", "status"], name="crm_intake_sub_status_idx"),
            models.Index(fields=["form", "created_at"], name="crm_intake_sub_created_idx"),
            models.Index(fields=["form", "is_qualified"], name="crm_intake_sub_qualified_idx"),
            models.Index(fields=["submitter_email"], name="crm_intake_sub_email_idx"),
        ]
        verbose_name = "Intake Form Submission"
        verbose_name_plural = "Intake Form Submissions"
    
    def __str__(self) -> str:
        return f"{self.form.name} - {self.submitter_email or 'Anonymous'} ({self.created_at})"
    
    def calculate_qualification_score(self) -> int:
        """Calculate qualification score based on field responses and scoring rules."""
        total_score = 0
        max_score = 0
        
        # Iterate through form fields with scoring enabled
        for field in self.form.fields.filter(scoring_enabled=True):
            if not field.scoring_rules:
                continue
            
            # Get the response for this field
            field_id = str(field.id)
            response_value = self.responses.get(field_id)
            
            if response_value is None:
                continue
            
            # Calculate score based on scoring rules
            # Scoring rules format: {value: points, ...} or {"ranges": [{"min": 0, "max": 10, "points": 5}]}
            if isinstance(field.scoring_rules, dict):
                # Check for exact match
                if str(response_value) in field.scoring_rules:
                    points = field.scoring_rules[str(response_value)]
                    total_score += points
                    # Safely get max score
                    if field.scoring_rules.values():
                        max_score += max(field.scoring_rules.values())
                # Check for range-based scoring (for number fields)
                elif "ranges" in field.scoring_rules:
                    try:
                        value = float(response_value)
                        for range_def in field.scoring_rules.get("ranges", []):
                            min_val = range_def.get("min", float("-inf"))
                            max_val = range_def.get("max", float("inf"))
                            if min_val <= value <= max_val:
                                total_score += range_def.get("points", 0)
                                # Track max possible score from ranges
                                max_score += range_def.get("points", 0)
                                break
                    except (ValueError, TypeError):
                        pass
        
        # Normalize to 0-100 scale
        if max_score > 0:
            normalized_score = int((total_score / max_score) * 100)
        else:
            normalized_score = 0
        
        self.qualification_score = normalized_score
        self.is_qualified = normalized_score >= self.form.qualification_threshold
        
        if self.is_qualified and self.status == "pending":
            self.status = "qualified"
        elif not self.is_qualified and self.status == "pending":
            self.status = "disqualified"
        
        self.save()
        return normalized_score
    
    def create_lead(self) -> "Lead":
        """Create a Lead record from this submission."""
        if self.lead:
            return self.lead
        
        # Extract information from responses
        email = self.submitter_email
        name = self.submitter_name
        phone = self.submitter_phone
        company = self.submitter_company
        
        # Safely parse name into first and last
        name_parts = name.split() if name else []
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Create lead
        lead = Lead.objects.create(
            firm=self.form.firm,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            company=company,
            source="intake_form",
            status="new",
            assigned_to=self.form.default_owner,
            notes=f"Created from intake form: {self.form.name}\nQualification Score: {self.qualification_score}",
        )
        
        self.lead = lead
        self.status = "converted"
        self.save()
        
        # Update form submission count
        self.form.submission_count += 1
        if self.is_qualified:
            self.form.qualified_count += 1
        self.form.save()
        
        return lead


# ============================================================================
# CPQ (Configure-Price-Quote) System - Task 3.5
# ============================================================================


class Product(models.Model):
    """
    Product model for CPQ system (Task 3.5).
    
    Represents a product or service that can be configured and quoted.
    Products can be simple (no configuration) or complex (multiple options).
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    PRODUCT_TYPE_CHOICES = [
        ("service", "Service"),
        ("product", "Product"),
        ("subscription", "Subscription"),
        ("bundle", "Bundle"),
    ]
    
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ]
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="cpq_products",
        help_text="Firm (workspace) this product belongs to"
    )
    
    # Product Identity
    code = models.CharField(
        max_length=100,
        help_text="Unique product code/SKU"
    )
    name = models.CharField(max_length=255, help_text="Product name")
    description = models.TextField(blank=True, help_text="Product description")
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default="service"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Base price before configuration"
    )
    currency = models.CharField(max_length=3, default="USD", help_text="Currency code (ISO 4217)")
    
    # Configuration
    is_configurable = models.BooleanField(
        default=False,
        help_text="Whether this product has configurable options"
    )
    configuration_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON schema defining configuration rules and dependencies"
    )
    
    # Metadata
    category = models.CharField(max_length=100, blank=True, help_text="Product category")
    tags = models.JSONField(default=list, blank=True, help_text="Product tags for filtering")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_products",
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_product"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "status"], name="crm_prod_firm_status_idx"),
            models.Index(fields=["firm", "code"], name="crm_prod_firm_code_idx"),
            models.Index(fields=["firm", "product_type"], name="crm_prod_firm_type_idx"),
        ]
        unique_together = [["firm", "code"]]
    
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class ProductOption(models.Model):
    """
    ProductOption model for CPQ system (Task 3.5).
    
    Represents a configurable option for a product (e.g., size, color, features).
    Options can affect pricing and have dependencies on other options.
    
    TIER 0: Inherits firm from product.
    """
    
    OPTION_TYPE_CHOICES = [
        ("single_select", "Single Select"),
        ("multi_select", "Multi Select"),
        ("text", "Text Input"),
        ("number", "Number Input"),
        ("boolean", "Boolean"),
    ]
    
    # Parent product
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="options",
        help_text="Product this option belongs to"
    )
    
    # Option Identity
    code = models.CharField(max_length=100, help_text="Option code")
    label = models.CharField(max_length=255, help_text="Display label")
    description = models.TextField(blank=True, help_text="Option description")
    option_type = models.CharField(
        max_length=20,
        choices=OPTION_TYPE_CHOICES,
        default="single_select"
    )
    
    # Configuration
    required = models.BooleanField(default=False, help_text="Whether this option is required")
    display_order = models.IntegerField(default=0, help_text="Display order in UI")
    
    # Values (for select options)
    values = models.JSONField(
        default=list,
        blank=True,
        help_text="Available values for select options: [{value, label, price_modifier}]"
    )
    
    # Pricing Impact
    price_modifier = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Fixed price modifier (added to base price)"
    )
    price_multiplier = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=Decimal("1.0000"),
        validators=[MinValueValidator(Decimal("0.0000"))],
        help_text="Price multiplier (applied to base price)"
    )
    
    # Dependencies and Rules
    dependency_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rules defining when this option is available based on other options"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "crm_product_option"
        ordering = ["display_order", "label"]
        indexes = [
            models.Index(fields=["product", "display_order"], name="crm_prod_opt_prod_ord_idx"),
            models.Index(fields=["product", "code"], name="crm_prod_opt_prod_code_idx"),
        ]
        unique_together = [["product", "code"]]
    
    def __str__(self) -> str:
        return f"{self.product.code} - {self.label}"


class ProductConfiguration(models.Model):
    """
    ProductConfiguration model for CPQ system (Task 3.5).
    
    Represents a specific configuration of a product with selected options.
    Stores the configuration choices and calculated pricing.
    
    TIER 0: Inherits firm from product.
    """
    
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("validated", "Validated"),
        ("quoted", "Quoted"),
    ]
    
    # Product reference
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="configurations",
        help_text="Product being configured"
    )
    
    # Configuration Data
    configuration_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional name for this configuration"
    )
    selected_options = models.JSONField(
        default=dict,
        help_text="Selected options: {option_code: value}"
    )
    
    # Pricing Calculation
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Base price at time of configuration"
    )
    configuration_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total price after applying configuration"
    )
    price_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed price breakdown: {base, options, discounts, total}"
    )
    
    # Discount
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Discount percentage applied to configuration"
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Calculated discount amount"
    )
    
    # Validation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="Validation errors if configuration is invalid"
    )
    
    # Quote Reference (if this configuration becomes a quote)
    quote = models.ForeignKey(
        "pricing.Quote",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_configurations",
        help_text="Quote created from this configuration"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_configurations",
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "crm_product_configuration"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"], name="crm_prod_cfg_prod_cre_idx"),
            models.Index(fields=["product", "status"], name="crm_prod_cfg_prod_sta_idx"),
            models.Index(fields=["quote"], name="crm_prod_cfg_quote_idx"),
        ]
    
    def __str__(self) -> str:
        name = self.configuration_name or f"Configuration {self.pk}"
        return f"{self.product.code} - {name}"
    
    def calculate_price(self) -> Decimal:
        """
        Calculate the total price based on base price and selected options.
        
        Returns:
            Calculated configuration price
        """
        total_price = self.base_price
        option_adjustments = Decimal("0.00")
        multiplier = Decimal("1.0000")
        breakdown = {
            "base_price": float(self.base_price),
            "options": [],
            "subtotal": 0,
            "discount_percentage": float(self.discount_percentage),
            "discount_amount": 0,
            "total": 0,
        }
        
        # Apply option pricing
        for option_code, value in self.selected_options.items():
            try:
                option = self.product.options.get(code=option_code)
                
                # Apply fixed price modifier
                if option.price_modifier != Decimal("0.00"):
                    option_adjustments += option.price_modifier
                    breakdown["options"].append({
                        "option": option_code,
                        "label": option.label,
                        "type": "modifier",
                        "amount": float(option.price_modifier),
                    })
                
                # Apply price multiplier
                if option.price_multiplier != Decimal("1.0000"):
                    multiplier *= option.price_multiplier
                    breakdown["options"].append({
                        "option": option_code,
                        "label": option.label,
                        "type": "multiplier",
                        "amount": float(option.price_multiplier),
                    })
                
                # Check for value-specific pricing (in select options)
                if option.option_type in ["single_select", "multi_select"]:
                    for val_obj in option.values:
                        if val_obj.get("value") == value:
                            val_price = Decimal(str(val_obj.get("price_modifier", 0)))
                            if val_price != Decimal("0.00"):
                                option_adjustments += val_price
                                breakdown["options"].append({
                                    "option": option_code,
                                    "label": f"{option.label}: {val_obj.get('label', value)}",
                                    "type": "value_modifier",
                                    "amount": float(val_price),
                                })
            except ProductOption.DoesNotExist:
                pass
        
        # Calculate subtotal
        subtotal = (total_price + option_adjustments) * multiplier
        breakdown["subtotal"] = float(subtotal)
        
        # Apply discount
        discount_amount = subtotal * (self.discount_percentage / Decimal("100.00"))
        breakdown["discount_amount"] = float(discount_amount)
        self.discount_amount = discount_amount
        
        # Calculate final total
        final_total = subtotal - discount_amount
        breakdown["total"] = float(final_total)
        
        self.price_breakdown = breakdown
        return final_total
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """
        Validate the configuration against product rules and dependencies.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required options
        required_options = self.product.options.filter(required=True)
        for option in required_options:
            if option.code not in self.selected_options:
                errors.append(f"Required option '{option.label}' is missing")
        
        # Check option dependencies
        for option_code, value in self.selected_options.items():
            try:
                option = self.product.options.get(code=option_code)
                if option.dependency_rules:
                    # Evaluate dependency rules
                    dependencies_met = self._evaluate_dependencies(option.dependency_rules)
                    if not dependencies_met:
                        errors.append(
                            f"Option '{option.label}' dependencies not met: {option.dependency_rules}"
                        )
            except ProductOption.DoesNotExist:
                errors.append(f"Invalid option code: {option_code}")
        
        is_valid = len(errors) == 0
        self.validation_errors = errors
        self.status = "validated" if is_valid else "draft"
        
        return is_valid, errors
    
    def _evaluate_dependencies(self, rules: dict) -> bool:
        """
        Evaluate dependency rules against selected options.
        
        Args:
            rules: Dictionary of dependency rules
            
        Returns:
            True if dependencies are met, False otherwise
        """
        if not rules:
            return True
        
        # Simple implementation: check if required options are present
        required = rules.get("requires", [])
        for req in required:
            if isinstance(req, dict):
                option_code = req.get("option")
                required_value = req.get("value")
                if option_code not in self.selected_options:
                    return False
                if required_value and self.selected_options[option_code] != required_value:
                    return False
            elif isinstance(req, str):
                if req not in self.selected_options:
                    return False
        
        return True
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to calculate price before saving."""
        # Set base price from product if not set
        if not self.base_price:
            self.base_price = self.product.base_price
        
        # Calculate configuration price
        self.configuration_price = self.calculate_price()
        
        super().save(*args, **kwargs)


class Pipeline(models.Model):
    """
    Pipeline model with configurable stages (DEAL-1).
    
    Represents a customizable sales pipeline with stages that deals progress through.
    Each firm can have multiple pipelines for different types of deals.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="pipelines",
        help_text="Firm (workspace) this pipeline belongs to"
    )
    
    # Pipeline Details
    name = models.CharField(max_length=255, help_text="Pipeline name (e.g., 'Sales', 'Consulting', 'Enterprise')")
    description = models.TextField(blank=True, help_text="Pipeline description and purpose")
    is_active = models.BooleanField(default=True, help_text="Whether this pipeline is currently active")
    is_default = models.BooleanField(default=False, help_text="Whether this is the default pipeline for new deals")
    
    # Ordering
    display_order = models.IntegerField(default=0, help_text="Display order for sorting pipelines")
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_pipelines",
        help_text="User who created this pipeline"
    )
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_pipelines"
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="crm_pip_firm_active_idx"),
            models.Index(fields=["firm", "is_default"], name="crm_pip_firm_default_idx"),
        ]
        unique_together = [["firm", "name"]]
    
    def __str__(self) -> str:
        return f"{self.name}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure only one default pipeline per firm."""
        if self.is_default:
            # Use database transaction to prevent race conditions
            from django.db import transaction
            with transaction.atomic():
                # Lock the rows to prevent concurrent updates
                Pipeline.objects.select_for_update().filter(
                    firm=self.firm, 
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class PipelineStage(models.Model):
    """
    Pipeline Stage model (DEAL-1).
    
    Represents a stage within a pipeline. Stages have a specific order
    and probability associated with them.
    
    TIER 0: Belongs to exactly one Firm via Pipeline relationship.
    """
    
    # Pipeline relationship
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="stages",
        help_text="Pipeline this stage belongs to"
    )
    
    # Stage Details
    name = models.CharField(max_length=100, help_text="Stage name (e.g., 'Discovery', 'Proposal', 'Negotiation')")
    description = models.TextField(blank=True, help_text="Stage description")
    
    # Stage Configuration
    probability = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Default win probability percentage (0-100) for deals in this stage"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this stage is currently active")
    is_closed_won = models.BooleanField(default=False, help_text="Mark as won stage")
    is_closed_lost = models.BooleanField(default=False, help_text="Mark as lost stage")
    
    # Ordering
    display_order = models.IntegerField(default=0, help_text="Display order within the pipeline")
    
    # Automation (future)
    auto_tasks = models.JSONField(
        default=list,
        blank=True,
        help_text="Tasks to auto-create when deal enters this stage"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "crm_pipeline_stages"
        ordering = ["pipeline", "display_order", "name"]
        indexes = [
            models.Index(fields=["pipeline", "display_order"], name="crm_pip_stg_pip_ord_idx"),
            models.Index(fields=["pipeline", "is_active"], name="crm_pip_stg_pip_act_idx"),
        ]
        unique_together = [["pipeline", "name"]]
    
    def __str__(self) -> str:
        return f"{self.pipeline.name} - {self.name}"
    
    @property
    def firm(self):
        """Get the firm through the pipeline relationship."""
        return self.pipeline.firm


class Deal(models.Model):
    """
    Deal model with value, probability, and associations (DEAL-1).
    
    Represents a sales opportunity/deal that progresses through pipeline stages.
    More flexible than Prospect - can be associated with Accounts, Contacts, 
    and eventually converted to Projects.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="deals",
        help_text="Firm (workspace) this deal belongs to"
    )
    
    # Pipeline & Stage
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.PROTECT,
        related_name="deals",
        help_text="Pipeline this deal belongs to"
    )
    stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.PROTECT,
        related_name="deals",
        help_text="Current stage in the pipeline"
    )
    
    # Deal Details
    name = models.CharField(max_length=255, help_text="Deal name/title")
    description = models.TextField(blank=True, help_text="Deal description and notes")
    
    # Associations (optional - can have account, contact, or both)
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        help_text="Associated account/company"
    )
    contact = models.ForeignKey(
        AccountContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        help_text="Primary contact for this deal"
    )
    
    # Financial Details
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Deal value/amount"
    )
    currency = models.CharField(max_length=3, default="USD")
    probability = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Win probability percentage (0-100)"
    )
    weighted_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Auto-calculated: value * probability / 100"
    )
    
    # Timeline
    expected_close_date = models.DateField(help_text="Expected close date")
    actual_close_date = models.DateField(null=True, blank=True, help_text="Actual close date when won/lost")
    
    # Assignment & Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_deals",
        help_text="Primary deal owner"
    )
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="team_deals",
        help_text="Additional team members working on this deal"
    )
    
    # Deal Splitting (DEAL-6) - for multiple owners
    split_percentage = models.JSONField(
        default=dict,
        blank=True,
        help_text="Split percentages for multiple owners {user_id: percentage}"
    )
    
    # Source Tracking
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Lead source (e.g., 'Website', 'Referral', 'Cold Call')"
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        help_text="Marketing campaign that generated this deal"
    )
    
    # Status & Lifecycle
    is_active = models.BooleanField(default=True, help_text="Whether this deal is active")
    is_won = models.BooleanField(default=False, help_text="Deal was won")
    is_lost = models.BooleanField(default=False, help_text="Deal was lost")
    lost_reason = models.CharField(max_length=255, blank=True, help_text="Reason for losing the deal")
    
    # Rotting/Stale Detection (DEAL-6)
    last_activity_date = models.DateField(null=True, blank=True, help_text="Date of last activity on this deal")
    is_stale = models.BooleanField(default=False, help_text="Deal has had no activity for extended period")
    stale_days_threshold = models.IntegerField(default=30, help_text="Days without activity before marked stale")
    
    # Conversion to Project
    converted_to_project = models.BooleanField(default=False, help_text="Deal converted to project")
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_deals",
        help_text="Project created from this deal"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_deals",
        help_text="User who created this deal"
    )
    
    # Tags for filtering/organization
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorizing deals")
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_deals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "pipeline", "stage"], name="crm_deal_firm_pip_stg_idx"),
            models.Index(fields=["firm", "owner"], name="crm_deal_firm_owner_idx"),
            models.Index(fields=["firm", "is_active"], name="crm_deal_firm_active_idx"),
            models.Index(fields=["firm", "expected_close_date"], name="crm_deal_firm_close_idx"),
            models.Index(fields=["firm", "is_stale"], name="crm_deal_firm_stale_idx"),
            models.Index(fields=["account"], name="crm_deal_account_idx"),
            models.Index(fields=["contact"], name="crm_deal_contact_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.stage.name} (${self.value})"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to calculate weighted value and update status."""
        # Calculate weighted value
        self.weighted_value = (self.value * Decimal(self.probability)) / Decimal(100)
        
        # Update is_won/is_lost based on stage
        if self.stage.is_closed_won:
            self.is_won = True
            self.is_active = False
            if not self.actual_close_date:
                from django.utils import timezone
                self.actual_close_date = timezone.now().date()
        elif self.stage.is_closed_lost:
            self.is_lost = True
            self.is_active = False
            if not self.actual_close_date:
                from django.utils import timezone
                self.actual_close_date = timezone.now().date()
        
        # Check for stale deals (DEAL-6)
        if self.last_activity_date and self.is_active:
            from django.utils import timezone
            days_since_activity = (timezone.now().date() - self.last_activity_date).days
            self.is_stale = days_since_activity >= self.stale_days_threshold
        
        super().save(*args, **kwargs)
    
    def update_last_activity(self) -> None:
        """Update last activity date to today."""
        from django.utils import timezone
        self.last_activity_date = timezone.now().date()
        self.is_stale = False
        self.save(update_fields=["last_activity_date", "is_stale", "updated_at"])
    
    def convert_to_project(self, project_data: dict = None) -> Any:
        """
        Convert this deal to a project (DEAL-1 conversion workflow).
        
        Args:
            project_data: Optional dictionary with project creation data
            
        Returns:
            Created Project instance
        """
        if self.converted_to_project:
            raise ValueError("Deal has already been converted to a project")
        
        if not self.is_won:
            raise ValueError("Only won deals can be converted to projects")
        
        from modules.projects.models import Project
        from django.utils import timezone
        
        # Prepare project data
        project_defaults = {
            "firm": self.firm,
            "name": self.name,
            "description": self.description,
            "client": self.account.client if self.account and hasattr(self.account, "client") else None,
            "budget": self.value,
            "owner": self.owner,
            "start_date": timezone.now().date(),
            "status": "planning",
        }
        
        # Merge with provided project data
        if project_data:
            project_defaults.update(project_data)
        
        # Create the project
        project = Project.objects.create(**project_defaults)
        
        # Update deal
        self.converted_to_project = True
        self.project = project
        self.save(update_fields=["converted_to_project", "project", "updated_at"])
        
        return project


class DealTask(models.Model):
    """
    Task associated with a Deal (DEAL-2).
    
    Represents action items and tasks related to deal progression.
    
    TIER 0: Belongs to exactly one Firm via Deal relationship.
    """
    
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    
    # Deal relationship
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="tasks",
        help_text="Deal this task belongs to"
    )
    
    # Task Details
    title = models.CharField(max_length=255, help_text="Task title")
    description = models.TextField(blank=True, help_text="Task description")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deal_tasks",
        help_text="User assigned to this task"
    )
    
    # Timeline
    due_date = models.DateField(null=True, blank=True, help_text="Task due date")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When task was completed")
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_deal_tasks",
        help_text="User who created this task"
    )
    
    class Meta:
        db_table = "crm_deal_tasks"
        ordering = ["due_date", "-priority", "title"]
        indexes = [
            models.Index(fields=["deal", "status"], name="crm_deal_task_deal_status_idx"),
            models.Index(fields=["assigned_to", "status"], name="crm_deal_task_user_status_idx"),
            models.Index(fields=["due_date"], name="crm_deal_task_due_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.deal.name} - {self.title}"
    
    @property
    def firm(self):
        """Get the firm through the deal relationship."""
        return self.deal.firm
    
    def complete(self) -> None:
        """Mark task as completed."""
        from django.utils import timezone
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])
        
        # Update deal last activity
        self.deal.update_last_activity()


# Import assignment automation models (DEAL-5)
from .assignment_automation import AssignmentRule, StageAutomation
