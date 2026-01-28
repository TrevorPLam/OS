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


class Document(models.Model):
    """
    Document entity (Governed Artifact per docs/03-reference/requirements/DOC-14.md DOCUMENTS_AND_STORAGE_SPEC).

    Represents a file stored in S3.
    Supports versioning through the Version model.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Folder/Client, but included directly for efficient queries.

    DOC-14.1: Documents are governed artifacts, not unmanaged blobs.
    """

    VISIBILITY_CHOICES = [
        ("internal", "Internal Only"),
        ("client", "Visible to Client"),
    ]

    # DOC-14.1: Document status (per docs/03-reference/requirements/DOC-14.md section 2.1)
    # Extended with approval workflow (Tracked in TODO: T-089)
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "Under Review"),
        ("approved", "Approved"),
        ("published", "Published"),
        ("active", "Active"),  # Legacy status - treated as published
        ("deprecated", "Deprecated"),
        ("archived", "Archived"),
    ]

    # DOC-07.1: Classification levels (per DATA_GOVERNANCE)
    CLASSIFICATION_CHOICES = [
        ("PUB", "Public"),
        ("INT", "Internal"),
        ("CONF", "Confidential"),
        ("R-PII", "Restricted PII"),
        ("HR", "Highly Restricted"),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Firm (workspace) this document belongs to",
    )

    # Relationships - UPDATED to reference clients.Client
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Parent folder",
    )

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Denormalized for quick filtering (post-sale client)",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Optional: link to specific project",
    )

    # Document Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default="internal",
        help_text="Can clients see this document in the portal?",
    )

    # DOC-14.1: Document status with approval workflow (Tracked in TODO: T-089)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Document status (draft → review → approved → published)",
    )
    
    # Approval workflow fields (Tracked in TODO: T-089)
    submitted_for_review_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_submitted_for_review",
        help_text="User who submitted the document for review",
    )
    submitted_for_review_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the document was submitted for review",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_reviewed",
        help_text="User who reviewed/approved the document",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the document was reviewed/approved",
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Reviewer notes/feedback",
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_published",
        help_text="User who published the document",
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the document was published",
    )
    deprecated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_deprecated",
        help_text="User who deprecated the document",
    )
    deprecated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the document was deprecated",
    )
    deprecation_reason = models.TextField(
        blank=True,
        help_text="Reason for deprecating the document",
    )

    # DOC-07.1: Data classification (per DATA_GOVERNANCE)
    classification = models.CharField(
        max_length=10,
        choices=CLASSIFICATION_CHOICES,
        default="CONF",
        help_text="Data classification level for governance",
    )

    # File Metadata (for current version)
    file_type = models.CharField(max_length=50, help_text="MIME type (e.g., application/pdf, image/png)")
    file_size_bytes = models.BigIntegerField(help_text="File size in bytes")

    # S3 Storage
    s3_key = models.TextField(
        help_text="Encrypted S3 object key (path in bucket, unique per firm)",
    )
    s3_bucket = models.TextField(help_text="Encrypted S3 bucket name")
    s3_fingerprint = models.CharField(
        max_length=128,
        editable=False,
        db_index=True,
        default="",
        help_text="Deterministic fingerprint for uniqueness checks",
    )

    # Versioning
    current_version = models.IntegerField(default=1, help_text="Current version number")

    # Document Retention Policy (Simple feature 1.7)
    retention_policy = models.CharField(
        max_length=50, blank=True, help_text="Retention policy name (e.g., '7years', 'permanent', 'standard')"
    )
    retention_period_years = models.IntegerField(
        null=True, blank=True, help_text="Number of years to retain document (null = permanent)"
    )
    retention_start_date = models.DateField(
        null=True, blank=True, help_text="Date when retention period starts (usually creation date)"
    )
    scheduled_deletion_date = models.DateField(
        null=True, blank=True, help_text="Date when document is scheduled for deletion (if applicable)"
    )

    # Legal Hold (Simple feature 1.8)
    legal_hold = models.BooleanField(
        default=False, help_text="Whether document is under legal hold (prevents deletion)"
    )
    legal_hold_reason = models.TextField(
        blank=True, help_text="Reason for legal hold (e.g., litigation, investigation)"
    )
    legal_hold_applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applied_legal_holds",
        help_text="User who applied the legal hold",
    )
    legal_hold_applied_at = models.DateTimeField(null=True, blank=True, help_text="When legal hold was applied")

    # Audit Fields
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="uploaded_documents"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "documents_documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "client", "folder"]),  # TIER 0: Firm scoping, name="documents_fir_cli_fol_idx")
            models.Index(fields=["firm", "visibility"]),  # TIER 0: Firm scoping, name="documents_fir_vis_idx")
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping, name="documents_fir_cre_idx")
            models.Index(fields=["firm", "s3_fingerprint"]),  # TIER 0: Firm scoping, name="documents_fir_s3__idx")
        ]
        # TIER 0: S3 keys must be unique within a firm (not globally)
        unique_together = [["firm", "s3_fingerprint"]]

    def __str__(self) -> str:
        return f"{self.folder} / {self.name}"
    
    def submit_for_review(self, user) -> None:
        """
        Submit document for review (draft → review).
        
        Validates that document is in draft status and sets review tracking fields.
        """
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        if self.status != "draft":
            raise ValidationError(f"Cannot submit for review: document is in '{self.status}' status, must be 'draft'.")
        
        self.status = "review"
        self.submitted_for_review_by = user
        self.submitted_for_review_at = timezone.now()
        self.save(update_fields=["status", "submitted_for_review_by", "submitted_for_review_at", "updated_at"])
    
    def approve(self, user, notes: str = "") -> None:
        """
        Approve document (review → approved).
        
        Validates that document is under review and sets approval tracking fields.
        """
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        if self.status != "review":
            raise ValidationError(f"Cannot approve: document is in '{self.status}' status, must be 'review'.")
        
        self.status = "approved"
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_notes", "updated_at"])
    
    def reject(self, user, notes: str) -> None:
        """
        Reject document and return to draft (review → draft).
        
        Validates that document is under review and records rejection notes.
        """
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        if self.status != "review":
            raise ValidationError(f"Cannot reject: document is in '{self.status}' status, must be 'review'.")
        
        if not notes:
            raise ValidationError("Rejection notes are required.")
        
        self.status = "draft"
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        # Clear submission fields to allow resubmission
        self.submitted_for_review_by = None
        self.submitted_for_review_at = None
        self.save(update_fields=[
            "status", "reviewed_by", "reviewed_at", "review_notes",
            "submitted_for_review_by", "submitted_for_review_at", "updated_at"
        ])
    
    def publish(self, user) -> None:
        """
        Publish document (approved → published).
        
        Validates that document is approved and sets publication tracking fields.
        """
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        if self.status not in ["approved", "active"]:  # Support legacy "active" status
            raise ValidationError(
                f"Cannot publish: document is in '{self.status}' status, must be 'approved' or 'active'."
            )
        
        self.status = "published"
        self.published_by = user
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_by", "published_at", "updated_at"])
    
    def deprecate(self, user, reason: str) -> None:
        """
        Deprecate document (published → deprecated).
        
        Validates that document is published and records deprecation reason.
        """
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        if self.status not in ["published", "active"]:  # Support legacy "active" status
            raise ValidationError(
                f"Cannot deprecate: document is in '{self.status}' status, must be 'published' or 'active'."
            )
        
        if not reason:
            raise ValidationError("Deprecation reason is required.")
        
        self.status = "deprecated"
        self.deprecated_by = user
        self.deprecated_at = timezone.now()
        self.deprecation_reason = reason
        self.save(update_fields=["status", "deprecated_by", "deprecated_at", "deprecation_reason", "updated_at"])
    
    def archive(self) -> None:
        """
        Archive document (deprecated → archived or any status → archived).
        
        Archives can be performed from any status but typically from deprecated.
        """
        from django.utils import timezone
        
        self.status = "archived"
        self.save(update_fields=["status", "updated_at"])

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Set retention_start_date to created_at date if not provided
        if not self.retention_start_date and not self.pk:
            # For new documents, set to today
            from django.utils import timezone

            self.retention_start_date = timezone.now().date()

        # Calculate scheduled_deletion_date if retention period is set
        if self.retention_period_years and self.retention_start_date and not self.scheduled_deletion_date:
            from dateutil.relativedelta import relativedelta

            self.scheduled_deletion_date = self.retention_start_date + relativedelta(years=self.retention_period_years)

        self._encrypt_content_fields()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """
        Validate Document data integrity.

        Validates:
        - Firm consistency: folder.firm == client.firm == self.firm
        - Legal hold consistency: legal_hold requires reason and applied_by
        - Retention validation: retention_period requires retention_start_date
        - Legal hold prevents scheduled deletion
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency with folder
        if self.folder_id and self.firm_id:
            if hasattr(self, "folder") and self.folder.firm_id != self.firm_id:
                errors["folder"] = "Document firm must match folder's firm."

        # Firm consistency with client
        if self.client_id and self.firm_id:
            if hasattr(self, "client") and self.client.firm_id != self.firm_id:
                errors["client"] = "Document firm must match client's firm."

        # Legal hold consistency
        if self.legal_hold:
            if not self.legal_hold_reason:
                errors["legal_hold_reason"] = "Legal hold reason is required when document is under legal hold."
            if not self.legal_hold_applied_by_id:
                errors["legal_hold_applied_by"] = "Legal hold applied by is required when document is under legal hold."

        # Retention validation
        if self.retention_period_years and not self.retention_start_date:
            errors["retention_start_date"] = "Retention start date is required when retention period is set."

        # Legal hold prevents scheduled deletion
        if self.legal_hold and self.scheduled_deletion_date:
            errors["scheduled_deletion_date"] = (
                "Scheduled deletion date should be cleared when document is under legal hold."
            )

        if errors:
            raise ValidationError(errors)

    def decrypted_s3_key(self) -> str:
        return field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_key)

    def decrypted_s3_bucket(self) -> str:
        return field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_bucket)

    def _encrypt_content_fields(self) -> None:
        if not self.firm_id:
            return

        decrypted_bucket = field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_bucket)
        decrypted_key = field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_key)

        self.s3_bucket = field_encryption_service.encrypt_for_firm(self.firm_id, decrypted_bucket)
        self.s3_key = field_encryption_service.encrypt_for_firm(self.firm_id, decrypted_key)

        fingerprint_source = f"{decrypted_bucket}:{decrypted_key}" if decrypted_bucket or decrypted_key else None
        self.s3_fingerprint = field_encryption_service.fingerprint_for_firm(self.firm_id, fingerprint_source) or ""


class DocumentComment(models.Model):
    """
    Document comment model (COMM-1).

    Enables threaded comments on documents with @mentions, notifications,
    and full comment history tracking.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="document_comments",
        help_text="Firm (workspace) this comment belongs to",
    )

    # Associated document
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="The document this comment is on",
    )

    # Threading support
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        help_text="Parent comment for threaded replies (null = top-level comment)",
    )

    # Comment content
    body = models.TextField(
        help_text="Comment text content",
    )

    # @mentions
    mentions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of mentioned user IDs (staff users)",
    )

    # Edit/delete tracking
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the comment was last edited",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Soft delete timestamp (tombstone preserved)",
    )

    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="document_comments_created",
        help_text="User who created this comment",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "documents_comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["firm", "document", "created_at"], name="doc_com_fir_doc_cre_idx"),
            models.Index(fields=["firm", "parent_comment"], name="doc_com_fir_par_idx"),
            models.Index(fields=["firm", "created_by", "-created_at"], name="doc_com_fir_cre_by_idx"),
        ]

    def __str__(self) -> str:
        return f"Comment on {self.document.name} by {self.created_by}"

    @property
    def is_deleted(self) -> bool:
        """Check if comment has been soft deleted."""
        return self.deleted_at is not None

    @property
    def is_reply(self) -> bool:
        """Check if this is a reply to another comment."""
        return self.parent_comment_id is not None

    def clean(self) -> None:
        """Validate comment data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.document_id and self.firm_id:
            if hasattr(self, "document") and self.document.firm_id != self.firm_id:
                errors["document"] = "Comment firm must match document's firm."

        # Parent comment validation
        if self.parent_comment_id and hasattr(self, "parent_comment"):
            # Parent must belong to same document
            if self.document_id and self.parent_comment.document_id != self.document_id:
                errors["parent_comment"] = "Parent comment must belong to the same document."
            # Parent must belong to same firm
            if self.firm_id and self.parent_comment.firm_id != self.firm_id:
                errors["parent_comment"] = "Parent comment must belong to the same firm."

        # Prevent circular reference
        if self.pk and self.parent_comment_id:
            if self.parent_comment_id == self.pk:
                errors["parent_comment"] = "Comment cannot be its own parent."

        if errors:
            raise ValidationError(errors)


class DocumentViewLog(models.Model):
    """
    Document view tracking model (COMM-2).

    Tracks when users (staff and portal) view documents for read receipts.
    Provides view timestamps, read status indicators, and view notifications.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    VIEWER_TYPE_CHOICES = [
        ("staff", "Staff User"),
        ("portal", "Portal User"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="document_view_logs",
        help_text="Firm (workspace) this view log belongs to",
    )

    # Document being viewed
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="view_logs",
        help_text="The document that was viewed",
    )

    # Viewer information
    viewer_type = models.CharField(
        max_length=10,
        choices=VIEWER_TYPE_CHOICES,
        help_text="Type of viewer (staff or portal)",
    )
    viewer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_views",
        help_text="Staff user who viewed the document",
    )
    viewer_portal_user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Portal user ID if viewer_type='portal'",
    )
    viewer_contact = models.ForeignKey(
        "clients.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_views",
        help_text="Contact who viewed the document (for portal users)",
    )

    # View tracking
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the document was viewed",
    )
    view_duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="How long the document was viewed (if tracked)",
    )

    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the viewer",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string",
    )

    # Notification tracking
    notification_sent = models.BooleanField(
        default=False,
        help_text="Whether notification was sent for this view",
    )
    notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was sent",
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional view metadata",
    )

    # TIER 0: Manager
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "documents_view_logs"
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(fields=["firm", "document", "-viewed_at"], name="doc_vie_fir_doc_vie_idx"),
            models.Index(fields=["firm", "viewer_user", "-viewed_at"], name="doc_vie_fir_vie_use_idx"),
            models.Index(fields=["firm", "viewer_portal_user_id", "-viewed_at"], name="doc_vie_fir_vie_por_idx"),
            models.Index(fields=["firm", "viewer_type", "-viewed_at"], name="doc_vie_fir_vie_typ_idx"),
        ]

    def __str__(self) -> str:
        viewer = self.viewer_user if self.viewer_user else f"Portal User {self.viewer_portal_user_id}"
        return f"{viewer} viewed {self.document.name} at {self.viewed_at}"

    @classmethod
    def log_view(
        cls,
        firm_id: int,
        document: Document,
        viewer_type: str,
        viewer_user=None,
        viewer_portal_user_id: int = None,
        viewer_contact=None,
        view_duration_seconds: int = None,
        ip_address: str = None,
        user_agent: str = "",
        metadata: dict = None,
    ):
        """
        Convenience method to log a document view.

        Usage:
            DocumentViewLog.log_view(
                firm_id=document.firm_id,
                document=document,
                viewer_type="staff",
                viewer_user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
            )
        """
        return cls.objects.create(
            firm_id=firm_id,
            document=document,
            viewer_type=viewer_type,
            viewer_user=viewer_user,
            viewer_portal_user_id=viewer_portal_user_id,
            viewer_contact=viewer_contact,
            view_duration_seconds=view_duration_seconds,
            ip_address=ip_address,
            user_agent=user_agent[:1000] if user_agent else "",  # Truncate
            metadata=metadata or {},
        )

    def clean(self) -> None:
        """Validate view log data."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.document_id and self.firm_id:
            if hasattr(self, "document") and self.document.firm_id != self.firm_id:
                errors["document"] = "View log firm must match document's firm."

        # Viewer validation
        if self.viewer_type == "staff" and not self.viewer_user_id:
            errors["viewer_user"] = "Viewer user is required for staff views."
        if self.viewer_type == "portal" and not self.viewer_portal_user_id:
            errors["viewer_portal_user_id"] = "Portal user ID is required for portal views."

        if errors:
            raise ValidationError(errors)
