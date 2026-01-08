from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


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


