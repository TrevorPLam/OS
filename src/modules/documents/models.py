"""
Documents Models: Folder, Document, Version.

Implements S3-backed secure document storage with versioning.
Supports hierarchical folders and client portal access.

TIER 0: All documents belong to exactly one Firm for tenant isolation.
"""
from django.conf import settings
from django.db import models
from modules.projects.models import Project
from modules.firm.utils import FirmScopedManager
from modules.core.encryption import field_encryption_service


class Folder(models.Model):
    """
    Folder entity (Hierarchical structure).

    Represents a folder in the document management system.
    Supports nested folders (self-referential relationship).

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Client, but included directly for efficient queries.
    """
    VISIBILITY_CHOICES = [
        ('internal', 'Internal Only'),
        ('client', 'Visible to Client'),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='folders',
        help_text="Firm (workspace) this folder belongs to"
    )

    # Relationships - UPDATED to reference clients.Client
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='folders',
        help_text="The post-sale client who owns this folder"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='folders',
        help_text="Optional: link to specific project"
    )

    # Folder Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders',
        help_text="Parent folder (null = root folder)"
    )

    # Folder Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='internal',
        help_text="Can clients see this folder in the portal?"
    )

    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_folders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'documents_folders'
        ordering = ['name']
        indexes = [
            models.Index(fields=['firm', 'client', 'parent']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'visibility']),  # TIER 0: Firm scoping
        ]
        # TIER 0: Folder names must be unique within firm+client+parent (not globally)
        unique_together = [['firm', 'client', 'parent', 'name']]

    def __str__(self):
        if self.parent:
            return f"{self.parent} / {self.name}"
        return f"{self.client.company_name} / {self.name}"


class Document(models.Model):
    """
    Document entity.

    Represents a file stored in S3.
    Supports versioning through the Version model.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Folder/Client, but included directly for efficient queries.
    """
    VISIBILITY_CHOICES = [
        ('internal', 'Internal Only'),
        ('client', 'Visible to Client'),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Firm (workspace) this document belongs to"
    )

    # Relationships - UPDATED to reference clients.Client
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Denormalized for quick filtering (post-sale client)"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Optional: link to specific project"
    )

    # Document Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='internal',
        help_text="Can clients see this document in the portal?"
    )

    # File Metadata (for current version)
    file_type = models.CharField(
        max_length=50,
        help_text="MIME type (e.g., application/pdf, image/png)"
    )
    file_size_bytes = models.BigIntegerField(
        help_text="File size in bytes"
    )

    # S3 Storage
    s3_key = models.TextField(
        help_text="Encrypted S3 object key (path in bucket, unique per firm)",
    )
    s3_bucket = models.TextField(
        help_text="Encrypted S3 bucket name"
    )
    s3_fingerprint = models.CharField(
        max_length=128,
        editable=False,
        db_index=True,
        default='',
        help_text="Deterministic fingerprint for uniqueness checks",
    )

    # Versioning
    current_version = models.IntegerField(
        default=1,
        help_text="Current version number"
    )
    
    # Document Retention Policy (Simple feature 1.7)
    retention_policy = models.CharField(
        max_length=50,
        blank=True,
        help_text="Retention policy name (e.g., '7years', 'permanent', 'standard')"
    )
    retention_period_years = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of years to retain document (null = permanent)"
    )
    retention_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when retention period starts (usually creation date)"
    )
    scheduled_deletion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when document is scheduled for deletion (if applicable)"
    )
    
    # Legal Hold (Simple feature 1.8)
    legal_hold = models.BooleanField(
        default=False,
        help_text="Whether document is under legal hold (prevents deletion)"
    )
    legal_hold_reason = models.TextField(
        blank=True,
        help_text="Reason for legal hold (e.g., litigation, investigation)"
    )
    legal_hold_applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applied_legal_holds',
        help_text="User who applied the legal hold"
    )
    legal_hold_applied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When legal hold was applied"
    )

    # Audit Fields
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'documents_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'client', 'folder']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'visibility']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', '-created_at']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 's3_fingerprint']),  # TIER 0: Firm scoping
        ]
        # TIER 0: S3 keys must be unique within a firm (not globally)
        unique_together = [['firm', 's3_fingerprint']]

    def __str__(self):
        return f"{self.folder} / {self.name}"

    def save(self, *args, **kwargs):
        self._encrypt_content_fields()
        super().save(*args, **kwargs)

    def decrypted_s3_key(self):
        return field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_key)

    def decrypted_s3_bucket(self):
        return field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_bucket)

    def _encrypt_content_fields(self):
        if not self.firm_id:
            return

        decrypted_bucket = field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_bucket)
        decrypted_key = field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_key)

        self.s3_bucket = field_encryption_service.encrypt_for_firm(self.firm_id, decrypted_bucket)
        self.s3_key = field_encryption_service.encrypt_for_firm(self.firm_id, decrypted_key)

        fingerprint_source = f"{decrypted_bucket}:{decrypted_key}" if decrypted_bucket or decrypted_key else None
        self.s3_fingerprint = field_encryption_service.fingerprint_for_firm(self.firm_id, fingerprint_source) or ''


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
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='document_versions',
        help_text="Firm (workspace) this version belongs to"
    )

    # Relationships
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )

    # Version Details
    version_number = models.IntegerField()
    change_summary = models.TextField(
        blank=True,
        help_text="What changed in this version?"
    )

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
        default='',
        help_text="Deterministic fingerprint for version content",
    )

    # Audit Fields
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_versions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'documents_versions'
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['firm', 'document', 'version_number']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 's3_fingerprint']),  # TIER 0: Firm scoping
        ]
        # TIER 0: Version numbers unique within firm+document, S3 keys unique within firm
        unique_together = [
            ['firm', 'document', 'version_number'],
            ['firm', 's3_fingerprint']
        ]

    def __str__(self):
        return f"{self.document.name} (v{self.version_number})"

    def save(self, *args, **kwargs):
        self._encrypt_content_fields()
        super().save(*args, **kwargs)

    def decrypted_s3_key(self):
        return field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_key)

    def decrypted_s3_bucket(self):
        return field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_bucket)

    def _encrypt_content_fields(self):
        if not self.firm_id:
            return

        decrypted_bucket = field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_bucket)
        decrypted_key = field_encryption_service.decrypt_for_firm(self.firm_id, self.s3_key)

        self.s3_bucket = field_encryption_service.encrypt_for_firm(self.firm_id, decrypted_bucket)
        self.s3_key = field_encryption_service.encrypt_for_firm(self.firm_id, decrypted_key)

        fingerprint_source = f"{decrypted_bucket}:{decrypted_key}" if decrypted_bucket or decrypted_key else None
        self.s3_fingerprint = field_encryption_service.fingerprint_for_firm(self.firm_id, fingerprint_source) or ''
