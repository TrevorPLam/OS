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
from modules.core.encryption import field_encryption_service
from modules.firm.utils import FirmScopedManager
from modules.projects.models import Project
from .documents import Document


class DocumentLock(models.Model):

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

