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


