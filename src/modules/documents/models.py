"""
Documents Models: Folder, Document, Version.

Implements S3-backed secure document storage with versioning.
Supports hierarchical folders and client portal access.

TIER 0: All documents belong to exactly one Firm for tenant isolation.
"""

import uuid
from typing import Any

import bcrypt
from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.core.encryption import field_encryption_service
from modules.firm.utils import FirmScopedManager
from modules.projects.models import Project


class Folder(models.Model):
    """
    Folder entity (Hierarchical structure).

    Represents a folder in the document management system.
    Supports nested folders (self-referential relationship).

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Client, but included directly for efficient queries.
    """

    VISIBILITY_CHOICES = [
        ("internal", "Internal Only"),
        ("client", "Visible to Client"),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="folders",
        help_text="Firm (workspace) this folder belongs to",
    )

    # Relationships - UPDATED to reference clients.Client
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="folders",
        help_text="The post-sale client who owns this folder",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="folders",
        help_text="Optional: link to specific project",
    )

    # Folder Hierarchy
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subfolders",
        help_text="Parent folder (null = root folder)",
    )

    # Folder Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default="internal",
        help_text="Can clients see this folder in the portal?",
    )

    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_folders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "documents_folders"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "client", "parent"]),  # TIER 0: Firm scoping, name="documents_fir_cli_par_idx")
            models.Index(fields=["firm", "visibility"]),  # TIER 0: Firm scoping, name="documents_fir_vis_idx")
        ]
        # TIER 0: Folder names must be unique within firm+client+parent (not globally)
        unique_together = [["firm", "client", "parent", "name"]]

    def __str__(self) -> str:
        if self.parent:
            return f"{self.parent} / {self.name}"
        return f"{self.client.company_name} / {self.name}"

    def clean(self) -> None:
        """
        Validate Folder data integrity.

        Validates:
        - Firm consistency: client.firm == self.firm
        - Hierarchy validation: parent folder must belong to same firm and client
        - Prevents circular parent references
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency with client
        if self.client_id and self.firm_id:
            if hasattr(self, "client") and self.client.firm_id != self.firm_id:
                errors["client"] = "Folder firm must match client's firm."

        # Parent folder validation
        if self.parent_id:
            if hasattr(self, "parent"):
                # Parent must belong to same firm
                if self.firm_id and self.parent.firm_id != self.firm_id:
                    errors["parent"] = "Parent folder must belong to the same firm."
                # Parent must belong to same client
                if self.client_id and self.parent.client_id != self.client_id:
                    errors["parent"] = "Parent folder must belong to the same client."

        # Prevent circular reference
        if self.pk and self.parent_id:
            if self.parent_id == self.pk:
                errors["parent"] = "Folder cannot be its own parent."

        if errors:
            raise ValidationError(errors)


class Document(models.Model):
    """
    Document entity (Governed Artifact per docs/14 DOCUMENTS_AND_STORAGE_SPEC).

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

    # DOC-14.1: Document status (per docs/14 section 2.1)
    # Extended with approval workflow (TODO 2.7)
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
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="documents")
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

    # DOC-14.1: Document status with approval workflow (TODO 2.7)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Document status (draft → review → approved → published)",
    )
    
    # Approval workflow fields (TODO 2.7)
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


class DocumentLock(models.Model):
    """
    Document locking model (DOC-14.3 per docs/14 section 5).

    Implements exclusive locking for documents to prevent concurrent edits.

    Rules (per docs/14):
    1. If locked, only the lock holder (or Admin override) may upload a new version.
    2. Overrides MUST be auditable.
    3. Locks expire or require explicit release.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="document_locks",
        help_text="Firm (workspace) this lock belongs to",
    )

    # Document being locked (one active lock per document)
    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name="lock",
        help_text="The document this lock applies to",
    )

    # Lock holder
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_locks",
        help_text="User who holds the lock",
    )

    # Lock metadata
    locked_at = models.DateTimeField(auto_now_add=True, help_text="When the lock was acquired")
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the lock expires (null = no auto-expiry)",
    )
    lock_reason = models.TextField(
        blank=True,
        help_text="Optional reason for the lock",
    )

    # Admin override tracking (DOC-14.3)
    override_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_lock_overrides",
        help_text="Admin who overrode this lock (if any)",
    )
    override_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the lock was overridden",
    )
    override_reason = models.TextField(
        blank=True,
        help_text="Reason for the admin override (required for audit)",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "documents_locks"
        indexes = [
            models.Index(fields=["firm", "document"], name="documents_fir_doc_idx"),
            models.Index(fields=["firm", "locked_by"], name="documents_fir_loc_idx"),
            models.Index(fields=["firm", "expires_at"], name="documents_fir_exp_idx"),
        ]

    def __str__(self) -> str:
        return f"Lock on {self.document.name} by {self.locked_by}"

    @property
    def is_expired(self) -> bool:
        """Check if the lock has expired."""
        if self.expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def is_overridden(self) -> bool:
        """Check if an admin has overridden this lock."""
        return self.override_by_id is not None

    def can_upload(self, user) -> bool:
        """
        Check if a user can upload a new version while this lock exists.

        Returns True if:
        - User is the lock holder
        - Lock has been overridden
        - Lock has expired
        """
        if self.is_expired:
            return True
        if self.is_overridden:
            return True
        return self.locked_by_id == user.id

    def clean(self) -> None:
        """Validate lock data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.document_id and self.firm_id:
            if hasattr(self, "document") and self.document.firm_id != self.firm_id:
                errors["document"] = "Lock firm must match document's firm."

        # Override requires reason
        if self.override_by_id and not self.override_reason:
            errors["override_reason"] = "Override reason is required when lock is overridden."

        if errors:
            raise ValidationError(errors)

class Version(models.Model):
    """
    Version entity (DocumentVersion per docs/14 DOCUMENTS_AND_STORAGE_SPEC).

    Tracks all versions of a document.
    Each upload creates a new Version record.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Document, but included directly for efficient queries.

    DOC-14.1: DocumentVersion MUST be immutable. New uploads create new versions.
    """

    # DOC-14.1: Virus scan status (per docs/14 section 2.2 and section 6)
    SCAN_STATUS_CHOICES = [
        ("pending", "Pending Scan"),
        ("clean", "Clean"),
        ("flagged", "Flagged (Malware Detected)"),
        ("skipped", "Scan Skipped"),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="document_versions",
        help_text="Firm (workspace) this version belongs to",
    )

    # Relationships
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")

    # Version Details
    version_number = models.IntegerField()
    change_summary = models.TextField(blank=True, help_text="What changed in this version?")

    # File Metadata
    file_type = models.CharField(max_length=50)
    file_size_bytes = models.BigIntegerField()

    # DOC-14.1: Checksum for integrity verification (per docs/14 section 2.2)
    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 checksum of file content for integrity verification",
    )

    # DOC-14.1: Virus scan status (per docs/14 sections 2.2 and 6)
    virus_scan_status = models.CharField(
        max_length=20,
        choices=SCAN_STATUS_CHOICES,
        default="pending",
        help_text="Malware scan status for this version",
    )
    virus_scan_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the virus scan was completed",
    )
    virus_scan_result_detail = models.TextField(
        blank=True,
        help_text="Additional scan result details (e.g., detection name if flagged)",
    )

    # S3 Storage (each version has its own S3 object)
    s3_key = models.TextField(
        help_text="Encrypted S3 object key for this version (unique per firm)",
    )
    s3_bucket = models.TextField()
    s3_fingerprint = models.CharField(
        max_length=128,
        editable=False,
        db_index=True,
        default="",
        help_text="Deterministic fingerprint for version content",
    )

    # Audit Fields
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="uploaded_versions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "documents_versions"
        ordering = ["-version_number"]
        indexes = [
            models.Index(fields=["firm", "document", "version_number"]),  # TIER 0: Firm scoping, name="documents_fir_doc_ver_idx")
            models.Index(fields=["firm", "s3_fingerprint"]),  # TIER 0: Firm scoping, name="documents_fir_s3__idx")
        ]
        # TIER 0: Version numbers unique within firm+document, S3 keys unique within firm
        unique_together = [["firm", "document", "version_number"], ["firm", "s3_fingerprint"]]

    def __str__(self) -> str:
        return f"{self.document.name} (v{self.version_number})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self._encrypt_content_fields()
        super().save(*args, **kwargs)

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

class DocumentAccessLog(models.Model):
    """
    Document access logging model (DOC-14.2 per docs/14 sections 3.4 and docs/7).

    Tracks all access to governed artifacts for audit purposes.
    This is metadata-only - no content is logged.

    Per docs/7 section 3.4 and docs/14:
    - document download/view
    - document version upload
    - URL issuance (signed URL generation)

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    # Access action types
    ACTION_CHOICES = [
        ("url_issued", "Signed URL Issued"),
        ("download", "Download"),
        ("upload", "Upload"),
        ("view", "View"),
        ("version_created", "Version Created"),
        ("lock_acquired", "Lock Acquired"),
        ("lock_released", "Lock Released"),
        ("lock_overridden", "Lock Overridden"),
    ]

    # Actor type
    ACTOR_TYPE_CHOICES = [
        ("staff", "Staff User"),
        ("portal", "Portal User"),
        ("system", "System/Background Job"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="document_access_logs",
        help_text="Firm (workspace) this log belongs to",
    )

    # Document/Version reference
    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        related_name="access_logs",
        help_text="The document accessed (null if deleted)",
    )
    version = models.ForeignKey(
        Version,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_logs",
        help_text="Specific version accessed (if applicable)",
    )

    # Access details
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of access action",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Actor information
    actor_type = models.CharField(
        max_length=10,
        choices=ACTOR_TYPE_CHOICES,
        help_text="Type of actor (staff, portal, system)",
    )
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_access_logs",
        help_text="User who performed the action (if applicable)",
    )
    actor_portal_user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Portal user ID if actor is a portal user",
    )

    # Tracing
    correlation_id = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Correlation ID for request tracing",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string (truncated for logging)",
    )

    # Additional metadata (no content - per governance rules)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (must not contain document content or PII)",
    )

    # TIER 0: Manager (no firm_scoped needed - these are audit records)
    objects = models.Manager()

    class Meta:
        db_table = "documents_access_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["firm", "document", "-timestamp"], name="doc_acc_fir_doc_tim_idx"),
            models.Index(fields=["firm", "actor_user", "-timestamp"], name="doc_acc_fir_act_usr_idx"),
            models.Index(fields=["firm", "action", "-timestamp"], name="doc_acc_fir_act_tim_idx"),
            models.Index(fields=["correlation_id"], name="doc_acc_cor_idx"),
        ]

    def __str__(self) -> str:
        doc_name = self.document.name if self.document else "[deleted]"
        return f"{self.action} on {doc_name} at {self.timestamp}"

    @classmethod
    def log_access(
        cls,
        firm_id: int,
        document: "Document",
        action: str,
        actor_type: str,
        actor_user=None,
        actor_portal_user_id: int = None,
        version: "Version" = None,
        correlation_id: str = "",
        ip_address: str = None,
        user_agent: str = "",
        metadata: dict = None,
    ):
        """
        Convenience method to create an access log entry.

        Usage:
            DocumentAccessLog.log_access(
                firm_id=document.firm_id,
                document=document,
                action="download",
                actor_type="staff",
                actor_user=request.user,
                correlation_id=get_correlation_id(request),
            )
        """
        return cls.objects.create(
            firm_id=firm_id,
            document=document,
            version=version,
            action=action,
            actor_type=actor_type,
            actor_user=actor_user,
            actor_portal_user_id=actor_portal_user_id,
            correlation_id=correlation_id or "",
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else "",  # Truncate
            metadata=metadata or {},
        )


class ExternalShare(models.Model):
    """
    External document sharing model (Task 3.10).
    
    Enables secure token-based sharing of documents with external parties
    without requiring authentication. Supports password protection, expiration,
    download limits, and comprehensive access tracking.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    ACCESS_TYPE_CHOICES = [
        ("view", "View Only"),
        ("download", "Download"),
        ("comment", "View & Comment"),
        ("upload", "Upload Only"),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="external_shares",
        help_text="Firm (workspace) this share belongs to",
    )
    
    # Document being shared (nullable for upload-only shares)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="external_shares",
        help_text="The document being shared externally (null for upload-only shares)",
    )
    
    # Share token (UUID for secure public access)
    share_token = models.UUIDField(
        unique=True,
        db_index=True,
        editable=False,
        help_text="Unique token for accessing this share",
    )
    
    # Share configuration
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default="view",
        help_text="Type of access granted",
    )
    
    # Password protection
    require_password = models.BooleanField(
        default=False,
        help_text="Whether password is required to access",
    )
    password_hash = models.CharField(
        max_length=128,
        blank=True,
        help_text="Bcrypt hash of the password (if required)",
    )
    
    # Expiration and limits
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this share expires (null = no expiration)",
    )
    max_downloads = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of downloads allowed (null = unlimited)",
    )
    download_count = models.IntegerField(
        default=0,
        help_text="Current number of downloads",
    )
    
    # Revocation
    revoked = models.BooleanField(
        default=False,
        help_text="Whether this share has been revoked",
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this share was revoked",
    )
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_shares",
        help_text="User who revoked this share",
    )
    revoke_reason = models.TextField(
        blank=True,
        help_text="Reason for revocation",
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_shares",
        help_text="User who created this share",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "documents_external_shares"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "document"], name="doc_ext_fir_doc_idx"),
            models.Index(fields=["firm", "created_by"], name="doc_ext_fir_cre_idx"),
            models.Index(fields=["expires_at"], name="doc_ext_exp_idx"),
            models.Index(fields=["revoked"], name="doc_ext_rev_idx"),
        ]
    
    def __str__(self) -> str:
        return f"Share: {self.document.name} ({self.share_token})"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        # Generate share token on creation
        if not self.share_token:
            self.share_token = uuid.uuid4()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self) -> bool:
        """Check if the share has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_download_limit_reached(self) -> bool:
        """Check if download limit has been reached."""
        if self.max_downloads is None:
            return False
        return self.download_count >= self.max_downloads
    
    @property
    def is_active(self) -> bool:
        """Check if the share is currently active and accessible."""
        return not self.revoked and not self.is_expired and not self.is_download_limit_reached
    
    def verify_password(self, password: str) -> bool:
        """
        Verify the provided password against the stored hash.
        
        Args:
            password: The password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        if not self.require_password:
            return True
        
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def set_password(self, password: str) -> None:
        """
        Set the password for this share.
        
        Args:
            password: The plaintext password to hash and store
        """
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        self.require_password = True
    
    def revoke(self, user: Any, reason: str = "") -> None:
        """
        Revoke this share.
        
        Args:
            user: The user revoking the share
            reason: Optional reason for revocation
        """
        self.revoked = True
        self.revoked_at = timezone.now()
        self.revoked_by = user
        self.revoke_reason = reason
        self.save(update_fields=["revoked", "revoked_at", "revoked_by", "revoke_reason", "updated_at"])
    
    def increment_download_count(self) -> None:
        """Increment the download counter."""
        self.download_count += 1
        self.save(update_fields=["download_count", "updated_at"])
    
    def clean(self) -> None:
        """Validate external share data."""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Firm consistency
        if self.document_id and self.firm_id:
            if hasattr(self, "document") and self.document.firm_id != self.firm_id:
                errors["document"] = "Share firm must match document's firm."
        
        # Password validation
        if self.require_password and not self.password_hash:
            errors["password_hash"] = "Password hash is required when password protection is enabled."
        
        # Download limit validation
        if self.max_downloads is not None and self.max_downloads < 0:
            errors["max_downloads"] = "Max downloads must be non-negative."
        
        if errors:
            raise ValidationError(errors)


class SharePermission(models.Model):
    """
    Share permission configuration model (Task 3.10).
    
    Defines detailed permissions for external shares including
    print control, watermark settings, and other fine-grained controls.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="share_permissions",
        help_text="Firm (workspace) this permission belongs to",
    )
    
    # Associated share
    external_share = models.OneToOneField(
        ExternalShare,
        on_delete=models.CASCADE,
        related_name="permissions",
        help_text="The external share these permissions apply to",
    )
    
    # Permission flags
    allow_print = models.BooleanField(
        default=True,
        help_text="Allow printing the document",
    )
    allow_copy = models.BooleanField(
        default=True,
        help_text="Allow copying text from the document",
    )
    
    # Watermark settings
    apply_watermark = models.BooleanField(
        default=False,
        help_text="Whether to apply a watermark",
    )
    watermark_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Watermark text to display",
    )
    watermark_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional watermark settings (opacity, position, etc.)",
    )
    
    # IP restrictions
    allowed_ip_addresses = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed IP addresses/ranges (empty = no restriction)",
    )
    
    # Email notifications
    notify_on_access = models.BooleanField(
        default=False,
        help_text="Send notification when document is accessed",
    )
    notification_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Email addresses to notify on access",
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "documents_share_permissions"
        indexes = [
            models.Index(fields=["firm", "external_share"], name="doc_sha_fir_ext_idx"),
        ]
    
    def __str__(self) -> str:
        return f"Permissions for {self.external_share.share_token}"
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """
        Check if an IP address is allowed to access the share.
        
        Args:
            ip_address: The IP address to check
            
        Returns:
            True if allowed (or no restrictions), False otherwise
        """
        if not self.allowed_ip_addresses:
            return True
        
        # Simple exact match for now
        # Tracked in TODO: T-005 (Add CIDR Range Support for IP Whitelisting)
        return ip_address in self.allowed_ip_addresses
    
    def clean(self) -> None:
        """Validate share permission data."""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Firm consistency
        if self.external_share_id and self.firm_id:
            if hasattr(self, "external_share") and self.external_share.firm_id != self.firm_id:
                errors["external_share"] = "Permission firm must match share's firm."
        
        # Watermark validation
        if self.apply_watermark and not self.watermark_text:
            errors["watermark_text"] = "Watermark text is required when watermark is enabled."
        
        if errors:
            raise ValidationError(errors)


class ShareAccess(models.Model):
    """
    Share access tracking model (Task 3.10).
    
    Tracks all access attempts to external shares for audit and analytics.
    Records both successful and failed access attempts.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    ACTION_CHOICES = [
        ("view", "View"),
        ("download", "Download"),
        ("failed_password", "Failed Password"),
        ("failed_expired", "Failed - Expired"),
        ("failed_revoked", "Failed - Revoked"),
        ("failed_limit", "Failed - Download Limit"),
        ("failed_ip", "Failed - IP Restricted"),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="share_accesses",
        help_text="Firm (workspace) this access belongs to",
    )
    
    # Associated share
    external_share = models.ForeignKey(
        ExternalShare,
        on_delete=models.CASCADE,
        related_name="access_logs",
        help_text="The external share being accessed",
    )
    
    # Access details
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of access action",
    )
    success = models.BooleanField(
        help_text="Whether the access was successful",
    )
    accessed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the access occurred",
    )
    
    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string",
    )
    referer = models.TextField(
        blank=True,
        help_text="HTTP referer",
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional access metadata",
    )
    
    # TIER 0: Manager (no firm_scoped needed - these are audit records)
    objects = models.Manager()
    
    class Meta:
        db_table = "documents_share_accesses"
        ordering = ["-accessed_at"]
        indexes = [
            models.Index(fields=["firm", "external_share", "-accessed_at"], name="doc_sha_fir_ext_acc_idx"),
            models.Index(fields=["firm", "action", "-accessed_at"], name="doc_sha_fir_act_acc_idx"),
            models.Index(fields=["ip_address", "-accessed_at"], name="doc_sha_ip_acc_idx"),
        ]
    
    def __str__(self) -> str:
        status = "Success" if self.success else "Failed"
        return f"{self.action} - {status} at {self.accessed_at}"
    
    @classmethod
    def log_access(
        cls,
        firm_id: int,
        external_share: ExternalShare,
        action: str,
        success: bool,
        ip_address: str | None = None,
        user_agent: str = "",
        referer: str = "",
        metadata: dict | None = None,
    ):
        """
        Convenience method to log a share access attempt.
        
        Usage:
            ShareAccess.log_access(
                firm_id=share.firm_id,
                external_share=share,
                action="download",
                success=True,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
            )
        """
        return cls.objects.create(
            firm_id=firm_id,
            external_share=external_share,
            action=action,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent[:1000] if user_agent else "",  # Truncate
            referer=referer[:1000] if referer else "",  # Truncate
            metadata=metadata or {},
        )


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
        help_text="The upload-only share link for this request",
    )

    # Destination folder for uploaded files
    destination_folder = models.ForeignKey(
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


class FolderComment(models.Model):
    """
    Folder comment model (COMM-1).

    Enables threaded comments on folders with @mentions, notifications,
    and full comment history tracking.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="folder_comments",
        help_text="Firm (workspace) this comment belongs to",
    )

    # Associated folder
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="The folder this comment is on",
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
        related_name="folder_comments_created",
        help_text="User who created this comment",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "documents_folder_comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["firm", "folder", "created_at"], name="doc_fol_fir_fol_cre_idx"),
            models.Index(fields=["firm", "parent_comment"], name="doc_fol_fir_par_idx"),
            models.Index(fields=["firm", "created_by", "-created_at"], name="doc_fol_fir_cre_by_idx"),
        ]

    def __str__(self) -> str:
        return f"Comment on {self.folder.name} by {self.created_by}"

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
        if self.folder_id and self.firm_id:
            if hasattr(self, "folder") and self.folder.firm_id != self.firm_id:
                errors["folder"] = "Comment firm must match folder's firm."

        # Parent comment validation
        if self.parent_comment_id and hasattr(self, "parent_comment"):
            # Parent must belong to same folder
            if self.folder_id and self.parent_comment.folder_id != self.folder_id:
                errors["parent_comment"] = "Parent comment must belong to the same folder."
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