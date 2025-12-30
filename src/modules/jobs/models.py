"""
Job Queue and DLQ Models.

Implements DOC-20.1: Workers/queues payload rules, concurrency locks, DLQ reprocessing.
Complies with docs/20 WORKERS_AND_QUEUES.
"""

import uuid
import json
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class JobQueue(models.Model):
    """
    JobQueue model for background job execution tracking.

    Implements docs/20 section 2 (payload rules) and section 3 (concurrency model).
    """

    # Job categories per docs/20 section 1
    CATEGORY_CHOICES = [
        ("ingestion", "Ingestion"),  # email fetch/parse/store/map
        ("sync", "Sync"),  # calendar pull/push
        ("recurrence", "Recurrence"),  # period generation + work creation
        ("orchestration", "Orchestration"),  # step execution
        ("documents", "Documents"),  # scan/index/classify hooks
        ("notifications", "Notifications"),  # send email/in-app
        ("export", "Export"),  # firm offboarding, data export
        ("maintenance", "Maintenance"),  # cleanup, archival
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("dlq", "Dead Letter Queue"),
    ]

    PRIORITY_CHOICES = [
        (0, "Critical"),
        (1, "High"),
        (2, "Normal"),
        (3, "Low"),
    ]

    # Identity
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tenancy (per docs/20 section 2: payload MUST include tenant_id)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="job_queue",
        help_text="Firm this job belongs to (tenant isolation)",
    )

    # Job metadata
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Job category per docs/20 section 1",
    )
    job_type = models.CharField(
        max_length=100,
        help_text="Specific job type (e.g., 'email_ingestion_fetch', 'calendar_sync_pull')",
    )

    # Payload (per docs/20 section 2: minimal, versioned, with required fields)
    payload_version = models.CharField(
        max_length=10,
        default="1.0",
        help_text="Payload schema version for evolution",
    )
    payload = models.JSONField(
        help_text="Job payload: MUST include tenant_id, correlation_id, idempotency_key, object refs"
    )

    # Idempotency (per docs/20 section 2 and section 3)
    idempotency_key = models.CharField(
        max_length=255,
        help_text="Unique key for at-most-once processing per docs/20 section 3",
    )
    correlation_id = models.UUIDField(
        help_text="Correlation ID for tracing across systems per docs/20 section 2"
    )

    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current job status",
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2,
        help_text="Job priority (0=Critical, 3=Low)",
    )

    # Execution tracking
    scheduled_at = models.DateTimeField(
        default=timezone.now,
        help_text="When job should be processed",
    )
    claimed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When job was claimed by a worker (for concurrency control)",
    )
    claimed_by_worker = models.CharField(
        max_length=255,
        blank=True,
        help_text="Worker ID that claimed this job",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Retry tracking (aligned with orchestration error classes per docs/20 section 5)
    attempt_count = models.IntegerField(
        default=0,
        help_text="Number of execution attempts",
    )
    max_attempts = models.IntegerField(
        default=5,
        help_text="Maximum retry attempts before DLQ",
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled time for next retry",
    )

    # Error tracking
    error_class = models.CharField(
        max_length=50,
        blank=True,
        help_text="Error classification (transient, retryable, non_retryable, rate_limited)",
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message (redacted, no PII/content)",
    )

    # Result storage (optional)
    result = models.JSONField(
        null=True,
        blank=True,
        help_text="Job result (if applicable, minimal)",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "job_queue"
        ordering = ["priority", "scheduled_at"]
        indexes = [
            models.Index(fields=["firm", "status", "scheduled_at"], name="jobs_fir_sta_sch_idx"),
            models.Index(fields=["status", "priority", "scheduled_at"], name="jobs_sta_pri_sch_idx"),
            models.Index(fields=["idempotency_key"], name="jobs_ide_idx"),
            models.Index(fields=["correlation_id"], name="jobs_cor_idx"),
            models.Index(fields=["category", "status"], name="jobs_cat_sta_idx"),
            models.Index(fields=["claimed_at"], name="jobs_cla_idx"),
        ]
        # Uniqueness constraint for idempotency per docs/20 section 3
        constraints = [
            models.UniqueConstraint(
                fields=["firm", "idempotency_key"],
                name="unique_job_idempotency_key",
            )
        ]

    def __str__(self):
        return f"{self.category}:{self.job_type} [{self.status}]"

    def clean(self):
        """Validate payload structure per docs/20 section 2."""
        errors = {}

        # Validate payload has required fields
        if not isinstance(self.payload, dict):
            errors["payload"] = "Payload must be a dictionary"
        else:
            required_fields = ["tenant_id", "correlation_id", "idempotency_key"]
            missing = [f for f in required_fields if f not in self.payload]
            if missing:
                errors["payload"] = f"Payload missing required fields: {', '.join(missing)}"

            # Validate tenant_id matches firm
            if "tenant_id" in self.payload and self.firm_id:
                if self.payload["tenant_id"] != self.firm_id:
                    errors["payload"] = "Payload tenant_id must match job firm_id"

        if errors:
            raise ValidationError(errors)

    @transaction.atomic
    def claim_for_processing(self, worker_id: str) -> bool:
        """
        Claim this job for processing using advisory lock pattern.

        Implements docs/20 section 3: at-most-one concurrent processing.

        Returns:
            True if successfully claimed, False if already claimed
        """
        # Use SELECT FOR UPDATE SKIP LOCKED for concurrency control
        job = (
            JobQueue.objects.select_for_update(skip_locked=True)
            .filter(job_id=self.job_id, status="pending")
            .first()
        )

        if not job:
            return False

        # Claim the job
        job.status = "processing"
        job.claimed_at = timezone.now()
        job.claimed_by_worker = worker_id
        job.started_at = timezone.now()
        job.attempt_count += 1
        job.save()

        # Refresh self to reflect changes
        self.refresh_from_db()
        return True

    def mark_completed(self, result=None):
        """Mark job as completed with optional result."""
        self.status = "completed"
        self.completed_at = timezone.now()
        if result is not None:
            self.result = result
        self.save()

    def mark_failed(self, error_class: str, error_message: str, should_retry: bool = True):
        """
        Mark job as failed with error classification.

        Implements docs/20 section 4: DLQ handling for non-retryable or exhausted retries.

        Args:
            error_class: Error classification (transient, retryable, non_retryable, rate_limited)
            error_message: Redacted error message
            should_retry: Whether to retry or move to DLQ
        """
        self.error_class = error_class
        self.last_error = error_message

        # Check if should move to DLQ per docs/20 section 4
        if not should_retry or self.attempt_count >= self.max_attempts or error_class == "non_retryable":
            self.status = "dlq"
            # Create DLQ entry
            JobDLQ.objects.create(
                original_job=self,
                firm=self.firm,
                category=self.category,
                job_type=self.job_type,
                payload_version=self.payload_version,
                payload=self.payload,
                idempotency_key=self.idempotency_key,
                correlation_id=self.correlation_id,
                error_class=error_class,
                error_message=error_message,
                attempt_count=self.attempt_count,
                original_created_at=self.created_at,
            )
        else:
            # Schedule retry
            self.status = "pending"
            # Calculate backoff (exponential with jitter)
            import random
            base_delay = 2 ** self.attempt_count  # 2, 4, 8, 16, 32...
            jitter = random.uniform(0.8, 1.2)
            delay_seconds = min(base_delay * jitter, 300)  # Max 5 minutes

            from datetime import timedelta
            self.next_retry_at = timezone.now() + timedelta(seconds=delay_seconds)

        self.save()


class JobDLQ(models.Model):
    """
    Dead Letter Queue for failed jobs.

    Implements docs/20 section 4: DLQ with viewable/reprocessable items and audit trail.
    """

    STATUS_CHOICES = [
        ("pending_review", "Pending Review"),
        ("reprocessing", "Reprocessing"),
        ("resolved", "Resolved"),
        ("discarded", "Discarded"),
    ]

    # Identity
    dlq_id = models.BigAutoField(primary_key=True)

    # Original job reference
    original_job = models.ForeignKey(
        JobQueue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dlq_entries",
        help_text="Original job that failed (nullable if job is purged)",
    )

    # Tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="job_dlq",
        help_text="Firm this DLQ entry belongs to",
    )

    # Job metadata (preserved from original per docs/20 section 4)
    category = models.CharField(max_length=20)
    job_type = models.CharField(max_length=100)
    payload_version = models.CharField(max_length=10)
    payload = models.JSONField(help_text="Original payload preserved for reprocessing")
    idempotency_key = models.CharField(max_length=255)
    correlation_id = models.UUIDField()

    # Failure details
    error_class = models.CharField(
        max_length=50,
        help_text="Error classification from original failure",
    )
    error_message = models.TextField(
        help_text="Error message from original failure (redacted)",
    )
    attempt_count = models.IntegerField(
        help_text="Number of attempts before DLQ",
    )

    # DLQ status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending_review",
        help_text="DLQ processing status",
    )

    # Reprocessing tracking (per docs/20 section 4: reprocessing must be auditable)
    reprocessed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When item was reprocessed",
    )
    reprocessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reprocessed_dlq_items",
        help_text="Admin who initiated reprocessing",
    )
    reprocessing_notes = models.TextField(
        blank=True,
        help_text="Admin notes on reprocessing (why, what was fixed, etc.)",
    )
    new_job = models.ForeignKey(
        JobQueue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dlq_reprocessed_from",
        help_text="New job created from reprocessing",
    )

    # Timestamps
    original_created_at = models.DateTimeField(
        help_text="Original job creation time (preserved)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "job_dlq"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status", "created_at"], name="jobs_fir_sta_cre_idx"),
            models.Index(fields=["category", "status"], name="jobs_cat_sta_idx"),
            models.Index(fields=["error_class"], name="jobs_err_idx"),
            models.Index(fields=["idempotency_key"], name="jobs_ide_idx"),
            models.Index(fields=["correlation_id"], name="jobs_cor_idx"),
        ]

    def __str__(self):
        return f"DLQ: {self.category}:{self.job_type} [{self.status}]"

    @transaction.atomic
    def reprocess(self, user, notes: str = "") -> JobQueue:
        """
        Reprocess this DLQ item by creating a new job.

        Implements docs/20 section 4: reprocessable with audit trail.

        Args:
            user: Admin user initiating reprocessing
            notes: Reprocessing notes for audit

        Returns:
            New JobQueue instance
        """
        from modules.firm.audit import AuditEvent

        # Create audit event per docs/20 section 4
        AuditEvent.objects.create(
            firm=self.firm,
            event_category="admin",
            event_type="job_dlq_reprocess_requested",
            actor_user=user,
            resource_type="JobDLQ",
            resource_id=str(self.dlq_id),
            metadata={
                "dlq_id": self.dlq_id,
                "category": self.category,
                "job_type": self.job_type,
                "original_idempotency_key": self.idempotency_key,
                "notes": notes,
            },
        )

        # Create new job with fresh idempotency key (append retry suffix)
        new_idempotency_key = f"{self.idempotency_key}_retry_{timezone.now().timestamp()}"

        new_job = JobQueue.objects.create(
            firm=self.firm,
            category=self.category,
            job_type=self.job_type,
            payload_version=self.payload_version,
            payload={
                **self.payload,
                "idempotency_key": new_idempotency_key,
                "reprocessed_from_dlq_id": self.dlq_id,
            },
            idempotency_key=new_idempotency_key,
            correlation_id=self.correlation_id,
            status="pending",
            priority=0,  # High priority for reprocessed items
        )

        # Update DLQ status
        self.status = "reprocessing"
        self.reprocessed_at = timezone.now()
        self.reprocessed_by = user
        self.reprocessing_notes = notes
        self.new_job = new_job
        self.save()

        # Audit success
        AuditEvent.objects.create(
            firm=self.firm,
            event_category="admin",
            event_type="job_dlq_reprocess_success",
            actor_user=user,
            resource_type="JobDLQ",
            resource_id=str(self.dlq_id),
            metadata={
                "dlq_id": self.dlq_id,
                "new_job_id": str(new_job.job_id),
                "new_idempotency_key": new_idempotency_key,
            },
        )

        return new_job
