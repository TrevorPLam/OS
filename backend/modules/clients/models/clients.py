import hashlib
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager
from .organizations import Organization


class Client(models.Model):
    """
    Post-sale Client entity.

    Created when a CRM Proposal is accepted. Represents an active
    business relationship with a company that has signed a contract.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive - No Active Projects"),
        ("terminated", "Terminated"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="clients",
        help_text="Firm (workspace) this client belongs to",
    )

    # TIER 2.6: Organization grouping (OPTIONAL)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
        help_text="Optional organization for cross-client collaboration",
    )

    # Origin Tracking (from CRM)
    source_prospect = models.ForeignKey(
        "crm.Prospect",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="converted_clients",
        help_text="The prospect that was converted to this client",
    )
    source_proposal = models.ForeignKey(
        "crm.Proposal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="converted_clients",
        help_text="The proposal that created this client",
    )

    # Company Information
    # SECURITY: company_name is unique per firm, not globally (ASSESS-D4.4b)
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)

    # Contact Information
    primary_contact_name = models.CharField(max_length=255)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=50, blank=True)

    # Address
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="USA")

    # Business Metadata
    website = models.URLField(blank=True, validators=[validate_safe_url])
    employee_count = models.IntegerField(null=True, blank=True)

    # Client Status (Post-Sale Only)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Assigned Team
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_clients",
        help_text="Primary account manager for this client",
    )
    assigned_team = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assigned_clients",
        blank=True,
        help_text="Team members assigned to this client",
    )

    # Portal Access
    portal_enabled = models.BooleanField(default=False, help_text="Whether client portal access is enabled")

    # Financial Tracking
    total_lifetime_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total revenue from this client across all engagements",
    )

    # Retainer Balance Tracking (Simple feature 1.6)
    retainer_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Current retainer balance (prepaid hours/amount)",
    )
    retainer_hours_balance = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"), help_text="Prepaid hours remaining in retainer"
    )
    retainer_last_updated = models.DateTimeField(
        null=True, blank=True, help_text="When retainer balance was last updated"
    )

    # TIER 4: Autopay Settings
    autopay_enabled = models.BooleanField(default=False, help_text="Enable automatic payment of invoices")
    autopay_payment_method_id = models.CharField(
        max_length=255, blank=True, help_text="Stripe payment method ID for autopay"
    )
    autopay_activated_at = models.DateTimeField(null=True, blank=True, help_text="When autopay was enabled")
    autopay_activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="autopay_activations",
        help_text="Who enabled autopay",
    )

    # Activity Tracking
    active_projects_count = models.IntegerField(default=0, help_text="Number of currently active projects")
    client_since = models.DateField(help_text="Date of first engagement")

    # GDPR/Privacy Compliance (ASSESS-L19.2)
    marketing_opt_in = models.BooleanField(
        default=False,
        help_text="Has the client opted in to receive marketing communications?"
    )
    consent_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When consent was given (GDPR requirement)"
    )
    consent_source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Source of consent (e.g., 'signup_form', 'email_campaign', 'portal_settings')"
    )
    tos_accepted = models.BooleanField(
        default=False,
        help_text="Has the client accepted Terms of Service?"
    )
    tos_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When Terms of Service were accepted"
    )
    tos_version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Version of ToS that was accepted"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal notes (not visible to client)")

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "clients_client"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping, name="clients_fir_sta_idx")
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping, name="clients_fir_cre_idx")
            models.Index(fields=["organization"]),  # TIER 2.6: Org scoping, name="clients_org_idx")
            models.Index(fields=["account_manager"], name="clients_acc_idx"),
            models.Index(fields=["company_name"], name="clients_com_idx"),
        ]
        # TIER 0: Company names must be unique within a firm (not globally)
        unique_together = [["firm", "company_name"]]

    def __str__(self):
        return f"{self.company_name} ({self.firm.name})"

    def clean(self):
        """
        Validate Client data integrity.

        Validates:
        - Organization firm consistency: organization.firm == self.firm
        - Numeric constraints: employee_count >= 0
        - Autopay consistency: autopay_enabled requires payment_method_id
        - Retainer balance non-negative
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Organization firm consistency
        if self.organization_id and self.firm_id:
            if hasattr(self, "organization") and self.organization.firm_id != self.firm_id:
                errors["organization"] = "Client's organization must belong to the same firm."

        # Employee count validation
        if self.employee_count is not None and self.employee_count < 0:
            errors["employee_count"] = "Employee count cannot be negative."

        # Autopay consistency
        if self.autopay_enabled and not self.autopay_payment_method_id:
            errors["autopay_payment_method_id"] = "Payment method is required when autopay is enabled."

        # Retainer balance non-negative
        if self.retainer_balance < 0:
            errors["retainer_balance"] = "Retainer balance cannot be negative."
        if self.retainer_hours_balance < 0:
            errors["retainer_hours_balance"] = "Retainer hours balance cannot be negative."

        if errors:
            raise ValidationError(errors)


