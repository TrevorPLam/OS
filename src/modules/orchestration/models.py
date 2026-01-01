"""
Orchestration Engine Models (DOC-11.1 per docs/11 ORCHESTRATION_ENGINE_SPEC).

Implements:
- OrchestrationDefinition: Workflow template with steps and policies
- OrchestrationExecution: Single run instance with idempotency
- StepExecution: Individual step attempt with retry tracking
- Error classification and retry policies

TIER 0: All orchestration records belong to exactly one Firm for tenant isolation.
DOC-11.1: Idempotent, retry-safe, observable execution with DLQ routing.
"""

import hashlib
import json
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class OrchestrationDefinition(models.Model):
    """
    OrchestrationDefinition model per docs/11 section 2.1.

    Defines a workflow template (steps + transitions + policies).

    Invariants:
    - Published definitions MUST be immutable
    - Executions MUST reference a specific published definition version
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
        related_name="orchestration_definitions",
        help_text="Firm (workspace) this definition belongs to",
    )

    # Definition identity
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for this orchestration",
    )
    code = models.CharField(
        max_length=100,
        help_text="Stable code identifier",
    )
    version = models.IntegerField(
        default=1,
        help_text="Monotonic version number",
    )

    # Steps and policies
    steps_json = models.JSONField(
        default=list,
        help_text="Step definitions array",
    )
    policies = models.JSONField(
        default=dict,
        help_text="Timeout, retry, concurrency policies",
    )

    # Schemas
    input_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON schema for input validation",
    )
    output_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON schema for output validation",
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
    )
    deprecated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_orchestration_definitions",
    )
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "orchestration_definition"
        ordering = ["-version"]
        indexes = [
            models.Index(fields=["firm", "code", "-version"], name="orchestrat_fir_cod_ver_idx"),
            models.Index(fields=["firm", "status"], name="orchestrat_def_fir_sta_idx"),
        ]
        unique_together = [["firm", "code", "version"]]

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({self.status})"

    def publish(self, user=None) -> "OrchestrationDefinition":
        """Publish this definition, making it immutable."""
        if self.status == "published":
            return self

        self.status = "published"
        self.published_at = timezone.now()
        self.save()
        return self

    def clean(self) -> None:
        """Validate definition data integrity."""
        errors = {}

        # Published definitions cannot be modified
        if self.pk:
            try:
                existing = OrchestrationDefinition.objects.get(pk=self.pk)
                if existing.status == "published":
                    if self.steps_json != existing.steps_json:
                        errors["steps_json"] = (
                            "Published definitions cannot be modified."
                        )
            except OrchestrationDefinition.DoesNotExist:
                pass

        if errors:
            raise ValidationError(errors)


class OrchestrationExecution(models.Model):
    """
    OrchestrationExecution model per docs/11 section 2.3.

    Represents a single run of a definition for a specific target.

    Invariants:
    - Execution MUST be idempotent at creation (same idempotency_key => same execution)
    - Execution MUST store sufficient data to reconstruct what happened
    """

    STATUS_CHOICES = [
        ("running", "Running"),
        ("waiting_approval", "Waiting Approval"),
        ("paused", "Paused"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
    ]

    TARGET_TYPE_CHOICES = [
        ("engagement", "Engagement"),
        ("work_item", "WorkItem"),
        ("task", "Task"),
        ("invoice", "Invoice"),
        ("document", "Document"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="orchestration_executions",
    )

    # Definition reference
    definition = models.ForeignKey(
        OrchestrationDefinition,
        on_delete=models.PROTECT,
        related_name="executions",
    )
    definition_version = models.IntegerField(
        help_text="Version at time of execution",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="running",
    )

    # Target object
    target_object_type = models.CharField(
        max_length=50,
        choices=TARGET_TYPE_CHOICES,
        help_text="Type of object being orchestrated",
    )
    target_object_id = models.IntegerField(
        help_text="ID of target object",
    )

    # Input/output
    input_data = models.JSONField(
        default=dict,
        help_text="Validated input snapshot",
    )
    output_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Execution output",
    )

    # Idempotency and correlation
    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        help_text="Execution-level idempotency key",
    )
    correlation_id = models.CharField(
        max_length=64,
        help_text="Root correlation ID",
    )

    # Lifecycle
    started_at = models.DateTimeField(
        auto_now_add=True,
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Retry tracking
    attempt_count = models.IntegerField(
        default=1,
        help_text="Number of execution restart attempts",
    )

    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_executions",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "orchestration_execution"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["firm", "status", "-started_at"], name="orchestrat_fir_sta_sta_idx"),
            models.Index(fields=["firm", "definition", "-started_at"], name="orchestrat_fir_def_sta_idx"),
            models.Index(fields=["idempotency_key"], name="orchestrat_exe_ide_idx"),
            models.Index(fields=["correlation_id"], name="orchestrat_cor_idx"),
            models.Index(fields=["target_object_type", "target_object_id"], name="orchestrat_tar_tar_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.definition.name} execution {self.id} ({self.status})"

    @staticmethod
    def compute_idempotency_key(
        firm_id: int,
        definition_code: str,
        target_type: str,
        target_id: int,
        discriminator: str = "",
    ) -> str:
        """
        Compute execution-level idempotency key per docs/11 section 6.1.

        Args:
            firm_id: Firm ID
            definition_code: OrchestrationDefinition code
            target_type: Target object type
            target_id: Target object ID
            discriminator: Optional discriminator

        Returns:
            SHA-256 hash of components
        """
        components = f"{firm_id}:{definition_code}:{target_type}:{target_id}:{discriminator}"
        return hashlib.sha256(components.encode()).hexdigest()


class StepExecution(models.Model):
    """
    StepExecution model per docs/11 section 2.4.

    Represents an attempt of a specific step within an execution.

    Invariants:
    - StepExecution is append-only (retries create new attempts)
    - Step idempotency key ensures safe retries
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("retrying", "Retrying"),
        ("timed_out", "Timed Out"),
        ("skipped", "Skipped"),
        ("awaiting_approval", "Awaiting Approval"),
    ]

    ERROR_CLASS_CHOICES = [
        ("TRANSIENT", "Transient Error"),
        ("RETRYABLE", "Retryable Error"),
        ("NON_RETRYABLE", "Non-Retryable Error"),
        ("RATE_LIMITED", "Rate Limited"),
        ("DEPENDENCY_FAILED", "Dependency Failed"),
        ("COMPENSATION_REQUIRED", "Compensation Required"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="step_executions",
    )

    # Parent execution
    execution = models.ForeignKey(
        OrchestrationExecution,
        on_delete=models.CASCADE,
        related_name="steps",
    )

    # Step identity
    step_id = models.CharField(
        max_length=100,
        help_text="Step ID from definition",
    )
    step_name = models.CharField(
        max_length=255,
        help_text="Human-readable step name",
    )

    # Attempt tracking
    attempt_number = models.IntegerField(
        default=1,
        help_text="Attempt number for this step",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    # Error tracking
    error_class = models.CharField(
        max_length=50,
        choices=ERROR_CLASS_CHOICES,
        blank=True,
        help_text="Classified error type per docs/11 section 4",
    )
    error_summary = models.TextField(
        blank=True,
        help_text="Redacted error summary",
    )

    # Retry scheduling
    retry_after_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to retry this step",
    )

    # Idempotency
    idempotency_key = models.CharField(
        max_length=64,
        help_text="Step-level idempotency key",
    )

    # Result
    result_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Step result (bounded)",
    )

    # Logs reference
    logs_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional pointer to external logs",
    )

    # Lifecycle
    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "orchestration_step_execution"
        ordering = ["execution", "step_id", "attempt_number"]
        indexes = [
            models.Index(fields=["firm", "execution", "step_id"], name="orchestrat_fir_exe_ste_idx"),
            models.Index(fields=["firm", "status"], name="orchestrat_stp_fir_sta_idx"),
            models.Index(fields=["idempotency_key"], name="orchestrat_stp_ide_idx"),
            models.Index(fields=["retry_after_at"], name="orchestrat_ret_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.step_name} (attempt {self.attempt_number}): {self.status}"

    @staticmethod
    def compute_idempotency_key(
        firm_id: int,
        execution_id: int,
        step_id: str,
    ) -> str:
        """
        Compute step-level idempotency key per docs/11 section 6.2.

        Args:
            firm_id: Firm ID
            execution_id: OrchestrationExecution ID
            step_id: Step ID from definition

        Returns:
            SHA-256 hash of components
        """
        components = f"{firm_id}:{execution_id}:{step_id}"
        return hashlib.sha256(components.encode()).hexdigest()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Compute idempotency key before saving."""
        if not self.idempotency_key:
            self.idempotency_key = self.compute_idempotency_key(
                self.firm_id,
                self.execution_id,
                self.step_id,
            )
        super().save(*args, **kwargs)


class OrchestrationDLQ(models.Model):
    """
    Dead Letter Queue for failed orchestration steps.

    Tracks steps that exceeded retry limits or hit non-retryable errors.

    DOC-11.1: DLQ routing for non-retryable and exhausted retries.
    """

    REASON_CHOICES = [
        ("max_retries_exceeded", "Max Retries Exceeded"),
        ("non_retryable_error", "Non-Retryable Error"),
        ("compensation_required", "Compensation Required"),
        ("timeout_exceeded", "Timeout Exceeded"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="orchestration_dlq",
    )

    # Step reference
    step_execution = models.ForeignKey(
        StepExecution,
        on_delete=models.CASCADE,
        related_name="dlq_entries",
    )
    execution = models.ForeignKey(
        OrchestrationExecution,
        on_delete=models.CASCADE,
        related_name="dlq_entries",
    )

    # DLQ metadata
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        help_text="Why this was sent to DLQ",
    )
    error_class = models.CharField(
        max_length=50,
        help_text="Error classification",
    )
    error_summary = models.TextField(
        help_text="Redacted error summary",
    )

    # Resolution tracking
    resolved = models.BooleanField(
        default=False,
        help_text="Has this DLQ item been resolved?",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_dlq_items",
    )
    resolution_notes = models.TextField(
        blank=True,
        help_text="Notes on how this was resolved",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "orchestration_dlq"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "resolved", "-created_at"], name="orchestrat_fir_res_cre_idx"),
            models.Index(fields=["execution"], name="orchestrat_exe_idx"),
        ]

    def __str__(self) -> str:
        return f"DLQ: {self.step_execution.step_name} ({self.reason})"
