from __future__ import annotations

import hashlib
import hmac
import ipaddress
import secrets
from typing import Any
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.clients.models import Contact
from modules.firm.models import Firm
from modules.firm.utils import FirmScopedManager


def _hash_tracking_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def generate_tracking_secret() -> str:
    return f"trk_{secrets.token_urlsafe(28)}"


class TrackingSession(models.Model):
    """
    Visitor session for site tracking.

    Tracks consent state and identifiers needed to associate multiple events.
    """

    CONSENT_CHOICES = [
        ("pending", "Pending"),
        ("granted", "Granted"),
        ("denied", "Denied"),
    ]

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="tracking_sessions")
    visitor_id = models.UUIDField(default=uuid4, help_text="Stable visitor identifier")
    session_id = models.UUIDField(default=uuid4, help_text="Session identifier (rotates after inactivity window)")
    consent_state = models.CharField(max_length=20, choices=CONSENT_CHOICES, default="pending")
    user_agent_hash = models.CharField(max_length=64, blank=True, help_text="Hashed user agent for analytics grouping")
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "tracking_session"
        indexes = [
            models.Index(fields=["firm", "visitor_id"], name="tracking_session_visitor_idx"),
            models.Index(fields=["firm", "session_id"], name="tracking_session_session_idx"),
        ]
        unique_together = ("firm", "session_id")

    def __str__(self) -> str:
        return f"{self.firm.slug}:{self.session_id}"

    @staticmethod
    def hash_user_agent(user_agent: str | None) -> str:
        if not user_agent:
            return ""
        return hashlib.sha256(user_agent.encode("utf-8")).hexdigest()


class TrackingEvent(models.Model):
    """
    Individual tracking event (page view, custom event, identity).
    """

    EVENT_TYPES = [
        ("page_view", "Page View"),
        ("custom_event", "Custom Event"),
        ("identity", "Identity"),
    ]

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="tracking_events")
    session = models.ForeignKey(TrackingSession, on_delete=models.CASCADE, related_name="events")
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name="tracking_events")
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    name = models.CharField(max_length=255)
    url = models.TextField(blank=True)
    referrer = models.TextField(blank=True)
    properties = models.JSONField(default=dict, blank=True)
    consent_state = models.CharField(max_length=20, default="pending")
    ip_truncated = models.CharField(max_length=64, blank=True, help_text="Anonymized IP (CIDR truncated)")
    occurred_at = models.DateTimeField(default=timezone.now)
    received_at = models.DateTimeField(auto_now_add=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)
    tracking_key = models.ForeignKey(
        "TrackingKey", on_delete=models.SET_NULL, null=True, blank=True, related_name="events"
    )
    used_fallback_key = models.BooleanField(
        default=False, help_text="True when the legacy/static key was used for ingestion"
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "tracking_event"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["firm", "event_type"], name="tracking_event_type_idx"),
            models.Index(fields=["firm", "occurred_at"], name="tracking_event_occurred_idx"),
            models.Index(fields=["firm", "url"], name="tracking_event_url_idx"),
            models.Index(fields=["firm", "tracking_key"], name="tracking_event_key_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.firm.slug}:{self.event_type}:{self.name}"

    @staticmethod
    def truncate_ip(ip_address_str: str | None) -> str:
        if not ip_address_str:
            return ""
        try:
            ip_obj = ipaddress.ip_address(ip_address_str)
        except ValueError:
            return ""
        if ip_obj.version == 4:
            network = ipaddress.IPv4Network(f"{ip_obj}/24", strict=False)
        else:
            network = ipaddress.IPv6Network(f"{ip_obj}/48", strict=False)
        return str(network.network_address)

    @classmethod
    def record_event(
        cls,
        *,
        firm: Firm,
        session: TrackingSession,
        payload: dict[str, Any],
        contact: Contact | None,
        request_meta: dict[str, Any],
        tracking_key: "TrackingKey | None" = None,
        used_fallback_key: bool = False,
    ) -> "TrackingEvent":
        """Persist a tracking event with normalized fields."""
        ip_address = payload.get("ip_address") or request_meta.get("REMOTE_ADDR")
        user_agent = payload.get("user_agent") or request_meta.get("HTTP_USER_AGENT")
        truncated_ip = cls.truncate_ip(ip_address)
        user_agent_hash = TrackingSession.hash_user_agent(user_agent)

        occurred_at = payload.get("occurred_at")
        if isinstance(occurred_at, str):
            try:
                occurred_at = timezone.datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
            except ValueError:
                occurred_at = timezone.now()
        if not occurred_at:
            occurred_at = timezone.now()

        properties = payload.get("properties") or {}
        # Enforce a max payload size (16 KB) to protect DB
        max_bytes = getattr(settings, "TRACKING_MAX_PROPERTIES_BYTES", 16384)
        if len(str(properties).encode("utf-8")) > max_bytes:
            properties = {"truncated": True}

        event = cls.objects.create(
            firm=firm,
            session=session,
            contact=contact,
            event_type=payload["event_type"],
            name=payload["name"][:255],
            url=(payload.get("url") or "")[:2048],
            referrer=(payload.get("referrer") or "")[:2048],
            properties=properties,
            consent_state=payload.get("consent_state", "pending"),
            ip_truncated=truncated_ip,
            occurred_at=occurred_at,
            user_agent_hash=user_agent_hash,
            tracking_key=tracking_key,
            used_fallback_key=used_fallback_key,
        )
        return event


class TrackingKey(models.Model):
    """
    Firm-scoped tracking key for SDK authentication.

    Keys are rotated via API actions; only the hash is persisted.
    """

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="tracking_keys")
    public_id = models.UUIDField(default=uuid4, unique=True, help_text="Public identifier for instrumentation")
    label = models.CharField(max_length=255, blank=True, help_text="Human-friendly label for the key")
    secret_hash = models.CharField(max_length=128, help_text="Hashed secret token for verification")
    is_active = models.BooleanField(default=True)
    rotated_from = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="rotated_children"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_tracking_keys"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    client_config_version = models.PositiveIntegerField(default=1)

    objects = models.Manager()

    class Meta:
        db_table = "tracking_key"
        indexes = [
            models.Index(fields=["firm", "is_active"], name="tracking_key_active_idx"),
            models.Index(fields=["firm", "public_id"], name="tracking_key_public_idx"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.firm.slug}:{self.public_id}"

    @classmethod
    def issue(cls, *, firm: Firm, created_by=None, label: str = "") -> tuple["TrackingKey", str]:
        secret = generate_tracking_secret()
        key = cls.objects.create(
            firm=firm,
            label=label,
            secret_hash=_hash_tracking_secret(secret),
            created_by=created_by,
        )
        TrackingKeyAudit.record(key=key, firm=firm, action="created", actor=created_by, detail="Key issued")
        return key, secret

    def rotate(self, *, rotated_by=None) -> str:
        secret = generate_tracking_secret()
        self.secret_hash = _hash_tracking_secret(secret)
        self.rotated_at = timezone.now()
        self.client_config_version += 1
        self.save(update_fields=["secret_hash", "rotated_at", "client_config_version"])
        TrackingKeyAudit.record(
            key=self,
            firm=self.firm,
            action="rotated",
            actor=rotated_by,
            detail="Secret rotated and client config bumped",
        )
        return secret

    def revoke(self, *, revoked_by=None) -> None:
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_active", "revoked_at"])
        TrackingKeyAudit.record(
            key=self, firm=self.firm, action="revoked", actor=revoked_by, detail="Key revoked"
        )

    def matches(self, secret: str) -> bool:
        return hmac.compare_digest(self.secret_hash, _hash_tracking_secret(secret))

    def touch(self) -> None:
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])


class TrackingKeyAudit(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("rotated", "Rotated"),
        ("downloaded", "Downloaded"),
        ("revoked", "Revoked"),
        ("abuse_blocked", "Abuse Blocked"),
    ]

    tracking_key = models.ForeignKey(TrackingKey, on_delete=models.CASCADE, related_name="audits")
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="tracking_key_audits")
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tracking_key_audits",
    )
    detail = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tracking_key_audit"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["firm", "action"], name="tracking_key_audit_action_idx")]

    @classmethod
    def record(cls, *, key: TrackingKey, firm: Firm, action: str, actor=None, detail: str = "") -> "TrackingKeyAudit":
        return cls.objects.create(tracking_key=key, firm=firm, action=action, actor=actor, detail=detail)


class TrackingAbuseEvent(models.Model):
    """Captures ingestion rate limit and invalid-key activity for monitoring."""

    REASONS = [
        ("rate_limited", "Rate limited"),
        ("invalid_key", "Invalid key"),
    ]

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="tracking_abuse_events")
    tracking_key = models.ForeignKey(
        TrackingKey, on_delete=models.SET_NULL, null=True, blank=True, related_name="abuse_events"
    )
    source_ip = models.CharField(max_length=64, blank=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)
    reason = models.CharField(max_length=32, choices=REASONS)
    request_count = models.PositiveIntegerField(default=0)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tracking_abuse_event"
        ordering = ["-occurred_at"]
        indexes = [models.Index(fields=["firm", "reason"], name="tracking_abuse_reason_idx")]

    def __str__(self) -> str:
        return f"{self.firm.slug}:{self.reason}:{self.source_ip}"


class SiteMessage(models.Model):
    """Configurable site message definition for personalization surfaces."""

    MESSAGE_TYPES = [
        ("modal", "Modal"),
        ("slide_in", "Slide In"),
        ("banner", "Banner"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="site_messages")
    name = models.CharField(max_length=255)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    targeting_rules = models.JSONField(default=dict, blank=True, help_text="Segment and behavior targeting rules")
    content = models.JSONField(default=dict, blank=True, help_text="Structured content for rendering variants")
    personalization_tokens = models.JSONField(default=list, blank=True)
    form_schema = models.JSONField(default=dict, blank=True, help_text="Optional embedded form definition")
    frequency_cap = models.PositiveIntegerField(default=1, help_text="Max displays per visitor per day")
    active_from = models.DateTimeField(null=True, blank=True)
    active_until = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="site_messages"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tracking_site_message"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="site_message_status_idx"),
            models.Index(fields=["firm", "message_type"], name="site_message_type_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.firm.slug}:{self.name}"


class SiteMessageImpression(models.Model):
    """Tracks site message deliveries, impressions, and clicks for frequency control."""

    KIND_CHOICES = [
        ("delivered", "Delivered"),
        ("view", "Viewed"),
        ("click", "Clicked"),
    ]

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="site_message_impressions")
    site_message = models.ForeignKey(SiteMessage, on_delete=models.CASCADE, related_name="impressions")
    session = models.ForeignKey(TrackingSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    visitor_id = models.UUIDField()
    delivery_id = models.UUIDField(default=uuid4, editable=False, help_text="Stable id per delivery to group events")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    variant = models.CharField(max_length=100, blank=True)
    url = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "tracking_site_message_impression"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["firm", "visitor_id", "site_message"], name="site_message_impr_freq_idx"),
            models.Index(fields=["firm", "delivery_id"], name="site_message_impr_delivery_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.firm.slug}:{self.site_message_id}:{self.kind}"
