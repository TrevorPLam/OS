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
    STATUS_CHOICES = [
        ("active", "Active"),
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

    # DOC-14.1: Document status (active | archived per docs/14)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Document status (active or archived)",
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
            models.Index(fields=["firm", "document"]),
            models.Index(fields=["firm", "locked_by"]),
            models.Index(fields=["firm", "expires_at"]),
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
            models.Index(fields=["firm", "document", "-timestamp"]),
            models.Index(fields=["firm", "actor_user", "-timestamp"]),
            models.Index(fields=["firm", "action", "-timestamp"]),
            models.Index(fields=["correlation_id"]),
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