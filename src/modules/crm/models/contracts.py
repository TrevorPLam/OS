from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


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
        "crm.Proposal",
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

