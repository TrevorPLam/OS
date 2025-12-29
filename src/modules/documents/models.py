"""
Documents Models: Folder, Document, Version.

Implements S3-backed secure document storage with versioning.
Supports hierarchical folders and client portal access.

TIER 0: All documents belong to exactly one Firm for tenant isolation.
"""

from typing import Any

from django.conf import settings
from django.db import models

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
            models.Index(fields=["firm", "client", "parent"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "visibility"]),  # TIER 0: Firm scoping
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
    Document entity.

    Represents a file stored in S3.
    Supports versioning through the Version model.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Folder/Client, but included directly for efficient queries.
    """

    VISIBILITY_CHOICES = [
        ("internal", "Internal Only"),
        ("client", "Visible to Client"),
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
            models.Index(fields=["firm", "client", "folder"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "visibility"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "s3_fingerprint"]),  # TIER 0: Firm scoping
        ]
        # TIER 0: S3 keys must be unique within a firm (not globally)
        unique_together = [["firm", "s3_fingerprint"]]

    def __str__(self) -> str:
        return f"{self.folder} / {self.name}"

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


class Version(models.Model):
    """
    Version entity (Document Version History).

    Tracks all versions of a document.
    Each upload creates a new Version record.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Document, but included directly for efficient queries.
    """

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
            models.Index(fields=["firm", "document", "version_number"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "s3_fingerprint"]),  # TIER 0: Firm scoping
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
