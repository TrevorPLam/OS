"""
Email Ingestion Models.

Implements email ingestion from Gmail/Outlook with governed artifact storage,
mapping suggestions, triage workflow, and audit trail.

Complies with docs/15 EMAIL_INGESTION_SPEC.
"""

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class EmailConnection(models.Model):
    """
    Email connection configuration (Gmail/Outlook).

    Represents a configured email connection for a firm.
    """

    PROVIDER_CHOICES = [
        ("gmail", "Gmail"),
        ("outlook", "Outlook"),
        ("other", "Other"),
    ]

    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="email_connections",
        help_text="Firm this connection belongs to",
    )

    name = models.CharField(max_length=255, help_text="Human-readable connection name")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    email_address = models.EmailField(help_text="Email address being monitored")

    # OAuth/API credentials (encrypted at rest)
    credentials_encrypted = models.TextField(
        blank=True, help_text="Encrypted OAuth credentials or API tokens"
    )

    # Status
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_email_connections",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "email_ingestion_connections"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="emailinges_fir_is__idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.email_address})"


class EmailArtifact(models.Model):
    """
    EmailArtifact model (per docs/15 section 2.1).

    Represents an ingested email message with governance and mapping.
    """

    STATUS_CHOICES = [
        ("ingested", "Ingested"),
        ("mapped", "Mapped"),
        ("triage", "Needs Triage"),
        ("ignored", "Ignored"),
    ]

    # Identity
    email_artifact_id = models.BigAutoField(primary_key=True)

    # Connection and provider info
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="email_artifacts",
        help_text="Firm this artifact belongs to",
    )
    connection = models.ForeignKey(
        EmailConnection,
        on_delete=models.CASCADE,
        related_name="artifacts",
        help_text="Email connection that ingested this message",
    )
    provider = models.CharField(
        max_length=20,
        choices=EmailConnection.PROVIDER_CHOICES,
        help_text="Email provider (gmail, outlook, other)",
    )

    # External identifiers (per docs/15 section 2.1)
    external_message_id = models.CharField(
        max_length=512, help_text="Provider's unique message ID (required; unique per connection)"
    )
    thread_id = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="Provider's thread/conversation ID (nullable)",
    )

    # Email metadata (governed fields - R-PII per docs/15 section 2.1)
    from_address = models.EmailField(help_text="Sender email address (governed: R-PII)")
    to_addresses = models.TextField(help_text="Recipient email addresses, comma-separated (governed: R-PII)")
    cc_addresses = models.TextField(
        blank=True, default="", help_text="CC email addresses, comma-separated (governed: R-PII)"
    )
    subject = models.TextField(help_text="Email subject line (governed)")

    # Timestamps
    sent_at = models.DateTimeField(help_text="When the email was sent (per provider)")
    received_at = models.DateTimeField(help_text="When the email was received (per provider)")

    # Content
    body_preview = models.TextField(
        max_length=500, blank=True, help_text="Bounded preview of email body (max 500 chars)"
    )
    storage_ref = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_artifacts",
        help_text="Optional: full MIME stored as a governed document",
    )

    # Status and mapping
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="ingested", help_text="Current processing status"
    )

    # Mapping suggestions (nullable; populated by mapping engine)
    suggested_account = models.ForeignKey(
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggested_emails",
        help_text="Suggested Client mapping",
    )
    suggested_engagement = models.ForeignKey(
        "clients.ClientEngagement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggested_emails",
        help_text="Suggested Engagement mapping",
    )
    suggested_work_item = models.ForeignKey(
        "projects.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggested_emails",
        help_text="Suggested Task mapping",
    )
    mapping_confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Mapping confidence score (0.00 to 1.00)",
    )
    mapping_reasons = models.TextField(
        blank=True, help_text="Human-readable reasons for mapping suggestion"
    )

    # Confirmed mappings (set after review/approval)
    confirmed_account = models.ForeignKey(
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_emails",
        help_text="Confirmed Client mapping (after review)",
    )
    confirmed_engagement = models.ForeignKey(
        "clients.ClientEngagement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_emails",
        help_text="Confirmed Engagement mapping (after review)",
    )
    confirmed_work_item = models.ForeignKey(
        "projects.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_emails",
        help_text="Confirmed Task mapping (after review)",
    )

    # Ignored reason (if status = ignored)
    ignored_reason = models.TextField(blank=True, help_text="Reason for marking as ignored")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_emails",
        help_text="Staff member who reviewed/confirmed mapping",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "email_ingestion_artifacts"
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="emailinges_fir_sta_idx"),
            models.Index(fields=["firm", "sent_at"], name="emailinges_fir_sen_idx"),
            models.Index(fields=["connection", "external_message_id"], name="emailinges_con_ext_idx"),
            models.Index(fields=["suggested_account"], name="emailinges_sug_idx"),
            models.Index(fields=["confirmed_account"], name="emailinges_con_idx"),
        ]
        # Uniqueness constraint per docs/15 section 2.1
        unique_together = [["connection", "external_message_id"]]

    def __str__(self):
        return f"Email from {self.from_address}: {self.subject[:50]}"

    def clean(self):
        """Validate EmailArtifact data integrity."""
        errors = {}

        # Firm consistency
        if self.connection_id and self.firm_id:
            if hasattr(self, "connection") and self.connection.firm_id != self.firm_id:
                errors["connection"] = "Email artifact firm must match connection's firm."

        # Mapping confidence must be between 0 and 1
        if self.mapping_confidence is not None:
            if not (Decimal("0") <= self.mapping_confidence <= Decimal("1")):
                errors["mapping_confidence"] = "Mapping confidence must be between 0.00 and 1.00"

        # If status is ignored, must have a reason
        if self.status == "ignored" and not self.ignored_reason:
            errors["ignored_reason"] = "Ignored emails must have a reason."

        if errors:
            raise ValidationError(errors)

    def confirm_mapping(self, account=None, engagement=None, work_item=None, user=None):
        """
        Confirm mapping for this email (per docs/15 section 5 correction workflow).

        Creates an audit event and updates confirmed mapping fields.
        """
        from modules.firm.audit import AuditEvent

        old_account_id = self.confirmed_account_id
        old_engagement_id = self.confirmed_engagement_id
        old_work_item_id = self.confirmed_work_item_id

        self.confirmed_account = account
        self.confirmed_engagement = engagement
        self.confirmed_work_item = work_item
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.status = "mapped" if (account or engagement or work_item) else self.status
        self.save()

        # Audit event per docs/15 section 5
        AuditEvent.objects.create(
            firm=self.firm,
            event_category="data",
            event_type="email_mapping_confirmed",
            actor_user=user,
            resource_type="EmailArtifact",
            resource_id=str(self.email_artifact_id),
            metadata={
                "old_account_id": old_account_id,
                "new_account_id": account.pk if account else None,
                "old_engagement_id": old_engagement_id,
                "new_engagement_id": engagement.pk if engagement else None,
                "old_work_item_id": old_work_item_id,
                "new_work_item_id": work_item.pk if work_item else None,
                "subject": self.subject[:100],
            },
        )

    def mark_ignored(self, reason, user=None):
        """
        Mark this email as ignored with a reason (per docs/15 section 5).

        Creates an audit event.
        """
        from modules.firm.audit import AuditEvent

        self.status = "ignored"
        self.ignored_reason = reason
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save()

        # Audit event
        AuditEvent.objects.create(
            firm=self.firm,
            event_category="data",
            event_type="email_marked_ignored",
            actor_user=user,
            resource_type="EmailArtifact",
            resource_id=str(self.email_artifact_id),
            metadata={
                "reason": reason,
                "subject": self.subject[:100],
            },
        )


class EmailAttachment(models.Model):
    """
    EmailAttachment linking table.

    Links EmailArtifact to Document (per docs/15 section 2.2).
    Each attachment is stored as a governed Document.
    """

    email_artifact = models.ForeignKey(
        EmailArtifact,
        on_delete=models.CASCADE,
        related_name="attachments",
        help_text="Email this attachment belongs to",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="email_attachments",
        help_text="Governed document storing this attachment",
    )

    # Original metadata from email
    original_filename = models.CharField(max_length=255, help_text="Original attachment filename")
    content_type = models.CharField(max_length=100, help_text="MIME type from email")
    size_bytes = models.BigIntegerField(help_text="Attachment size in bytes")

    # Position in email
    attachment_index = models.IntegerField(
        help_text="Index of this attachment in the email (0-indexed)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_ingestion_attachments"
        ordering = ["email_artifact", "attachment_index"]
        indexes = [
            models.Index(fields=["email_artifact"], name="emailinges_ema_idx"),
            models.Index(fields=["document"], name="emailinges_doc_idx"),
        ]
        unique_together = [["email_artifact", "attachment_index"]]

    def __str__(self):
        return f"Attachment: {self.original_filename} ({self.email_artifact})"


class IngestionAttempt(models.Model):
    """
    IngestionAttempt / SyncAttemptLog model (per docs/15 section 2.3).

    Records every ingestion attempt for retry-safety and debugging.
    Implements DOC-15.2: retry-safety with error classification.
    """

    OPERATION_CHOICES = [
        ("fetch", "Fetch"),
        ("parse", "Parse"),
        ("store", "Store"),
        ("map", "Map"),
    ]

    STATUS_CHOICES = [
        ("success", "Success"),
        ("fail", "Fail"),
    ]

    # Error classification for retry logic (per DOC-15.2)
    ERROR_CLASS_CHOICES = [
        ("transient", "Transient"),  # Temporary error, safe to retry
        ("retryable", "Retryable"),  # Retryable with backoff
        ("non_retryable", "Non-Retryable"),  # Permanent error, don't retry
        ("rate_limited", "Rate Limited"),  # Provider rate limit
    ]

    # Identity
    attempt_id = models.BigAutoField(primary_key=True)

    # Context
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="ingestion_attempts",
        help_text="Firm this attempt belongs to",
    )
    connection = models.ForeignKey(
        EmailConnection,
        on_delete=models.CASCADE,
        related_name="ingestion_attempts",
        help_text="Email connection for this attempt",
    )
    email_artifact = models.ForeignKey(
        EmailArtifact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ingestion_attempts",
        help_text="Email artifact (nullable if failed before create)",
    )

    # Attempt details
    operation = models.CharField(
        max_length=20, choices=OPERATION_CHOICES, help_text="Operation being attempted"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, help_text="Attempt status")
    error_summary = models.TextField(
        blank=True, help_text="Redacted error summary (no PII, no content)"
    )
    error_class = models.CharField(
        max_length=20,
        choices=ERROR_CLASS_CHOICES,
        null=True,
        blank=True,
        help_text="Error classification for retry logic (DOC-15.2)",
    )

    # Retry tracking (DOC-15.2)
    retry_count = models.IntegerField(
        default=0, help_text="Number of times this operation has been retried"
    )
    next_retry_at = models.DateTimeField(
        null=True, blank=True, help_text="Scheduled time for next retry (if applicable)"
    )
    max_retries_reached = models.BooleanField(
        default=False, help_text="Whether max retry attempts have been exhausted"
    )

    # Observability (per docs/21 OBSERVABILITY)
    correlation_id = models.UUIDField(
        null=True, blank=True, help_text="Correlation ID for tracing across systems"
    )

    # Timing
    occurred_at = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(
        null=True, blank=True, help_text="Operation duration in milliseconds"
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "email_ingestion_attempts"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["firm", "occurred_at"], name="emailinges_fir_occ_idx"),
            models.Index(fields=["connection", "status"], name="emailinges_con_sta_idx"),
            models.Index(fields=["email_artifact"], name="emailinges_ema_idx"),
            models.Index(fields=["correlation_id"], name="emailinges_cor_idx"),
            models.Index(fields=["status", "error_class"], name="emailinges_sta_err_idx"),
            models.Index(fields=["next_retry_at"], name="emailinges_nex_idx"),
            models.Index(fields=["max_retries_reached"], name="emailinges_max_idx"),
        ]

    def __str__(self):
        status_icon = "✓" if self.status == "success" else "✗"
        return f"{status_icon} {self.operation} for {self.connection} at {self.occurred_at}"
