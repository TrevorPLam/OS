from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


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


