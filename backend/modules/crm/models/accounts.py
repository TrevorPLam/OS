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


