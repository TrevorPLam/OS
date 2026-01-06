from __future__ import annotations

import hmac
from typing import Any

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from modules.clients.models import Contact
from modules.firm.models import Firm
from modules.tracking.models import SiteMessage, SiteMessageImpression, TrackingEvent, TrackingKey, TrackingSession


def validate_tracking_key(
    *, firm: Firm, secret: str, public_id=None
) -> tuple[TrackingKey | None, bool]:
    key_qs = TrackingKey.objects.filter(firm=firm, is_active=True)
    if public_id:
        key_qs = key_qs.filter(public_id=public_id)
    for key in key_qs:
        if key.matches(secret):
            key.touch()
            return key, False

    fallback = getattr(settings, "TRACKING_PUBLIC_KEY", None)
    active_keys_exist = TrackingKey.objects.filter(firm=firm, is_active=True).exists()
    if fallback and hmac.compare_digest(fallback, secret) and not active_keys_exist:
        return None, True
    raise serializers.ValidationError("Invalid or inactive tracking key")


class TrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingEvent
        fields = [
            "id",
            "event_type",
            "name",
            "url",
            "referrer",
            "properties",
            "consent_state",
            "occurred_at",
            "received_at",
            "tracking_key",
        ]


class TrackingEventIngestSerializer(serializers.Serializer):
    tracking_key = serializers.CharField(max_length=255)
    tracking_key_id = serializers.UUIDField(required=False)
    firm_slug = serializers.SlugField(max_length=255)
    event_type = serializers.ChoiceField(choices=[c[0] for c in TrackingEvent.EVENT_TYPES])
    name = serializers.CharField(max_length=255)
    url = serializers.CharField(required=False, allow_blank=True, max_length=2048)
    referrer = serializers.CharField(required=False, allow_blank=True, max_length=2048)
    properties = serializers.DictField(default=dict)
    consent_state = serializers.ChoiceField(
        choices=[c[0] for c in TrackingSession.CONSENT_CHOICES],
        required=False,
    )
    occurred_at = serializers.DateTimeField(required=False)
    visitor_id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    contact_id = serializers.IntegerField(required=False)
    user_agent = serializers.CharField(required=False, allow_blank=True)

    def validate_firm_slug(self, value: str) -> str:
        try:
            firm = Firm.objects.get(slug=value, status__in=["active", "trial"])
            self._firm = firm
            return value
        except Firm.DoesNotExist as exc:  # noqa: B904
            raise serializers.ValidationError("Invalid or inactive firm slug") from exc

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        max_bytes = getattr(settings, "TRACKING_MAX_PROPERTIES_BYTES", 16384)
        if len(str(attrs.get("properties", {})).encode("utf-8")) > max_bytes:
            raise serializers.ValidationError("Event properties exceed 16KB limit.")

        firm = getattr(self, "_firm", None) or Firm.objects.get(slug=attrs["firm_slug"])
        self._tracking_key, self._used_fallback_key = validate_tracking_key(
            firm=firm, secret=attrs["tracking_key"], public_id=attrs.get("tracking_key_id")
        )
        return attrs

    def save(self, **kwargs: Any) -> TrackingEvent:
        firm = getattr(self, "_firm", None) or Firm.objects.get(slug=self.validated_data["firm_slug"])
        session, _created = TrackingSession.objects.get_or_create(
            firm=firm,
            session_id=self.validated_data["session_id"],
            defaults={
                "visitor_id": self.validated_data["visitor_id"],
                "consent_state": self.validated_data.get("consent_state", "pending"),
                "user_agent_hash": TrackingSession.hash_user_agent(self.validated_data.get("user_agent")),
            },
        )
        session.consent_state = self.validated_data.get("consent_state", session.consent_state)
        session.last_seen_at = timezone.now()
        session.save(update_fields=["consent_state", "last_seen_at"])

        contact = None
        if contact_id := self.validated_data.get("contact_id"):
            contact = Contact.objects.filter(firm=firm, id=contact_id).first()

        event = TrackingEvent.record_event(
            firm=firm,
            session=session,
            payload=self.validated_data,
            contact=contact,
            request_meta=self.context.get("request_meta", {}),
            tracking_key=getattr(self, "_tracking_key", None),
            used_fallback_key=getattr(self, "_used_fallback_key", False),
        )
        return event


class TrackingEventBatchSerializer(serializers.Serializer):
    events = serializers.ListField(child=TrackingEventIngestSerializer())

    def create(self, validated_data: dict[str, Any]) -> list[TrackingEvent]:
        events = []
        for event_data in validated_data["events"]:
            serializer = TrackingEventIngestSerializer(
                data=event_data, context={"request_meta": self.context.get("request_meta", {})}
            )
            serializer.is_valid(raise_exception=True)
            events.append(serializer.save())
        return events


class TrackingKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingKey
        fields = [
            "id",
            "public_id",
            "label",
            "is_active",
            "client_config_version",
            "created_at",
            "rotated_at",
            "last_used_at",
        ]


class TrackingKeyRequestSerializer(serializers.Serializer):
    label = serializers.CharField(required=False, allow_blank=True, max_length=255)


class SiteMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteMessage
        fields = [
            "id",
            "name",
            "message_type",
            "status",
            "targeting_rules",
            "content",
            "personalization_tokens",
            "form_schema",
            "frequency_cap",
            "active_from",
            "active_until",
            "created_at",
            "updated_at",
        ]


class SiteMessageTargetRequestSerializer(serializers.Serializer):
    firm_slug = serializers.SlugField(max_length=255)
    visitor_id = serializers.UUIDField()
    session_id = serializers.UUIDField(required=False)
    contact_id = serializers.IntegerField(required=False)
    url = serializers.CharField(max_length=2048)
    consent_state = serializers.ChoiceField(
        choices=[c[0] for c in TrackingSession.CONSENT_CHOICES], required=False, default="pending"
    )
    segments = serializers.ListField(child=serializers.CharField(max_length=100), required=False)
    behaviors = serializers.DictField(default=dict)
    message_types = serializers.ListField(
        child=serializers.ChoiceField(choices=[c[0] for c in SiteMessage.MESSAGE_TYPES]),
        required=False,
    )
    limit = serializers.IntegerField(default=3, min_value=1, max_value=10)
    page_view_count = serializers.IntegerField(required=False, min_value=0, default=0)
    session_count = serializers.IntegerField(required=False, min_value=1, default=1)
    recent_events = serializers.ListField(child=serializers.CharField(max_length=255), required=False)

    def validate_firm_slug(self, value: str) -> str:
        try:
            self._firm = Firm.objects.get(slug=value, status__in=["active", "trial"])
            return value
        except Firm.DoesNotExist as exc:  # noqa: B904
            raise serializers.ValidationError("Invalid or inactive firm slug") from exc

    def validate_contact_id(self, value: int) -> int:
        firm = getattr(self, "_firm", None)
        if not firm or value is None:
            return value
        if not Contact.objects.filter(firm=firm, id=value).exists():
            raise serializers.ValidationError("Contact does not exist for this firm")
        return value

    @property
    def firm(self) -> Firm:
        return getattr(self, "_firm", None)


class SiteMessageManifestRequestSerializer(serializers.Serializer):
    firm_slug = serializers.SlugField(max_length=255)
    tracking_secret = serializers.CharField(max_length=255, source="tracking_key")
    tracking_key_id = serializers.UUIDField(required=False)

    def validate_firm_slug(self, value: str) -> str:
        try:
            self._firm = Firm.objects.get(slug=value, status__in=["active", "trial"])
            return value
        except Firm.DoesNotExist as exc:  # noqa: B904
            raise serializers.ValidationError("Invalid or inactive firm slug") from exc

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        firm = getattr(self, "_firm", None) or Firm.objects.get(slug=attrs["firm_slug"])
        self._tracking_key, self._used_fallback_key = validate_tracking_key(
            firm=firm, secret=attrs["tracking_secret"], public_id=attrs.get("tracking_key_id")
        )
        return attrs

    @property
    def firm(self) -> Firm:
        return getattr(self, "_firm", None)

    @property
    def tracking_key(self) -> TrackingKey | None:
        return getattr(self, "_tracking_key", None)


class SiteMessageImpressionLogSerializer(serializers.Serializer):
    delivery_id = serializers.UUIDField()
    event = serializers.ChoiceField(choices=[c[0] for c in SiteMessageImpression.KIND_CHOICES if c[0] != "delivered"])
    url = serializers.CharField(required=False, allow_blank=True, max_length=2048)
    variant = serializers.CharField(required=False, allow_blank=True, max_length=100)
