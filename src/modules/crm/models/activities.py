from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager

from .campaigns import Campaign
from .leads import Lead
from .proposals import Proposal
from .prospects import Prospect

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
        Lead,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activities",
        help_text="Lead this activity is associated with",
    )
    prospect = models.ForeignKey(
        Prospect,
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
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
        help_text="Campaign this activity is part of",
    )
    proposal = models.ForeignKey(
        Proposal,
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

