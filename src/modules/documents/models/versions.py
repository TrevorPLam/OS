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

