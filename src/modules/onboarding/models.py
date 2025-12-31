"""
Onboarding Models: OnboardingTemplate, OnboardingProcess, OnboardingTask, OnboardingDocument.

Implements Karbon-like client onboarding functionality:
- Standardized onboarding templates
- Automated document collection
- Progress tracking dashboard
- Auto-reminders for missing information

TIER 0: All onboarding entities MUST belong to exactly one Firm for tenant isolation.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from datetime import timedelta

from modules.firm.utils import FirmScopedManager
from modules.core.notifications import EmailNotification

import logging

logger = logging.getLogger(__name__)


class OnboardingTemplate(models.Model):
    """
    Onboarding template defining standardized client onboarding process.

    Templates define the steps, documents, and information required
    to onboard a new client successfully.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("archived", "Archived"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="onboarding_templates",
        help_text="Firm this template belongs to",
    )

    # Template identification
    name = models.CharField(max_length=255, help_text="Template name")
    description = models.TextField(blank=True, help_text="Template description")

    # Service type / industry
    service_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of service this onboarding is for",
    )

    # Template definition (JSON)
    # Structure: [{step_name, step_description, tasks: [{task_name, task_type, required, etc.}]}]
    steps = models.JSONField(
        default=list,
        help_text="Onboarding steps and tasks definition (JSON)",
    )

    # Duration estimate
    estimated_duration_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Estimated duration in days to complete onboarding",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Template status",
    )

    # Usage tracking
    times_used = models.IntegerField(
        default=0,
        help_text="Number of times this template has been used",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_onboarding_templates",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "onboarding_templates"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "status"], name="onboarding_fir_sta_idx"),
            models.Index(fields=["firm", "service_type"], name="onboarding_fir_ser_idx"),
        ]

    def __str__(self):
        return f"{self.name}"

    def mark_used(self):
        """Record template usage."""
        self.times_used += 1
        self.save(update_fields=["times_used"])


class OnboardingProcess(models.Model):
    """
    Active onboarding process for a client.

    Represents an instance of an onboarding template being executed
    for a specific client.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("waiting_client", "Waiting on Client"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="onboarding_processes",
        help_text="Firm this onboarding process belongs to",
    )

    # Template and client
    template = models.ForeignKey(
        OnboardingTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processes",
        help_text="Template this process is based on",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="onboarding_processes",
        help_text="Client being onboarded",
    )

    # Process details
    name = models.CharField(
        max_length=255,
        help_text="Process name (defaults to template name)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started",
        help_text="Current process status",
    )

    # Assigned staff
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_onboardings",
        help_text="Staff member responsible for this onboarding",
    )

    # Timeline
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When onboarding started",
    )
    target_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target date for completion",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When onboarding was completed",
    )

    # Progress tracking
    total_tasks = models.IntegerField(
        default=0,
        help_text="Total number of tasks in this onboarding",
    )
    completed_tasks = models.IntegerField(
        default=0,
        help_text="Number of completed tasks",
    )
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Completion percentage",
    )

    # Kick-off meeting
    kickoff_scheduled = models.BooleanField(
        default=False,
        help_text="Has kick-off meeting been scheduled?",
    )
    kickoff_completed = models.BooleanField(
        default=False,
        help_text="Has kick-off meeting been completed?",
    )
    kickoff_appointment = models.ForeignKey(
        "calendar.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_kickoffs",
        help_text="Kick-off meeting appointment",
    )

    # Notes and issues
    notes = models.TextField(blank=True, help_text="Internal notes")
    blockers = models.TextField(
        blank=True,
        help_text="Current blockers or issues",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_onboarding_processes",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "onboarding_processes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="onboarding_fir_sta_idx"),
            models.Index(fields=["firm", "-created_at"], name="onboarding_fir_cre_idx"),
            models.Index(fields=["client", "-created_at"], name="onboarding_cli_cre_idx"),
            models.Index(fields=["assigned_to", "status"], name="onboarding_ass_sta_idx"),
        ]

    def __str__(self):
        return f"{self.name} - {self.client.company_name}"

    def save(self, *args, **kwargs):
        """Auto-calculate progress percentage."""
        if self.total_tasks > 0:
            self.progress_percentage = (self.completed_tasks / self.total_tasks) * 100
        else:
            self.progress_percentage = 0
        super().save(*args, **kwargs)

    def start(self):
        """Mark onboarding as started."""
        if self.status == "not_started":
            self.status = "in_progress"
            self.started_at = timezone.now()
            self.save(update_fields=["status", "started_at"])

    def complete(self):
        """Mark onboarding as completed."""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save(update_fields=["status", "completed_at", "progress_percentage"])

    def update_progress(self):
        """Recalculate task completion progress."""
        completed = self.tasks.filter(status="completed").count()
        total = self.tasks.count()
        self.completed_tasks = completed
        self.total_tasks = total
        self.save(update_fields=["completed_tasks", "total_tasks", "progress_percentage"])


class OnboardingTask(models.Model):
    """
    Individual task within an onboarding process.

    Tasks can be information collection, document upload, form completion,
    or manual review steps.

    TIER 0: Belongs to exactly one Firm (via process relationship).
    """

    TASK_TYPE_CHOICES = [
        ("information", "Collect Information"),
        ("document", "Upload Document"),
        ("form", "Complete Form"),
        ("review", "Manual Review"),
        ("meeting", "Schedule Meeting"),
        ("approval", "Approval Required"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("blocked", "Blocked"),
        ("skipped", "Skipped"),
    ]

    # Relationship
    process = models.ForeignKey(
        OnboardingProcess,
        on_delete=models.CASCADE,
        related_name="tasks",
        help_text="Onboarding process this task belongs to",
    )

    # Task details
    name = models.CharField(max_length=255, help_text="Task name")
    description = models.TextField(blank=True, help_text="Task description")
    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPE_CHOICES,
        help_text="Type of task",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current task status",
    )

    # Sequencing
    step_number = models.IntegerField(
        help_text="Order of this task in the onboarding process",
    )
    depends_on = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dependent_tasks",
        help_text="Task that must be completed before this one",
    )

    # Requirements
    is_required = models.BooleanField(
        default=True,
        help_text="Is this task required for onboarding completion?",
    )
    assigned_to_client = models.BooleanField(
        default=False,
        help_text="Is this task assigned to the client to complete?",
    )

    # Timeline
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date for this task",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When task was completed",
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_onboarding_tasks",
        help_text="Who completed this task",
    )

    # Reminders
    reminder_sent = models.BooleanField(
        default=False,
        help_text="Has reminder been sent for this task?",
    )
    last_reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When last reminder was sent",
    )

    # Related objects
    related_document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_tasks",
        help_text="Document collected for this task",
    )

    # Notes
    notes = models.TextField(blank=True, help_text="Task notes")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "onboarding_tasks"
        ordering = ["process", "step_number"]
        indexes = [
            models.Index(fields=["process", "status"], name="onboarding_pro_sta_idx"),
            models.Index(fields=["process", "step_number"], name="onboarding_pro_ste_idx"),
            models.Index(fields=["status", "due_date"], name="onboarding_sta_due_idx"),
            models.Index(fields=["assigned_to_client", "status"], name="onboarding_ass_sta_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.process.name})"

    def complete(self, completed_by=None):
        """Mark task as completed."""
        self.status = "completed"
        self.completed_at = timezone.now()
        if completed_by:
            self.completed_by = completed_by
        self.save(update_fields=["status", "completed_at", "completed_by", "updated_at"])

        # Update parent process progress
        self.process.update_progress()

    def send_reminder(self):
        """Send reminder for incomplete task (if assigned to client)."""
        if self.assigned_to_client and self.status in ["pending", "in_progress"]:
            self.reminder_sent = True
            self.last_reminder_sent_at = timezone.now()
            self.save(update_fields=["reminder_sent", "last_reminder_sent_at"])
            
            # Send email notification to client
            try:
                client = self.process.client
                if client and client.primary_contact_email:
                    EmailNotification.send(
                        to=client.primary_contact_email,
                        subject=f"Reminder: {self.title} - {self.process.name}",
                        html_content=f"""
                            <h2>Onboarding Task Reminder</h2>
                            <p>Dear {client.primary_contact_name},</p>
                            <p>This is a friendly reminder about the following onboarding task:</p>
                            <p><strong>Task:</strong> {self.title}</p>
                            <p><strong>Description:</strong> {self.description or 'No description provided'}</p>
                            <p><strong>Due Date:</strong> {self.due_date.strftime('%B %d, %Y') if self.due_date else 'Not specified'}</p>
                            <p>Please complete this task at your earliest convenience to continue with your onboarding process.</p>
                            <p>If you have any questions, please don't hesitate to contact us.</p>
                            <p>Best regards,<br>{self.process.firm.name}</p>
                        """,
                    )
                    logger.info(
                        f"Sent onboarding task reminder to client {client.id} for task {self.id}",
                        extra={'task_id': self.id, 'client_id': client.id}
                    )
            except Exception as e:
                logger.error(
                    f"Failed to send onboarding task reminder: {str(e)}",
                    extra={'task_id': self.id, 'error': str(e)}
                )
            
            return True
        return False


class OnboardingDocument(models.Model):
    """
    Document collection tracking for onboarding.

    Links documents to onboarding processes and tracks collection status.

    TIER 0: Belongs to exactly one Firm (via process relationship).
    """

    STATUS_CHOICES = [
        ("required", "Required"),
        ("requested", "Requested from Client"),
        ("received", "Received"),
        ("reviewed", "Reviewed"),
        ("approved", "Approved"),
        ("rejected", "Rejected - Needs Update"),
    ]

    # Relationships
    process = models.ForeignKey(
        OnboardingProcess,
        on_delete=models.CASCADE,
        related_name="document_requirements",
        help_text="Onboarding process this document is for",
    )
    task = models.ForeignKey(
        OnboardingTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_requirements",
        help_text="Related onboarding task",
    )

    # Document details
    document_name = models.CharField(
        max_length=255,
        help_text="Name of required document",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what's needed",
    )
    document_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of document (e.g., 'W9', 'Operating Agreement')",
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="required",
        help_text="Document collection status",
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Is this document required?",
    )

    # Uploaded document
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_document_links",
        help_text="Uploaded document",
    )

    # Timeline
    requested_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When document was requested from client",
    )
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When document was received",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When document was approved",
    )

    # Review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_onboarding_documents",
        help_text="Staff member who reviewed this document",
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Review notes (e.g., rejection reason)",
    )

    # Reminders
    reminder_count = models.IntegerField(
        default=0,
        help_text="Number of reminders sent",
    )
    last_reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When last reminder was sent",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "onboarding_documents"
        ordering = ["process", "document_name"]
        indexes = [
            models.Index(fields=["process", "status"], name="onboarding_pro_sta_idx"),
            models.Index(fields=["status", "is_required"], name="onboarding_sta_is__idx"),
        ]

    def __str__(self):
        return f"{self.document_name} ({self.process.name})"

    def mark_received(self, document):
        """Mark document as received."""
        self.status = "received"
        self.document = document
        self.received_at = timezone.now()
        self.save(update_fields=["status", "document", "received_at", "updated_at"])

    def approve(self, reviewed_by, notes=""):
        """Approve the document."""
        self.status = "approved"
        self.reviewed_by = reviewed_by
        self.review_notes = notes
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "reviewed_by", "review_notes", "approved_at", "updated_at"])

    def reject(self, reviewed_by, notes):
        """Reject the document (needs update from client)."""
        self.status = "rejected"
        self.reviewed_by = reviewed_by
        self.review_notes = notes
        self.save(update_fields=["status", "reviewed_by", "review_notes", "updated_at"])

    def send_reminder(self):
        """Send reminder for missing document."""
        if self.status in ["required", "requested", "rejected"]:
            self.reminder_count += 1
            self.last_reminder_sent_at = timezone.now()
            if self.status == "required":
                self.status = "requested"
                self.requested_at = timezone.now()
            self.save(update_fields=["reminder_count", "last_reminder_sent_at", "status", "requested_at"])
            
            # Send email notification to client
            try:
                client = self.process.client
                if client and client.primary_contact_email:
                    status_message = {
                        'required': 'is required',
                        'requested': 'has been requested',
                        'rejected': 'was rejected and needs to be re-submitted'
                    }.get(self.status, 'is required')
                    
                    EmailNotification.send(
                        to=client.primary_contact_email,
                        subject=f"Document Reminder: {self.document_name} - {self.process.name}",
                        html_content=f"""
                            <h2>Onboarding Document Reminder</h2>
                            <p>Dear {client.primary_contact_name},</p>
                            <p>This is a reminder about the following document for your onboarding process:</p>
                            <p><strong>Document:</strong> {self.document_name}</p>
                            <p><strong>Description:</strong> {self.description or 'No description provided'}</p>
                            <p><strong>Status:</strong> This document {status_message}</p>
                            {f'<p><strong>Rejection Reason:</strong> {self.rejection_reason}</p>' if self.status == 'rejected' and self.rejection_reason else ''}
                            <p>Please upload this document at your earliest convenience to continue with your onboarding process.</p>
                            <p>If you have any questions, please don't hesitate to contact us.</p>
                            <p>Best regards,<br>{self.process.firm.name}</p>
                        """,
                    )
                    logger.info(
                        f"Sent onboarding document reminder to client {client.id} for document {self.id}",
                        extra={'document_id': self.id, 'client_id': client.id}
                    )
            except Exception as e:
                logger.error(
                    f"Failed to send onboarding document reminder: {str(e)}",
                    extra={'document_id': self.id, 'error': str(e)}
                )
            
            return True
        return False
