"""
Pricing Engine Models (DOC-09.1 per docs/03-reference/requirements/DOC-09.md PRICING_ENGINE_SPEC)

Implements:
- RuleSet: Versioned pricing rule collections
- Quote: Mutable working draft
- QuoteVersion: Immutable pricing snapshots for audit
- QuoteLineItem: Line items within a quote version
- EvaluationTrace: Audit trail for pricing evaluation

TIER 0: All pricing records belong to exactly one Firm for tenant isolation.
"""

import hashlib
import json
from typing import Any, Optional

from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class RuleSet(models.Model):
    """
    RuleSet model per docs/03-reference/requirements/DOC-09.md section 2.1.

    A RuleSet is a named collection of pricing rules under a specific schema version.

    Invariants:
    - Published RuleSets MUST be immutable
    - A QuoteVersion MUST reference the exact RuleSet (id + version + checksum)
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("deprecated", "Deprecated"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="pricing_rulesets",
        help_text="Firm (workspace) this ruleset belongs to",
    )

    # RuleSet identity
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for this ruleset",
    )
    code = models.CharField(
        max_length=100,
        help_text="Stable code identifier for this ruleset",
    )
    version = models.IntegerField(
        default=1,
        help_text="Monotonic version number (increments on each publish)",
    )
    schema_version = models.CharField(
        max_length=20,
        default="1.0.0",
        help_text="Pricing JSON schema version",
    )

    # Rule content
    rules_json = models.JSONField(
        default=dict,
        help_text="The pricing rules in JSON format",
    )
    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 checksum of normalized rules JSON",
    )

    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this ruleset was published",
    )
    deprecated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this ruleset was deprecated",
    )

    # Currency
    default_currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Default currency for this ruleset (ISO 4217)",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_rulesets",
    )
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "pricing_ruleset"
        ordering = ["-version"]
        indexes = [
            models.Index(fields=["firm", "code", "-version"], name="pricing_fir_cod_ver_idx"),
            models.Index(fields=["firm", "status"], name="pricing_rul_fir_sta_idx"),
            models.Index(fields=["checksum"], name="pricing_che_idx"),
        ]
        unique_together = [["firm", "code", "version"]]

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({self.status})"

    def compute_checksum(self) -> str:
        """
        Compute SHA-256 checksum of normalized rules JSON.

        DOC-09.3: Checksum is used for tamper detection and reproducibility.
        """
        normalized = json.dumps(self.rules_json, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode()).hexdigest()

    def verify_checksum(self) -> bool:
        """
        Verify that stored checksum matches current rules_json.

        DOC-09.3: Checksum enforcement for tamper detection.

        Returns:
            True if checksum is valid, False otherwise
        """
        expected_checksum = self.compute_checksum()
        return self.checksum == expected_checksum

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Update checksum before saving.

        DOC-09.3: Enforce immutability for published rulesets.
        """
        from django.core.exceptions import ValidationError

        # DOC-09.3: Prevent modification of published rulesets
        if self.pk:
            try:
                existing = RuleSet.objects.get(pk=self.pk)
                if existing.status == "published":
                    # Published rulesets are immutable - only allow status changes to deprecated
                    if self.status != existing.status and self.status == "deprecated":
                        # Allow publishing → deprecated transition
                        self.deprecated_at = timezone.now()
                    elif (
                        self.rules_json != existing.rules_json
                        or self.name != existing.name
                        or self.code != existing.code
                        or self.version != existing.version
                        or self.schema_version != existing.schema_version
                        or self.default_currency != existing.default_currency
                    ):
                        raise ValidationError(
                            "Published rulesets are immutable. Create a new version instead."
                        )
            except RuleSet.DoesNotExist:
                pass

        # Compute and update checksum
        self.checksum = self.compute_checksum()
        super().save(*args, **kwargs)

    def publish(self, user=None) -> "RuleSet":
        """
        Publish this ruleset, making it immutable.

        Returns:
            Self if already published, or raises error if validation fails.
        """
        if self.status == "published":
            return self

        # Validate rules before publishing
        self._validate_for_publish()

        self.status = "published"
        self.published_at = timezone.now()
        self.save()
        return self

    def _validate_for_publish(self) -> None:
        """Validate ruleset is ready for publishing."""
        from django.core.exceptions import ValidationError

        errors = []

        if not self.rules_json:
            errors.append("Rules JSON cannot be empty")

        # Validate required schema fields
        required_fields = ["schema_version", "products"]
        for field in required_fields:
            if field not in self.rules_json:
                errors.append(f"Missing required field: {field}")

        if errors:
            raise ValidationError({"rules_json": errors})

    def clean(self) -> None:
        """Validate ruleset data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Published rulesets cannot be modified
        if self.pk:
            try:
                existing = RuleSet.objects.get(pk=self.pk)
                if existing.status == "published":
                    if self.rules_json != existing.rules_json:
                        errors["rules_json"] = "Published rulesets cannot be modified."
            except RuleSet.DoesNotExist:
                pass

        if errors:
            raise ValidationError(errors)


class Quote(models.Model):
    """
    Quote model (mutable working draft) per docs/03-reference/requirements/DOC-09.md section 2.2.

    A Quote is the mutable working draft before snapshotting into QuoteVersion.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="quotes",
    )

    # Quote identity
    quote_number = models.CharField(
        max_length=50,
        help_text="Human-readable quote number",
    )

    # Client reference
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="quotes",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    # Current version reference
    current_version = models.ForeignKey(
        "QuoteVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Current active version of this quote",
    )

    # Validity
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Quote expiration date",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_quotes",
    )
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "pricing_quote"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "client", "-created_at"], name="pricing_fir_cli_cre_idx"),
            models.Index(fields=["firm", "status"], name="pricing_quo_fir_sta_idx"),
            models.Index(fields=["firm", "quote_number"], name="pricing_fir_quo_idx"),
        ]
        unique_together = [["firm", "quote_number"]]

    def __str__(self) -> str:
        return f"Quote {self.quote_number}"


class QuoteVersion(models.Model):
    """
    QuoteVersion model (immutable snapshot) per docs/03-reference/requirements/DOC-09.md section 2.2 and 7.

    The immutable snapshot used for issuance/acceptance/audit.

    A QuoteVersion MUST snapshot:
    - evaluation context (bounded)
    - ruleset reference (id/version/checksum)
    - evaluation outputs
    - evaluation trace
    - issuance/acceptance metadata

    Invariants:
    - Once accepted, QuoteVersion MUST be immutable
    - Any change requires a new QuoteVersion
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("accepted", "Accepted"),
        ("superseded", "Superseded"),
        ("rejected", "Rejected"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="quote_versions",
    )

    # Parent quote
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.IntegerField(
        default=1,
        help_text="Version number within the quote",
    )

    # RuleSet reference (DOC-09.1: exact reference required)
    ruleset = models.ForeignKey(
        RuleSet,
        on_delete=models.PROTECT,
        related_name="quote_versions",
        help_text="The ruleset used for evaluation",
    )
    ruleset_checksum = models.CharField(
        max_length=64,
        help_text="Checksum of ruleset at time of evaluation (for reproducibility)",
    )

    # Evaluation context snapshot (DOC-09.1: required for reproducibility)
    context_snapshot = models.JSONField(
        default=dict,
        help_text="Snapshot of evaluation context (bounded, no HR data)",
    )

    # Evaluation outputs (DOC-09.1: required outputs)
    line_items = models.JSONField(
        default=list,
        help_text="Computed line items",
    )
    totals = models.JSONField(
        default=dict,
        help_text="Computed totals (subtotal, discounts, taxes, total)",
    )
    assumptions = models.JSONField(
        default=list,
        help_text="List of assumption statements",
    )
    warnings = models.JSONField(
        default=list,
        help_text="Validation or policy warnings",
    )

    # Evaluation trace (DOC-09.1: required for audit)
    evaluation_trace = models.JSONField(
        default=dict,
        help_text="Complete evaluation trace for audit",
    )
    outputs_checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="Checksum of evaluation outputs",
    )

    # Currency
    currency = models.CharField(
        max_length=3,
        default="USD",
    )

    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    issued_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_quote_versions",
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_quote_versions",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    correlation_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Correlation ID from evaluation request",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "pricing_quote_version"
        ordering = ["-version_number"]
        indexes = [
            models.Index(fields=["firm", "quote", "-version_number"], name="pricing_fir_quo_ver_idx"),
            models.Index(fields=["firm", "status"], name="pricing_ver_fir_sta_idx"),
            models.Index(fields=["firm", "ruleset"], name="pricing_fir_rul_idx"),
            models.Index(fields=["correlation_id"], name="pricing_cor_idx"),
        ]
        unique_together = [["quote", "version_number"]]

    def __str__(self) -> str:
        return f"{self.quote} v{self.version_number}"

    def compute_outputs_checksum(self) -> str:
        """Compute checksum of evaluation outputs."""
        outputs = {
            "line_items": self.line_items,
            "totals": self.totals,
            "assumptions": self.assumptions,
        }
        normalized = json.dumps(outputs, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode()).hexdigest()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Update outputs checksum and validate immutability."""
        # Compute outputs checksum
        if self.line_items or self.totals:
            self.outputs_checksum = self.compute_outputs_checksum()

        # Store ruleset checksum at time of creation
        if not self.pk and self.ruleset_id:
            self.ruleset_checksum = self.ruleset.checksum

        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate quote version data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Accepted quote versions cannot be modified
        if self.pk:
            try:
                existing = QuoteVersion.objects.get(pk=self.pk)
                if existing.status == "accepted":
                    # Check if any evaluation fields changed
                    if (
                        self.context_snapshot != existing.context_snapshot
                        or self.line_items != existing.line_items
                        or self.totals != existing.totals
                    ):
                        errors["status"] = "Accepted quote versions cannot be modified."
            except QuoteVersion.DoesNotExist:
                pass

        if errors:
            raise ValidationError(errors)

    @property
    def total_amount(self) -> float:
        """Get the total amount from totals."""
        return self.totals.get("total", 0)


class QuoteLineItem(models.Model):
    """
    QuoteLineItem model per docs/03-reference/requirements/DOC-09.md section 6.1.

    Stores individual line items for a quote version.
    Each line item SHOULD map to an EngagementLine candidate.
    """

    BILLING_MODEL_CHOICES = [
        ("fixed", "Fixed Fee"),
        ("recurring", "Recurring"),
        ("usage", "Usage-Based"),
        ("hybrid", "Hybrid"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="quote_line_items",
    )

    # Parent quote version
    quote_version = models.ForeignKey(
        QuoteVersion,
        on_delete=models.CASCADE,
        related_name="line_item_records",
    )

    # Line item identity
    line_number = models.IntegerField(
        help_text="Line number within the quote version",
    )
    product_code = models.CharField(
        max_length=100,
        help_text="Product code from ruleset",
    )

    # Line item details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    # Billing configuration
    billing_model = models.CharField(
        max_length=20,
        choices=BILLING_MODEL_CHOICES,
        default="fixed",
    )
    billing_unit = models.CharField(
        max_length=50,
        blank=True,
        help_text="Billing unit (month, quarter, project, hour, etc.)",
    )

    # Additional metadata
    notes = models.TextField(blank=True)
    tax_category = models.CharField(max_length=50, blank=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "pricing_quote_line_item"
        ordering = ["line_number"]
        indexes = [
            models.Index(fields=["firm", "quote_version", "line_number"], name="pricing_fir_quo_lin_idx"),
            models.Index(fields=["firm", "product_code"], name="pricing_fir_pro_idx"),
        ]
        unique_together = [["quote_version", "line_number"]]

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.name}"
