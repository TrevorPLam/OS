import ipaddress
import uuid
from typing import Any

import bcrypt
from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.core.encryption import field_encryption_service
from modules.firm.utils import FirmScopedManager
from .documents import Document
from .versions import Version


class DocumentAccessLog(models.Model):
    """
    Document access logging model (DOC-14.2 per docs/03-reference/requirements/DOC-14.md sections 3.4 and docs/03-reference/requirements/DOC-07.md).

    Tracks all access to governed artifacts for audit purposes.
    This is metadata-only - no content is logged.

    Per docs/03-reference/requirements/DOC-07.md section 3.4 and docs/03-reference/requirements/DOC-14.md:
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

