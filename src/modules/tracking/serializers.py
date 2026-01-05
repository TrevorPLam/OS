from __future__ import annotations

from typing import Any

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from modules.clients.models import Contact
from modules.firm.models import Firm
from modules.tracking.models import TrackingEvent, TrackingSession


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
        ]


class TrackingEventIngestSerializer(serializers.Serializer):
    tracking_key = serializers.CharField(max_length=255)
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
