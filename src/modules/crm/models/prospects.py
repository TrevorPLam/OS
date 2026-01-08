from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager

from .leads import Lead

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

