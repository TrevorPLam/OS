from __future__ import annotations

import hashlib
import ipaddress
from typing import Any
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.clients.models import Contact
from modules.firm.models import Firm
from modules.firm.utils import FirmScopedManager


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

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "tracking_event"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["firm", "event_type"], name="tracking_event_type_idx"),
            models.Index(fields=["firm", "occurred_at"], name="tracking_event_occurred_idx"),
            models.Index(fields=["firm", "url"], name="tracking_event_url_idx"),
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
        )
        return event
