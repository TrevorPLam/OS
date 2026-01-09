"""
TIER 3: Audit Event System

Implements structured, immutable audit logging for all critical platform events.

CRITICAL REQUIREMENTS (from NOTES_TO_CLAUDE.md):
- Audit events must be categorized (auth, billing, break-glass, purge)
- Logs must have defined retention windows
- Ownership of audit review must be defined
- Break-glass actions must be immutably audited
- Purge operations must be fully logged

Meta-commentary:
- **Current Status:** Audit model complete; automatic emission wired for config changes only.
- **Follow-up (T-045):** Add Sentry breadcrumbs for critical audit events.
- **Assumption:** Content is never logged (metadata only) per privacy-first design.
- **Missing:** Retention policy enforcement (manual cleanup required; no TTL automation).
- **Limitation:** Audit records are immutable (no updates, only creates) per Tier 3 governance.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from config.sentry import capture_message_with_context

class AuditEvent(models.Model):
    """
    Immutable audit event record.

    Tracks all critical platform actions for compliance, security, and debugging.

    SECURITY GUARANTEES:
    - Immutable: No updates allowed after creation
    - Tenant-scoped: All events belong to a Firm
    - Content-free: Only metadata, no customer content
    - Tamper-evident: Includes hash chain (future enhancement)

    PRIVACY:
    - Never logs customer content (documents, messages, notes)
    - Only logs metadata (IDs, timestamps, actions, outcomes)
    - Suitable for break-glass review without exposing sensitive data
    """

    # Event Categories (as per Tier 3 requirements)
    CATEGORY_AUTH = "AUTH"
    CATEGORY_PERMISSIONS = "PERMISSIONS"
    CATEGORY_BREAK_GLASS = "BREAK_GLASS"
    CATEGORY_BILLING_METADATA = "BILLING_METADATA"
    CATEGORY_PURGE = "PURGE"
    CATEGORY_CONFIG = "CONFIG"
    CATEGORY_DATA_ACCESS = "DATA_ACCESS"
    CATEGORY_SYSTEM = "SYSTEM"

    CATEGORY_CHOICES = [
        (CATEGORY_AUTH, "Authentication & Authorization"),
        (CATEGORY_PERMISSIONS, "Permission Changes"),
        (CATEGORY_BREAK_GLASS, "Break-Glass Access"),
        (CATEGORY_BILLING_METADATA, "Billing Metadata"),
        (CATEGORY_PURGE, "Content Purge"),
        (CATEGORY_CONFIG, "Configuration Changes"),
        (CATEGORY_DATA_ACCESS, "Data Access"),
        (CATEGORY_SYSTEM, "System Events"),
    ]

    # Severity Levels
    SEVERITY_INFO = "INFO"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_CRITICAL = "CRITICAL"

    SEVERITY_CHOICES = [
        (SEVERITY_INFO, "Informational"),
        (SEVERITY_WARNING, "Warning - Requires Review"),
        (SEVERITY_CRITICAL, "Critical - Immediate Review Required"),
    ]

    # Core Fields (required for all events)
    id = models.BigAutoField(primary_key=True)

    # Tenant Context (REQUIRED for tenant isolation)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.PROTECT,  # Never delete audit records
        related_name="audit_events",
        help_text="Firm (tenant) this event belongs to",
    )

    # Event Classification
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, db_index=True, help_text="Event category for filtering and review"
    )

    action = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Specific action taken (e.g., 'login_failed', 'purge_document', 'break_glass_activated')",
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_INFO,
        db_index=True,
        help_text="Event severity for prioritization",
    )

    # Actor (who performed the action)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events_as_actor",
        help_text="User who performed the action (null for system events)",
    )

    actor_email = models.EmailField(blank=True, help_text="Email at time of action (preserved even if user deleted)")

    actor_role = models.CharField(max_length=50, blank=True, help_text="User's role at time of action")

    # Target (what was acted upon)
    target_model = models.CharField(
        max_length=100, blank=True, help_text="Model name of target object (e.g., 'Client', 'Document')"
    )

    target_id = models.CharField(max_length=255, blank=True, help_text="ID of target object")

    target_repr = models.CharField(
        max_length=500, blank=True, help_text="Human-readable representation of target (no sensitive data)"
    )

    # Event Details
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, help_text="When the event occurred")

    reason = models.TextField(blank=True, help_text="Reason for action (required for break-glass, purge, etc.)")

    outcome = models.CharField(
        max_length=50, blank=True, help_text="Result of action (e.g., 'success', 'denied', 'failed')"
    )

    # Metadata (JSON for extensibility, NO CUSTOMER CONTENT)
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional context (metadata only, never customer content)"
    )

    # Request Context
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of request")

    user_agent = models.CharField(max_length=500, blank=True, help_text="User agent string")

    request_id = models.CharField(max_length=100, blank=True, db_index=True, help_text="Request ID for correlation")

    # Review Tracking
    reviewed_at = models.DateTimeField(
        null=True, blank=True, help_text="When this event was reviewed (for anomaly detection)"
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events_reviewed",
        help_text="Who reviewed this event",
    )

    review_notes = models.TextField(blank=True, help_text="Notes from review")

    class Meta:
        db_table = "firm_audit_events"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["firm", "category", "-timestamp"]),
            models.Index(fields=["firm", "actor", "-timestamp"]),
            models.Index(fields=["category", "severity", "-timestamp"]),
            models.Index(fields=["firm", "action", "-timestamp"]),
        ]
        permissions = [
            ("review_audit_events", "Can review audit events"),
            ("export_audit_events", "Can export audit events"),
        ]

    def __str__(self):
        return f"[{self.category}] {self.action} by {self.actor_email or 'System'} at {self.timestamp}"

    def save(self, *args, **kwargs):
        """
        Custom save to enforce immutability.

        Once created, audit events cannot be modified.
        This ensures audit log integrity.
        """
        if self.pk is not None:
            raise ValidationError(
                "Audit events are immutable and cannot be modified after creation. " "Create a new audit event instead."
            )

        # Auto-populate actor_email from actor if not set
        if self.actor and not self.actor_email:
            self.actor_email = self.actor.email

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Prevent deletion of audit events.

        Audit events must be retained per compliance requirements.
        """
        raise ValidationError(
            "Audit events cannot be deleted. " "If legal deletion is required, mark as purged via metadata."
        )


class AuditEventManager:
    """
    Helper for creating audit events with consistent structure.

    Usage:
        from modules.firm.audit import audit

        audit.log_auth_event(
            firm=request.firm,
            actor=request.user,
            action='login_success',
            ip_address=get_client_ip(request),
            metadata={'method': '2FA'}
        )
    """

    @staticmethod
    def log_event(
        firm,
        category,
        action,
        actor=None,
        target_model=None,
        target_id=None,
        target_repr=None,
        reason="",
        outcome="",
        severity=AuditEvent.SEVERITY_INFO,
        metadata=None,
        ip_address=None,
        user_agent=None,
        request_id=None,
        actor_role="",
    ):
        """
        Create an audit event with standard fields.

        Args:
            firm: Firm instance (required for tenant scoping)
            category: Event category (use AuditEvent.CATEGORY_* constants)
            action: Specific action taken
            actor: User who performed action (None for system events)
            target_model: Model name of target object
            target_id: ID of target object
            target_repr: Human-readable target representation
            reason: Reason for action (required for sensitive operations)
            outcome: Result of action
            severity: Event severity
            metadata: Additional context (dict, no customer content)
            ip_address: Request IP address
            user_agent: Request user agent
            request_id: Request correlation ID
            actor_role: Actor's role at time of action

        Returns:
            AuditEvent instance
        """
        if metadata is None:
            metadata = {}

        return AuditEvent.objects.create(
            firm=firm,
            category=category,
            action=action,
            actor=actor,
            target_model=target_model,
            target_id=str(target_id) if target_id else "",
            target_repr=target_repr or "",
            reason=reason,
            outcome=outcome,
            severity=severity,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            actor_role=actor_role,
        )

    @staticmethod
    def log_auth_event(firm, action, actor=None, outcome="success", **kwargs):
        """Log authentication/authorization event."""
        return AuditEventManager.log_event(
            firm=firm, category=AuditEvent.CATEGORY_AUTH, action=action, actor=actor, outcome=outcome, **kwargs
        )

    @staticmethod
    def log_break_glass_event(firm, action, actor, reason, **kwargs):
        """
        Log break-glass access event (CRITICAL).

        Break-glass events are always CRITICAL severity and require a reason.
        """
        if not reason:
            raise ValueError("Break-glass events require a reason")

        event = AuditEventManager.log_event(
            firm=firm,
            category=AuditEvent.CATEGORY_BREAK_GLASS,
            action=action,
            actor=actor,
            reason=reason,
            severity=AuditEvent.SEVERITY_CRITICAL,
            **kwargs,
        )
        capture_message_with_context(
            "break_glass_event",
            level="error",
            context={
                "action": action,
                "actor_id": getattr(actor, "id", None),
                "target_model": kwargs.get("target_model"),
                "target_id": kwargs.get("target_id"),
                "outcome": kwargs.get("outcome"),
            },
            module="firm",
            category=AuditEvent.CATEGORY_BREAK_GLASS,
            firm_id=getattr(firm, "id", None),
            firm_name=getattr(firm, "name", None),
        )
        return event

    @staticmethod
    def log_purge_event(firm, action, actor, target_model, target_id, reason, **kwargs):
        """
        Log content purge event (CRITICAL).

        Purge events are always CRITICAL and require reason, target info.
        """
        if not reason:
            raise ValueError("Purge events require a reason")
        if not target_model or not target_id:
            raise ValueError("Purge events require target_model and target_id")

        return AuditEventManager.log_event(
            firm=firm,
            category=AuditEvent.CATEGORY_PURGE,
            action=action,
            actor=actor,
            target_model=target_model,
            target_id=target_id,
            reason=reason,
            severity=AuditEvent.SEVERITY_CRITICAL,
            **kwargs,
        )

    @staticmethod
    def log_permission_change(firm, action, actor, target_model, target_id, **kwargs):
        """Log permission/role change event."""
        return AuditEventManager.log_event(
            firm=firm,
            category=AuditEvent.CATEGORY_PERMISSIONS,
            action=action,
            actor=actor,
            target_model=target_model,
            target_id=target_id,
            severity=AuditEvent.SEVERITY_WARNING,
            **kwargs,
        )

    @staticmethod
    def log_billing_event(firm, action, actor=None, **kwargs):
        """Log billing metadata event."""
        return AuditEventManager.log_event(
            firm=firm, category=AuditEvent.CATEGORY_BILLING_METADATA, action=action, actor=actor, **kwargs
        )

    @staticmethod
    def log_config_change(firm, action, actor, **kwargs):
        """Log configuration change event."""
        return AuditEventManager.log_event(
            firm=firm,
            category=AuditEvent.CATEGORY_CONFIG,
            action=action,
            actor=actor,
            severity=AuditEvent.SEVERITY_WARNING,
            **kwargs,
        )


# Global audit helper instance
audit = AuditEventManager()
