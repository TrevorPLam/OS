from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


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


