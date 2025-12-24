"""
Documents Models: Folder, Document, Version.

Implements S3-backed secure document storage with versioning.
Supports hierarchical folders and client portal access.
"""
from django.db import models
from django.contrib.auth.models import User
from modules.projects.models import Project


class Folder(models.Model):
    """
    Folder entity (Hierarchical structure).

    Represents a folder in the document management system.
    Supports nested folders (self-referential relationship).
    """
    VISIBILITY_CHOICES = [
        ('internal', 'Internal Only'),
        ('client', 'Visible to Client'),
    ]

    # Relationships - UPDATED to reference clients.Client
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='folders',
        help_text="Firm (workspace) this folder belongs to"
    )
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_folders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents_folders'
        ordering = ['name']
        indexes = [
            models.Index(fields=['firm', 'client', 'parent']),
        ]
        unique_together = [['firm', 'client', 'parent', 'name']]

    def __str__(self):
        if self.parent:
            return f"{self.parent} / {self.name}"
        return f"{self.client.company_name} / {self.name}"

    def save(self, *args, **kwargs):
        """Ensure firm is aligned with the client firm."""
        if self.client_id:
            if self.firm_id and self.firm_id != self.client.firm_id:
                raise ValueError("Folder firm must match client firm.")
            if not self.firm_id:
                self.firm = self.client.firm
        super().save(*args, **kwargs)


class Document(models.Model):
    """
    Document entity.

    Represents a file stored in S3.
    Supports versioning through the Version model.
    """
    VISIBILITY_CHOICES = [
        ('internal', 'Internal Only'),
        ('client', 'Visible to Client'),
    ]

    # Relationships - UPDATED to reference clients.Client
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Firm (workspace) this document belongs to"
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

    # Versioning
    current_version = models.IntegerField(
        default=1,
        help_text="Current version number"
    )

    # Audit Fields
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'client', 'folder']),
        ]

    def __str__(self):
        return f"{self.folder} / {self.name}"

    def save(self, *args, **kwargs):
        """Ensure firm is aligned with the folder/client firm."""
        if self.folder_id:
            if self.firm_id and self.firm_id != self.folder.firm_id:
                raise ValueError("Document firm must match folder firm.")
            if not self.firm_id:
                self.firm = self.folder.firm
        if self.client_id and self.firm_id and self.firm_id != self.client.firm_id:
            raise ValueError("Document firm must match client firm.")
        super().save(*args, **kwargs)


class DocumentContent(models.Model):
    """
    Content storage metadata for a document.

    Separated to keep content pointers isolated from metadata access.
    """
    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='content'
    )
    s3_key = models.CharField(
        max_length=500,
        unique=True,
        help_text="S3 object key (path in bucket)"
    )
    s3_bucket = models.CharField(
        max_length=255,
        help_text="S3 bucket name"
    )

    class Meta:
        db_table = 'documents_document_content'

    def __str__(self):
        return f"{self.document} content"


class Version(models.Model):
    """
    Version entity (Document Version History).

    Tracks all versions of a document.
    Each upload creates a new Version record.
    """
    # Relationships
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='document_versions',
        help_text="Firm (workspace) this document version belongs to"
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

    # Audit Fields
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_versions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documents_versions'
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['firm', 'document', 'version_number']),
        ]
        unique_together = [['firm', 'document', 'version_number']]

    def __str__(self):
        return f"{self.document.name} (v{self.version_number})"

    def save(self, *args, **kwargs):
        """Ensure firm is aligned with the document firm."""
        if self.document_id:
            if self.firm_id and self.firm_id != self.document.firm_id:
                raise ValueError("Document version firm must match document firm.")
            if not self.firm_id:
                self.firm = self.document.firm
        super().save(*args, **kwargs)


class VersionContent(models.Model):
    """
    Content storage metadata for a document version.
    """
    version = models.OneToOneField(
        Version,
        on_delete=models.CASCADE,
        related_name='content'
    )
    s3_key = models.CharField(
        max_length=500,
        unique=True,
        help_text="S3 object key for this version"
    )
    s3_bucket = models.CharField(max_length=255)

    class Meta:
        db_table = 'documents_version_content'

    def __str__(self):
        return f"{self.version} content"
