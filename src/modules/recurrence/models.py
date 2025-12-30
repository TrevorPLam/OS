"""
Recurrence Engine Models (DOC-10.1 per docs/10 RECURRENCE_ENGINE_SPEC).

Implements:
- RecurrenceRule: Definition of "what repeats" and "how to compute periods"
- RecurrenceGeneration: Dedupe ledger for generated instances
- PeriodDefinition: Helper model for period boundaries

TIER 0: All recurrence records belong to exactly one Firm for tenant isolation.
DOC-10.1: Deterministic generation without duplicates, DST correctness.
"""

import hashlib
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class RecurrenceRule(models.Model):
    """
    RecurrenceRule model per docs/10 section 2.1.

    A definition of "what repeats" and "how to compute periods."

    Invariants:
    - RecurrenceRule MUST be validated at creation/update time
    - If end_at is absent, the rule is open-ended
    - Every RecurrenceRule MUST specify a timezone
    """

    SCOPE_CHOICES = [
        ("work_item_template_node", "WorkItemTemplateNode"),
        ("delivery_template", "DeliveryTemplate"),
        ("engagement_line", "EngagementLine"),
        ("engagement", "Engagement"),
    ]

    ANCHOR_TYPE_CHOICES = [
        ("calendar", "Calendar"),
        ("fiscal", "Fiscal"),
        ("custom", "Custom"),
    ]

    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("canceled", "Canceled"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="recurrence_rules",
        help_text="Firm (workspace) this recurrence rule belongs to",
    )

    # Scope - what this recurrence applies to
    scope = models.CharField(
        max_length=50,
        choices=SCOPE_CHOICES,
        help_text="What object type this recurrence applies to",
    )

    # Polymorphic target references
    target_delivery_template = models.ForeignKey(
        "delivery.DeliveryTemplate",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recurrence_rules",
    )
    target_engagement = models.ForeignKey(
        "clients.ClientEngagement",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recurrence_rules",
    )
    target_engagement_line = models.ForeignKey(
        "clients.EngagementLine",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recurrence_rules",
    )

    # Recurrence pattern
    anchor_type = models.CharField(
        max_length=20,
        choices=ANCHOR_TYPE_CHOICES,
        default="calendar",
        help_text="Calendar anchoring type",
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        help_text="Recurrence frequency",
    )
    interval = models.IntegerField(
        default=1,
        help_text="Interval for frequency (e.g., every 2 weeks)",
    )

    # Frequency-specific parameters
    by_day = models.JSONField(
        default=list,
        blank=True,
        help_text="Days of week for weekly rules (e.g., ['MON', 'WED', 'FRI'])",
    )
    by_month_day = models.JSONField(
        default=list,
        blank=True,
        help_text="Days of month for monthly rules (e.g., [1, 15, -1])",
    )

    # Time parameters
    time_of_day = models.TimeField(
        null=True,
        blank=True,
        help_text="Time of day for deadlines/appointments",
    )
    timezone = models.CharField(
        max_length=100,
        help_text="IANA timezone (required; e.g., 'America/New_York')",
    )

    # DST policy (docs/10 section 3.2)
    dst_ambiguous_policy = models.CharField(
        max_length=20,
        default="first",
        choices=[
            ("first", "First Occurrence"),
            ("second", "Second Occurrence"),
        ],
        help_text="Policy for ambiguous times during DST fall-back",
    )

    # Validity window
    start_at = models.DateTimeField(
        help_text="When this recurrence starts (timezone-aware)",
    )
    end_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this recurrence ends (optional; open-ended if null)",
    )

    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    paused_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this rule was paused",
    )
    paused_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paused_recurrence_rules",
    )
    canceled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this rule was canceled",
    )
    canceled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="canceled_recurrence_rules",
    )

    # Metadata
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for this recurrence rule",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this recurrence",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_recurrence_rules",
    )
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "recurrence_rule"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["firm", "scope"]),
            models.Index(fields=["target_delivery_template"]),
            models.Index(fields=["target_engagement"]),
            models.Index(fields=["target_engagement_line"]),
            models.Index(fields=["start_at"]),
            models.Index(fields=["end_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.frequency}, {self.status})"

    def clean(self) -> None:
        """Validate recurrence rule data integrity."""
        errors = {}

        # Validate timezone
        try:
            import zoneinfo
            zoneinfo.ZoneInfo(self.timezone)
        except Exception:
            errors["timezone"] = f"Invalid timezone: {self.timezone}"

        # Validate target reference
        target_count = sum(
            [
                bool(self.target_delivery_template_id),
                bool(self.target_engagement_id),
                bool(self.target_engagement_line_id),
            ]
        )
        if target_count == 0:
            errors["scope"] = "At least one target must be specified"
        elif target_count > 1:
            errors["scope"] = "Only one target can be specified"

        # Validate end_at after start_at
        if self.end_at and self.start_at and self.end_at <= self.start_at:
            errors["end_at"] = "End date must be after start date"

        # Validate frequency-specific parameters
        if self.frequency == "weekly" and not self.by_day:
            errors["by_day"] = "Weekly frequency requires by_day parameter"

        if errors:
            raise ValidationError(errors)

    def pause(self, user) -> None:
        """
        Pause this recurrence rule.

        DOC-10.1: Paused rules do not generate new instances.
        """
        if self.status == "paused":
            return

        self.status = "paused"
        self.paused_at = timezone.now()
        self.paused_by = user
        self.save()

    def resume(self, user) -> None:
        """
        Resume this recurrence rule.

        DOC-10.1: Resumed rules continue generating instances.
        """
        if self.status != "paused":
            return

        self.status = "active"
        self.save()

    def cancel(self, user) -> None:
        """
        Cancel this recurrence rule.

        DOC-10.1: Canceled rules do not generate new instances.
        Previously generated instances are not affected.
        """
        if self.status == "canceled":
            return

        self.status = "canceled"
        self.canceled_at = timezone.now()
        self.canceled_by = user
        self.save()


class RecurrenceGeneration(models.Model):
    """
    RecurrenceGeneration model per docs/10 section 2.3.

    The dedupe ledger representing the "fact" that the system generated
    (or attempted to generate) an instance for a given period.

    Invariants:
    - RecurrenceGeneration MUST be the dedupe source of truth
    - Work generation MUST NOT bypass this table
    - Unique constraint on (recurrence_rule, period_key, discriminator)
    """

    TARGET_OBJECT_TYPE_CHOICES = [
        ("work_item", "WorkItem"),
        ("task", "Task"),
        ("appointment", "Appointment"),
    ]

    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("generated", "Generated"),
        ("skipped", "Skipped"),
        ("failed", "Failed"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="recurrence_generations",
    )

    # Recurrence rule reference
    recurrence_rule = models.ForeignKey(
        RecurrenceRule,
        on_delete=models.PROTECT,
        related_name="generations",
    )

    # Period identification (DOC-10.1: stable period_key)
    period_key = models.CharField(
        max_length=100,
        help_text="Stable period key (e.g., '2026-01', '2026-Q1', '2026-W05')",
    )
    period_starts_at = models.DateTimeField(
        help_text="Period start (UTC, derived from timezone-aware boundaries)",
    )
    period_ends_at = models.DateTimeField(
        help_text="Period end (UTC, derived from timezone-aware boundaries)",
    )
    period_label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Human-friendly label (e.g., 'January 2026')",
    )

    # Target object tracking
    target_object_type = models.CharField(
        max_length=50,
        choices=TARGET_OBJECT_TYPE_CHOICES,
        help_text="Type of object created by this generation",
    )
    target_object_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of created object (nullable until generated)",
    )

    # Discriminator for multiple targets per period
    target_discriminator = models.CharField(
        max_length=100,
        blank=True,
        help_text="Discriminator for multiple targets per period (e.g., template_node_id)",
    )

    # Generation status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planned",
    )
    generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the target object was generated",
    )

    # Idempotency key (DOC-10.1: required for dedupe)
    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        help_text="Hash of (tenant + rule + period + discriminator) for idempotency",
    )

    # Skip/failure tracking
    skip_reason_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Reason code if skipped (e.g., 'engagement_not_active')",
    )
    skip_reason_message = models.TextField(
        blank=True,
        help_text="Human-readable reason if skipped",
    )
    error_summary = models.TextField(
        blank=True,
        help_text="Redacted error summary if failed",
    )

    # Retry tracking
    attempt_count = models.IntegerField(
        default=0,
        help_text="Number of generation attempts",
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last generation attempt occurred",
    )

    # Backfill tracking (DOC-10.2)
    backfilled = models.BooleanField(
        default=False,
        help_text="Whether this generation was created via backfill operation",
    )
    backfill_reason = models.TextField(
        blank=True,
        help_text="Reason for backfill (if backfilled=True)",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    correlation_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Correlation ID for tracking",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "recurrence_generation"
        ordering = ["-period_starts_at"]
        indexes = [
            models.Index(fields=["firm", "recurrence_rule", "-period_starts_at"]),
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["idempotency_key"]),
            models.Index(fields=["target_object_type", "target_object_id"]),
            models.Index(fields=["correlation_id"]),
        ]
        unique_together = [
            ["recurrence_rule", "period_key", "target_discriminator"]
        ]

    def __str__(self) -> str:
        return f"{self.recurrence_rule.name} - {self.period_key} ({self.status})"

    @staticmethod
    def compute_idempotency_key(
        firm_id: int,
        recurrence_rule_id: int,
        period_key: str,
        discriminator: str = "",
    ) -> str:
        """
        Compute idempotency key per docs/10 section 5.2.

        Args:
            firm_id: Firm ID
            recurrence_rule_id: RecurrenceRule ID
            period_key: Period key
            discriminator: Optional discriminator

        Returns:
            SHA-256 hash of the components
        """
        components = f"{firm_id}:{recurrence_rule_id}:{period_key}:{discriminator}"
        return hashlib.sha256(components.encode()).hexdigest()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Compute idempotency key before saving."""
        if not self.idempotency_key:
            self.idempotency_key = self.compute_idempotency_key(
                self.firm_id,
                self.recurrence_rule_id,
                self.period_key,
                self.target_discriminator,
            )
        super().save(*args, **kwargs)
