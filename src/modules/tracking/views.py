from __future__ import annotations

import csv
import io
import json
import logging
from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from modules.automation.triggers import TriggerDetector
from modules.firm.models import FirmMembership
from modules.tracking.models import (
    SiteMessage,
    TrackingAbuseEvent,
    TrackingEvent,
    TrackingKey,
    TrackingKeyAudit,
    TrackingSession,
)
from modules.tracking.serializers import (
    SiteMessageSerializer,
    TrackingEventIngestSerializer,
    TrackingEventSerializer,
    TrackingKeyRequestSerializer,
    TrackingKeySerializer,
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

        # Support single event payloads for convenience
        raw_events = request.data.get("events") if isinstance(request.data, dict) else None
        payloads = raw_events if raw_events is not None else [request.data]

        serializers_to_save: list[TrackingEventIngestSerializer] = []
        for payload in payloads:
            serializer = TrackingEventIngestSerializer(
                data=payload, context={"request_meta": request.META}
            )
            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as exc:
                if "Invalid or inactive tracking key" in str(exc.detail):
                    firm_slug = payload.get("firm_slug")
                    self._record_abuse(
                        firm_slug=firm_slug,
                        reason="invalid_key",
                        request_meta=request.META,
                        tracking_key=None,
                    )
                raise
            serializers_to_save.append(serializer)

        if not serializers_to_save:
            return Response({"detail": "No events supplied"}, status=status.HTTP_400_BAD_REQUEST)

        firm_slug = serializers_to_save[0].validated_data["firm_slug"]
        if any(s.validated_data["firm_slug"] != firm_slug for s in serializers_to_save):
            return Response({"detail": "All events must target the same firm"}, status=status.HTTP_400_BAD_REQUEST)

        events = []
        firm = serializers_to_save[0]._firm  # set during validation
        if self._is_rate_limited(firm=firm, serializers_to_save=serializers_to_save, request_meta=request.META):
            return Response({"detail": "Tracking ingestion rate limit exceeded"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        for serializer in serializers_to_save:
            event = serializer.save()
            events.append(event)
            self._emit_automation_event(event)

        return Response({"created": len(events)}, status=status.HTTP_201_CREATED)

    def _is_rate_limited(
        self,
        *,
        firm,
        serializers_to_save: Iterable[TrackingEventIngestSerializer],
        request_meta,
    ) -> bool:
        limit = getattr(settings, "TRACKING_INGEST_RATE_LIMIT_PER_MINUTE", 300)
        ip_address = request_meta.get("REMOTE_ADDR", "")
        bucket_suffix = timezone.now().strftime("%Y%m%d%H%M")
        event_count = len(serializers_to_save)
        firm_bucket_key = f"tracking:firm:{firm.id}:{bucket_suffix}"
        if self._increment_and_check(bucket_key=firm_bucket_key, increment=event_count, limit=limit):
            self._record_abuse(
                firm_slug=firm.slug,
                reason="rate_limited",
                request_meta=request_meta,
                tracking_key=None,
                request_count=event_count,
            )
            return True

        for serializer in serializers_to_save:
            tk = getattr(serializer, "_tracking_key", None)
            if not tk:
                continue
            key_bucket_key = f"tracking:key:{tk.public_id}:{bucket_suffix}"
            if self._increment_and_check(bucket_key=key_bucket_key, increment=1, limit=limit):
                self._record_abuse(
                    firm_slug=firm.slug,
                    reason="rate_limited",
                    request_meta=request_meta,
                    tracking_key=tk,
                    request_count=1,
                )
                return True

        if ip_address:
            ip_bucket_key = f"tracking:ip:{ip_address}:{bucket_suffix}"
            if self._increment_and_check(bucket_key=ip_bucket_key, increment=event_count, limit=limit):
                self._record_abuse(
                    firm_slug=firm.slug,
                    reason="rate_limited",
                    request_meta=request_meta,
                    tracking_key=None,
                    request_count=event_count,
                )
                return True

        return False

    @staticmethod
    def _increment_and_check(*, bucket_key: str, increment: int, limit: int) -> bool:
        current = cache.get(bucket_key, 0)
        new_value = current + increment
        cache.set(bucket_key, new_value, timeout=60)
        return new_value > limit

    def _record_abuse(self, *, firm_slug: str | None, reason: str, request_meta, tracking_key=None, request_count=0):
        if not firm_slug:
            return
        from modules.firm.models import Firm

        firm = Firm.objects.filter(slug=firm_slug).first()
        if not firm:
            return
        user_agent_hash = TrackingSession.hash_user_agent(request_meta.get("HTTP_USER_AGENT"))
        event = TrackingAbuseEvent.objects.create(
            firm=firm,
            tracking_key=tracking_key,
            source_ip=request_meta.get("REMOTE_ADDR", ""),
            user_agent_hash=user_agent_hash,
            reason=reason,
            request_count=request_count,
        )
        if tracking_key:
            TrackingKeyAudit.record(
                key=tracking_key,
                firm=firm,
                action="abuse_blocked",
                actor=None,
                detail=f"{reason} (source_ip={event.source_ip})",
            )

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

        url_filter = request.query_params.get("url")
        event_name_filter = request.query_params.get("event_name")
        days = int(request.query_params.get("days", "30"))
        days = min(max(days, 1), 90)

        since = timezone.now() - timedelta(days=days)
        events = TrackingEvent.objects.filter(firm=firm, occurred_at__gte=since)
        if url_filter:
            events = events.filter(url__icontains=url_filter)
        if event_name_filter:
            events = events.filter(name__icontains=event_name_filter)

        page_views = events.filter(event_type="page_view")
        custom_events = events.filter(event_type="custom_event")

        time_series = (
            events.annotate(day=TruncDay("occurred_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        recent_referrers = list(
            events.exclude(referrer="")
            .values("referrer")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        campaign_breakdown = list(
            events.filter(properties__utm_source__isnull=False)
            .values("properties__utm_source", "properties__utm_campaign")
            .annotate(count=Count("id"))
            .order_by("-count")[:15]
        )
        fallback_key_used = events.filter(used_fallback_key=True).exists()
        default_key_warning = fallback_key_used or not firm.tracking_keys.filter(is_active=True).exists()

        summary = {
            "window_days": days,
            "page_views": page_views.count(),
            "unique_visitors": page_views.values("session__visitor_id").distinct().count(),
            "custom_events": custom_events.count(),
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
            "time_series": list(time_series),
            "referrers": recent_referrers,
            "campaigns": campaign_breakdown,
            "filters": {"url": url_filter, "event_name": event_name_filter, "days": days},
            "default_key_warning": default_key_warning,
            "export_path": "/api/v1/tracking/analytics/export/",
        }
        return Response(summary)

    @staticmethod
    def _is_member(user, firm) -> bool:
        return (
            getattr(user, "is_authenticated", False)
            and FirmMembership.objects.filter(user=user, firm=firm, is_active=True).exists()
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
            and FirmMembership.objects.filter(user=user, firm=firm, is_active=True).exists()
        )


class TrackingKeyViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        firm = self._get_firm(request)
        if not firm:
            return Response({"detail": "Firm context required"}, status=status.HTTP_403_FORBIDDEN)
        keys = TrackingKey.objects.filter(firm=firm, is_active=True)
        serializer = TrackingKeySerializer(keys, many=True)
        fallback_key_warning = bool(settings.TRACKING_PUBLIC_KEY and not keys.exists())
        return Response({"keys": serializer.data, "fallback_in_use": fallback_key_warning})

    def create(self, request):
        firm = self._get_firm(request)
        if not firm:
            return Response({"detail": "Firm context required"}, status=status.HTTP_403_FORBIDDEN)
        if not self._can_manage_settings(request.user, firm):
            return Response({"detail": "Insufficient permissions"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TrackingKeyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key, secret = TrackingKey.issue(
            firm=firm, created_by=request.user, label=serializer.validated_data.get("label", "")
        )
        bundle = self._client_bundle(firm=firm, key=key, secret=secret)
        TrackingKeyAudit.record(key=key, firm=firm, action="downloaded", actor=request.user, detail="Key issued")
        return Response({"key": TrackingKeySerializer(key).data, "client_config": bundle}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def rotate(self, request, pk=None):
        key = self._get_key(request, pk)
        if not key:
            return Response({"detail": "Key not found"}, status=status.HTTP_404_NOT_FOUND)
        secret = key.rotate(rotated_by=request.user)
        bundle = self._client_bundle(firm=key.firm, key=key, secret=secret)
        return Response({"key": TrackingKeySerializer(key).data, "client_config": bundle})

    @action(detail=True, methods=["get"])
    def config(self, request, pk=None):
        key = self._get_key(request, pk)
        if not key:
            return Response({"detail": "Key not found"}, status=status.HTTP_404_NOT_FOUND)
        secret = key.rotate(rotated_by=request.user)
        TrackingKeyAudit.record(key=key, firm=key.firm, action="downloaded", actor=request.user, detail="Config pull")
        bundle = self._client_bundle(firm=key.firm, key=key, secret=secret)
        return Response({"client_config": bundle})

    def _get_key(self, request, pk):
        firm = self._get_firm(request)
        if not firm:
            return None
        if not self._can_manage_settings(request.user, firm):
            return None
        try:
            return TrackingKey.objects.get(firm=firm, pk=pk, is_active=True)
        except TrackingKey.DoesNotExist:
            return None

    @staticmethod
    def _client_bundle(*, firm, key: TrackingKey, secret: str) -> dict:
        return {
            "firm_slug": firm.slug,
            "tracking_key": secret,
            "tracking_key_id": str(key.public_id),
            "ingest_endpoint": "/api/v1/tracking/collect/",
            "version": key.client_config_version,
        }

    @staticmethod
    def _get_firm(request):
        return getattr(request, "firm", None)

    @staticmethod
    def _can_manage_settings(user, firm) -> bool:
        return FirmMembership.objects.filter(
            user=user, firm=firm, is_active=True, can_manage_settings=True
        ).exists()


class TrackingAnalyticsExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        firm = getattr(request, "firm", None)
        if not firm or not FirmMembership.objects.filter(
            user=request.user, firm=firm, is_active=True, can_view_reports=True
        ).exists():
            return Response({"detail": "Firm analytics access required"}, status=status.HTTP_403_FORBIDDEN)

        days = int(request.query_params.get("days", "30"))
        days = min(max(days, 1), 90)
        url_filter = request.query_params.get("url")
        event_name_filter = request.query_params.get("event_name")

        events = TrackingEvent.objects.filter(firm=firm, occurred_at__gte=timezone.now() - timedelta(days=days))
        if url_filter:
            events = events.filter(url__icontains=url_filter)
        if event_name_filter:
            events = events.filter(name__icontains=event_name_filter)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["occurred_at", "event_type", "name", "url", "referrer", "session_id", "visitor_id", "properties"]
        )
        for event in events.order_by("-occurred_at"):
            writer.writerow(
                [
                    event.occurred_at.isoformat(),
                    event.event_type,
                    event.name,
                    event.url,
                    event.referrer,
                    event.session.session_id,
                    event.session.visitor_id,
                    json.dumps(event.properties),
                ]
            )

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=tracking-events.csv"
        return response


class SiteMessageViewSet(viewsets.ModelViewSet):
    serializer_class = SiteMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        firm = getattr(self.request, "firm", None)
        if not firm or not FirmMembership.objects.filter(
            user=self.request.user, firm=firm, is_active=True, can_manage_settings=True
        ).exists():
            return SiteMessage.objects.none()
        return SiteMessage.objects.filter(firm=firm)

    def create(self, request, *args, **kwargs):
        firm = getattr(request, "firm", None)
        if not firm:
            return Response({"detail": "Firm context required"}, status=status.HTTP_403_FORBIDDEN)
        if not FirmMembership.objects.filter(
            user=request.user, firm=firm, is_active=True, can_manage_settings=True
        ).exists():
            return Response({"detail": "Insufficient permissions"}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        firm = getattr(request, "firm", None)
        if not firm:
            return Response({"detail": "Firm context required"}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        firm = getattr(request, "firm", None)
        if not firm:
            return Response({"detail": "Firm context required"}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def perform_create(self, serializer):
        firm = getattr(self.request, "firm", None)
        serializer.save(firm=firm, created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()
