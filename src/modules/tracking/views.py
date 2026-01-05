from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.automation.triggers import TriggerDetector
from modules.firm.models import FirmMembership
from modules.tracking.models import TrackingEvent, TrackingSession
from modules.tracking.serializers import (
    TrackingEventBatchSerializer,
    TrackingEventIngestSerializer,
    TrackingEventSerializer,
)

logger = logging.getLogger(__name__)


class TrackingIngestView(APIView):
    """
    Public ingestion endpoint for tracking events.

    Authentication is handled via firm-specific tracking key in the payload.
    """

    authentication_classes: list = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs) -> Response:
        if getattr(settings, "TRACKING_INGEST_ENABLED", True) is False:
            return Response({"detail": "Tracking ingestion disabled"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        expected_key = getattr(settings, "TRACKING_PUBLIC_KEY", None)
        if not expected_key:
            return Response(
                {"detail": "Tracking key not configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Support single event payloads for convenience
        if "events" not in request.data and isinstance(request.data, dict):
            serializer = TrackingEventIngestSerializer(
                data=request.data, context={"request_meta": request.META}
            )
            serializer.is_valid(raise_exception=True)
            event_payloads = [serializer.validated_data]
        else:
            batch_serializer = TrackingEventBatchSerializer(
                data=request.data, context={"request_meta": request.META}
            )
            batch_serializer.is_valid(raise_exception=True)
            event_payloads = batch_serializer.validated_data["events"]

        if any(event["tracking_key"] != expected_key for event in event_payloads):
            return Response({"detail": "Invalid tracking key"}, status=status.HTTP_403_FORBIDDEN)

        events = []
        for payload in event_payloads:
            ingest_serializer = TrackingEventIngestSerializer(
                data=payload, context={"request_meta": request.META}
            )
            ingest_serializer.is_valid(raise_exception=True)
            event = ingest_serializer.save()
            events.append(event)
            self._emit_automation_event(event)

        return Response({"created": len(events)}, status=status.HTTP_201_CREATED)

    def _emit_automation_event(self, event: TrackingEvent) -> None:
        trigger_type = "site_page_view" if event.event_type == "page_view" else "site_custom_event"
        event_data = {
            "event_name": event.name,
            "event_type": event.event_type,
            "url": event.url,
            "referrer": event.referrer,
            "properties": event.properties,
            "session_id": str(event.session.session_id),
            "visitor_id": str(event.session.visitor_id),
            "occurred_at": event.occurred_at.isoformat(),
            "discriminator": f"{event.session.session_id}:{event.name}:{event.occurred_at.isoformat()}",
        }

        try:
            TriggerDetector.detect_and_trigger(
                firm=event.firm,
                trigger_type=trigger_type,
                event_data=event_data,
                contact=event.contact,
            )
        except Exception:
            logger.exception("Failed to dispatch tracking event to automation")


class TrackingEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrackingEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        firm = getattr(self.request, "firm", None)
        qs = TrackingEvent.objects.all()
        if firm and self._is_member(self.request.user, firm):
            qs = qs.filter(firm=firm)
        else:
            qs = qs.none()
        return qs

    @staticmethod
    def _is_member(user, firm) -> bool:
        return (
            getattr(user, "is_authenticated", False)
            and FirmMembership.objects.filter(user=user, firm=firm, is_active=True).exists()
        )


class TrackingSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        firm = getattr(request, "firm", None)
        if not firm or not self._is_member(request.user, firm):
            return Response({"detail": "Firm context required"}, status=status.HTTP_403_FORBIDDEN)

        since = timezone.now() - timedelta(days=30)
        events = TrackingEvent.objects.filter(firm=firm, occurred_at__gte=since)
        page_views = events.filter(event_type="page_view")
        custom_events = events.filter(event_type="custom_event")

        summary = {
            "page_views_30d": page_views.count(),
            "unique_visitors_30d": page_views.values("session__visitor_id").distinct().count(),
            "custom_events_30d": custom_events.count(),
            "recent_events": list(
                events.order_by("-occurred_at")[:20].values(
                    "name", "event_type", "url", "referrer", "occurred_at", "properties"
                )
            ),
            "top_pages": list(
                page_views.values("url").annotate(count=Count("id")).order_by("-count")[:10]
            ),
            "top_events": list(
                custom_events.values("name").annotate(count=Count("id")).order_by("-count")[:10]
            ),
        }
        return Response(summary)

    @staticmethod
    def _is_member(user, firm) -> bool:
        return (
            getattr(user, "is_authenticated", False)
            and FirmMembership.objects.filter(user=user, firm=firm, status="active").exists()
        )


class TrackingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrackingSession.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        firm = getattr(self.request, "firm", None)
        qs = super().get_queryset()
        if firm and self._is_member(self.request.user, firm):
            qs = qs.filter(firm=firm)
        else:
            qs = qs.none()
        return qs

    @staticmethod
    def _is_member(user, firm) -> bool:
        return (
            getattr(user, "is_authenticated", False)
            and FirmMembership.objects.filter(user=user, firm=firm, status="active").exists()
        )
