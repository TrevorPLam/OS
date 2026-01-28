import ipaddress
import uuid
from typing import Any

import bcrypt
from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.core.encryption import field_encryption_service
from modules.firm.utils import FirmScopedManager
from modules.projects.models import Project
from .folders import Folder
from .shares import ExternalShare


class FileRequest(models.Model):
    """
    File request model for soliciting documents from clients/external parties.

    Enables creation of upload-only links with request templates, expiration,
    and status tracking. Links can be sent to clients to request specific documents
    like W2s, bank statements, tax returns, etc.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    # Request template types
    TEMPLATE_TYPE_CHOICES = [
        ("w2", "W-2 Form"),
        ("1099", "1099 Form"),
        ("bank_statement", "Bank Statement"),
        ("tax_return", "Tax Return"),
        ("pay_stub", "Pay Stub"),
        ("id_document", "ID Document"),
        ("contract", "Contract/Agreement"),
        ("invoice", "Invoice"),
        ("receipt", "Receipt"),
        ("other", "Other Document"),
    ]

    # Request status tracking
    STATUS_CHOICES = [
        ("pending", "Pending Upload"),
        ("partially_uploaded", "Partially Uploaded"),
        ("uploaded", "Uploaded"),
        ("reviewed", "Reviewed"),
        ("completed", "Completed"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="file_requests",
        help_text="Firm (workspace) this request belongs to",
    )

    # Associated client (optional - can request from external parties)
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="file_requests",
        help_text="Client this request is for (optional)",
    )

    # Associated external share (for the upload link)
    external_share = models.OneToOneField(
        ExternalShare,
        on_delete=models.CASCADE,
        related_name="file_request",
        help_text="External share for upload link",
    )

    # Destination folder
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name="file_requests",
        help_text="Folder where uploaded files will be stored",
    )

    # Request details
    title = models.CharField(
        max_length=255,
        help_text="Title/name of this request (e.g., 'Tax Documents for 2023')",
    )
    description = models.TextField(
        blank=True,
        help_text="Description/instructions for the recipient",
    )
    template_type = models.CharField(
        max_length=50,
        choices=TEMPLATE_TYPE_CHOICES,
        default="other",
        help_text="Type of document being requested",
    )

    # Request status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of the request",
    )

    # Recipient information
    recipient_email = models.EmailField(
        help_text="Email address of the recipient",
    )
    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of the recipient",
    )

    # Expiration and limits
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this request expires (synced with external_share.expires_at)",
    )
    max_files = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of files allowed (null = unlimited)",
    )
    uploaded_file_count = models.IntegerField(
        default=0,
        help_text="Number of files uploaded so far",
    )

    # Request configuration
    require_specific_files = models.BooleanField(
        default=False,
        help_text="Whether specific file names are required",
    )
    required_file_names = models.JSONField(
        default=list,
        blank=True,
        help_text="List of required file names (if require_specific_files is True)",
    )
    allowed_file_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed MIME types (empty = all types allowed)",
    )

    # Reminders
    enable_reminders = models.BooleanField(
        default=True,
        help_text="Whether to send automated reminders",
    )
    reminder_sent_count = models.IntegerField(
        default=0,
        help_text="Number of reminders sent",
    )
    last_reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last reminder was sent",
    )

    # Notifications
    notify_on_upload = models.BooleanField(
        default=True,
        help_text="Send notification when files are uploaded",
    )
    notification_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional email addresses to notify on upload",
    )

    # Completion tracking
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was completed",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_file_requests",
        help_text="User who reviewed the uploaded files",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the files were reviewed",
    )

    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_file_requests",
        help_text="User who created this request",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "documents_file_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "client"], name="doc_fil_fir_cli_idx"),
            models.Index(fields=["firm", "status"], name="doc_fil_fir_sta_idx"),
            models.Index(fields=["firm", "created_by"], name="doc_fil_fir_cre_idx"),
            models.Index(fields=["expires_at"], name="doc_fil_exp_idx"),
            models.Index(fields=["status", "enable_reminders"], name="doc_fil_sta_ena_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.recipient_email}"

    @property
    def is_expired(self) -> bool:
        """Check if the request has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_file_limit_reached(self) -> bool:
        """Check if file upload limit has been reached."""
        if self.max_files is None:
            return False
        return self.uploaded_file_count >= self.max_files

    @property
    def is_active(self) -> bool:
        """Check if the request is currently active."""
        return (
            self.status in ["pending", "partially_uploaded"]
            and not self.is_expired
            and not self.is_file_limit_reached
        )

    def mark_as_uploaded(self) -> None:
        """Mark request as uploaded when files are received."""
        if self.status == "pending":
            self.status = "partially_uploaded" if self.require_specific_files else "uploaded"
        elif self.status == "partially_uploaded" and not self.require_specific_files:
            self.status = "uploaded"
        self.save(update_fields=["status", "updated_at"])

    def mark_as_completed(self, user: Any) -> None:
        """Mark request as completed."""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "reviewed_by", "reviewed_at", "updated_at"])

    def increment_upload_count(self) -> None:
        """Increment the uploaded file counter."""
        self.uploaded_file_count += 1
        self.save(update_fields=["uploaded_file_count", "updated_at"])

    def clean(self) -> None:
        """Validate file request data."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.client_id and self.firm_id:
            if hasattr(self, "client") and self.client.firm_id != self.firm_id:
                errors["client"] = "Request firm must match client's firm."

        if self.destination_folder_id and self.firm_id:
            if hasattr(self, "destination_folder") and self.destination_folder.firm_id != self.firm_id:
                errors["destination_folder"] = "Request firm must match folder's firm."

        if self.external_share_id and self.firm_id:
            if hasattr(self, "external_share") and self.external_share.firm_id != self.firm_id:
                errors["external_share"] = "Request firm must match share's firm."

        # Validate specific file requirements
        if self.require_specific_files and not self.required_file_names:
            errors["required_file_names"] = "Required file names must be specified when specific files are required."

        # Validate max_files
        if self.max_files is not None and self.max_files < 0:
            errors["max_files"] = "Max files must be non-negative."

        if errors:
            raise ValidationError(errors)


class FileRequestReminder(models.Model):
    """
    File request reminder tracking model.

    Tracks reminder sequences for file requests including scheduled reminders
    at configurable intervals (Day 1, 3, 7, 14, etc.) and escalation to team members.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    REMINDER_TYPE_CHOICES = [
        ("initial", "Initial Reminder"),
        ("followup", "Follow-up Reminder"),
        ("escalation", "Escalation Notice"),
        ("final", "Final Reminder"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="file_request_reminders",
        help_text="Firm (workspace) this reminder belongs to",
    )

    # Associated file request
    file_request = models.ForeignKey(
        FileRequest,
        on_delete=models.CASCADE,
        related_name="reminders",
        help_text="The file request this reminder is for",
    )

    # Reminder configuration
    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPE_CHOICES,
        default="followup",
        help_text="Type of reminder",
    )
    days_after_creation = models.IntegerField(
        help_text="Number of days after request creation to send this reminder",
    )

    # Reminder content
    subject = models.CharField(
        max_length=255,
        help_text="Email subject for this reminder",
    )
    message = models.TextField(
        help_text="Email message body for this reminder",
    )

    # Escalation settings
    escalate_to_team = models.BooleanField(
        default=False,
        help_text="Whether to escalate to team members",
    )
    escalation_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Team member email addresses to escalate to",
    )

    # Scheduling
    scheduled_for = models.DateTimeField(
        help_text="When this reminder is scheduled to be sent",
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this reminder was actually sent",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ("scheduled", "Scheduled"),
            ("sent", "Sent"),
            ("skipped", "Skipped"),
            ("failed", "Failed"),
        ],
        default="scheduled",
        help_text="Status of this reminder",
    )
    failure_reason = models.TextField(
        blank=True,
        help_text="Reason if reminder failed to send",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Manager
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "documents_file_request_reminders"
        ordering = ["scheduled_for"]
        indexes = [
            models.Index(fields=["firm", "file_request"], name="doc_rem_fir_req_idx"),
            models.Index(fields=["scheduled_for", "status"], name="doc_rem_sch_sta_idx"),
            models.Index(fields=["firm", "status"], name="doc_rem_fir_sta_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.reminder_type} for {self.file_request.title} - {self.scheduled_for}"

    def mark_as_sent(self) -> None:
        """Mark reminder as sent."""
        self.status = "sent"
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at", "updated_at"])

    def mark_as_failed(self, reason: str) -> None:
        """Mark reminder as failed."""
        self.status = "failed"
        self.failure_reason = reason
        self.save(update_fields=["status", "failure_reason", "updated_at"])

    def mark_as_skipped(self) -> None:
        """Mark reminder as skipped (e.g., request already completed)."""
        self.status = "skipped"
        self.save(update_fields=["status", "updated_at"])

    def clean(self) -> None:
        """Validate reminder data."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.file_request_id and self.firm_id:
            if hasattr(self, "file_request") and self.file_request.firm_id != self.firm_id:
                errors["file_request"] = "Reminder firm must match request's firm."

        # Escalation validation
        if self.escalate_to_team and not self.escalation_emails:
            errors["escalation_emails"] = "Escalation emails must be specified when escalating to team."

        if errors:
            raise ValidationError(errors)


