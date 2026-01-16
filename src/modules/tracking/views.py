from __future__ import annotations

import csv
import io
import json
import logging
import hashlib
import math
from datetime import timedelta
from typing import Iterable
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.core.signing import Signer
from django.db import models
from django.db.models import Count, Q
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
    SiteMessageImpression,
    TrackingAbuseEvent,
    TrackingEvent,
    TrackingKey,
    TrackingKeyAudit,
    TrackingSession,
)
from modules.tracking.serializers import (
    SiteMessageImpressionLogSerializer,
    SiteMessageManifestRequestSerializer,
    SiteMessageSerializer,
    SiteMessageTargetRequestSerializer,
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


class TrackingWebVitalsSummaryView(APIView):
    """
    Summarize Core Web Vitals captured via tracking events.

    Meta-commentary:
    - **Functionality:** Aggregates `web_vital` custom events into P75 values per metric.
    - **Mapping:** Uses `TrackingEvent.properties.metric/value` emitted by the frontend tracking client.
    - **Reasoning:** Keeps aggregation server-side so the dashboard can compare against alert thresholds.
    """

    permission_classes = [permissions.IsAuthenticated]

    METRIC_ORDER = ("LCP", "FID", "CLS", "TTFB", "FCP", "TTI", "INP")
    METRIC_UNITS = {
        "LCP": "ms",
        "FID": "ms",
        "CLS": "score",
        "TTFB": "ms",
        "FCP": "ms",
        "TTI": "ms",
        "INP": "ms",
    }
    ALERT_THRESHOLDS = {
        "LCP": 2500,
        "FID": 100,
        "CLS": 0.1,
    }

    def get(self, request, *args, **kwargs) -> Response:
        firm = getattr(request, "firm", None)
        if not firm or not self._is_member(request.user, firm):
            return Response({"detail": "Firm context required"}, status=status.HTTP_403_FORBIDDEN)

        days = int(request.query_params.get("days", "30"))
        days = min(max(days, 1), 90)
        since = timezone.now() - timedelta(days=days)

        events = TrackingEvent.objects.filter(
            firm=firm,
            event_type="custom_event",
            name="web_vital",
            occurred_at__gte=since,
        ).values_list("properties", flat=True)

        metrics: dict[str, list[float]] = {metric: [] for metric in self.METRIC_ORDER}
        for properties in events.iterator():
            if not isinstance(properties, dict):
                continue
            metric_name = properties.get("metric")
            value = properties.get("value")
            if metric_name in metrics and isinstance(value, (int, float)):
                metrics[metric_name].append(float(value))

        response_metrics = []
        for metric in self.METRIC_ORDER:
            values = metrics[metric]
            p75 = self._percentile(values, 75)
            threshold = self.ALERT_THRESHOLDS.get(metric)
            status_label = self._status_for_threshold(p75, threshold)
            response_metrics.append(
                {
                    "metric": metric,
                    "p75": p75,
                    "count": len(values),
                    "unit": self.METRIC_UNITS.get(metric, "ms"),
                    "target": threshold,
                    "status": status_label,
                }
            )

        return Response(
            {
                "window_days": days,
                "generated_at": timezone.now().isoformat(),
                "metrics": response_metrics,
                "targets": self.ALERT_THRESHOLDS,
            }
        )

    @staticmethod
    def _percentile(values: list[float], percentile: int) -> float | None:
        if not values:
            return None
        values_sorted = sorted(values)
        rank = (len(values_sorted) - 1) * (percentile / 100)
        lower = math.floor(rank)
        upper = math.ceil(rank)
        if lower == upper:
            return values_sorted[int(rank)]
        lower_value = values_sorted[lower]
        upper_value = values_sorted[upper]
        return lower_value + (upper_value - lower_value) * (rank - lower)

    @staticmethod
    def _status_for_threshold(value: float | None, threshold: float | None) -> str:
        if value is None:
            return "unknown"
        if threshold is None:
            return "info"
        return "ok" if value <= threshold else "alert"

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


class SiteMessageManifestView(APIView):
    """Public endpoint to fetch a signed manifest of active site messages."""

    authentication_classes: list = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SiteMessageManifestRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        firm = serializer.firm
        if not firm:
            return Response({"detail": "Invalid firm"}, status=status.HTTP_400_BAD_REQUEST)

        messages = self._active_messages(firm)
        manifest = [
            {
                "id": message.id,
                "name": message.name,
                "message_type": message.message_type,
                "updated_at": message.updated_at.isoformat(),
                "active_from": message.active_from.isoformat() if message.active_from else None,
                "active_until": message.active_until.isoformat() if message.active_until else None,
            }
            for message in messages
        ]
        signature = self._sign_manifest(manifest)
        tracking_key = serializer.tracking_key
        config_version = tracking_key.client_config_version if tracking_key else 1

        return Response(
            {
                "manifest": manifest,
                "signature": signature,
                "config_version": config_version,
                "generated_at": timezone.now().isoformat(),
            }
        )

    @staticmethod
    def _active_messages(firm):
        now = timezone.now()
        return SiteMessage.objects.filter(firm=firm, status="published").filter(
            models.Q(active_from__lte=now) | models.Q(active_from__isnull=True),
            models.Q(active_until__gte=now) | models.Q(active_until__isnull=True),
        )

    @staticmethod
    def _sign_manifest(manifest: list[dict]) -> str:
        signer = Signer(salt="tracking-site-message-manifest")
        payload = json.dumps(manifest, sort_keys=True)
        return signer.sign(payload)


class SiteMessageTargetingView(APIView):
    """
    Public endpoint to evaluate eligible site messages for a visitor/session.

    Applies targeting rules, consent checks, and frequency caps before returning messages.
    """

    authentication_classes: list = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SiteMessageTargetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        firm = serializer.firm
        if not firm:
            return Response({"detail": "Invalid firm"}, status=status.HTTP_400_BAD_REQUEST)

        session = self._get_or_create_session(serializer=serializer)
        if session and session.consent_state == "denied":
            return Response({"messages": []})
        messages = self._select_messages(firm=firm, session=session, data=serializer.validated_data)
        return Response({"messages": messages})

    def _get_or_create_session(self, *, serializer: SiteMessageTargetRequestSerializer) -> TrackingSession | None:
        if not serializer.firm:
            return None
        session_id = serializer.validated_data.get("session_id") or uuid4()
        consent_state = serializer.validated_data.get("consent_state", "pending")
        session, _created = TrackingSession.objects.get_or_create(
            firm=serializer.firm,
            session_id=session_id,
            defaults={
                "visitor_id": serializer.validated_data["visitor_id"],
                "consent_state": consent_state,
            },
        )
        if session.consent_state != consent_state:
            session.consent_state = consent_state
            session.save(update_fields=["consent_state"])
        return session

    def _select_messages(self, *, firm, session, data: dict) -> list[dict]:
        now = timezone.now()
        qs = SiteMessage.objects.filter(firm=firm, status="published").filter(
            models.Q(active_from__lte=now) | models.Q(active_from__isnull=True),
            models.Q(active_until__gte=now) | models.Q(active_until__isnull=True),
        )
        if data.get("message_types"):
            qs = qs.filter(message_type__in=data["message_types"])

        selected: list[dict] = []
        for message in qs:
            if not self._matches_targeting(message=message, data=data):
                continue
            if self._frequency_exceeded(message=message, firm=firm, visitor_id=data["visitor_id"]):
                continue

            variant = self._select_variant(message=message, visitor_id=str(data["visitor_id"]))
            delivery_id = uuid4()
            impression = SiteMessageImpression.objects.create(
                firm=firm,
                site_message=message,
                session=session,
                visitor_id=data["visitor_id"],
                delivery_id=delivery_id,
                kind="delivered",
                variant=variant or "",
                url=data.get("url", ""),
            )
            payload = SiteMessageSerializer(message).data
            payload["delivery_id"] = str(delivery_id)
            payload["variant"] = variant
            payload["frequency_cap"] = message.frequency_cap
            if variant and isinstance(message.content, dict):
                variant_content = message.content.get("variants", {}).get(variant)
                if variant_content:
                    payload["content"] = variant_content
            # include delivery timestamp for transparency
            payload["delivered_at"] = impression.occurred_at
            selected.append(payload)
            if len(selected) >= data.get("limit", 3):
                break
        return selected

    def _matches_targeting(self, *, message: SiteMessage, data: dict) -> bool:
        rules = message.targeting_rules or {}
        segments_required = set(rules.get("segments") or [])
        visitor_segments = set(data.get("segments") or [])
        if segments_required and not segments_required.intersection(visitor_segments):
            return False

        audience = rules.get("audience") or {}
        allow_anonymous = audience.get("allow_anonymous", True)
        allow_known = audience.get("allow_known", True)
        is_known = data.get("contact_id") is not None
        if is_known and not allow_known:
            return False
        if not is_known and not allow_anonymous:
            return False

        behaviors = rules.get("behaviors") or {}
        url_contains = behaviors.get("url_contains") or behaviors.get("page_url_contains") or []
        url = (data.get("url") or "").lower()
        if url_contains:
            if not any(fragment.lower() in url for fragment in url_contains):
                return False

        event_contains = behaviors.get("event_name_contains") or []
        if event_contains:
            recent_events = [evt.lower() for evt in data.get("recent_events") or []]
            if not any(term.lower() in evt for term in event_contains for evt in recent_events):
                return False

        min_sessions = behaviors.get("min_sessions")
        if min_sessions and data.get("session_count", 1) < min_sessions:
            return False

        min_page_views = behaviors.get("min_page_views")
        if min_page_views and data.get("page_view_count", 0) < min_page_views:
            return False

        return True

    def _frequency_exceeded(self, *, message: SiteMessage, firm, visitor_id) -> bool:
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_impressions = SiteMessageImpression.objects.filter(
            firm=firm,
            site_message=message,
            visitor_id=visitor_id,
            occurred_at__gte=today_start,
            kind="delivered",
        ).count()
        return recent_impressions >= message.frequency_cap

    def _select_variant(self, *, message: SiteMessage, visitor_id: str) -> str | None:
        variants = (message.targeting_rules or {}).get("experiments") or []
        if not variants:
            return None
        idx_seed = hashlib.sha256(f"{visitor_id}:{message.id}".encode("utf-8")).hexdigest()
        idx = int(idx_seed, 16) % len(variants)
        return variants[idx]


class SiteMessageImpressionView(APIView):
    """Record view or click interactions for previously delivered site messages."""

    authentication_classes: list = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SiteMessageImpressionLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delivery = serializer.validated_data["delivery_id"]
        event = serializer.validated_data["event"]
        base_impression = (
            SiteMessageImpression.objects.filter(delivery_id=delivery, kind="delivered")
            .select_related("site_message", "session", "firm")
            .first()
        )
        if not base_impression:
            return Response({"detail": "Unknown delivery id"}, status=status.HTTP_404_NOT_FOUND)

        SiteMessageImpression.objects.create(
            firm=base_impression.firm,
            site_message=base_impression.site_message,
            session=base_impression.session,
            visitor_id=base_impression.visitor_id,
            delivery_id=delivery,
            kind=event,
            variant=serializer.validated_data.get("variant") or base_impression.variant,
            url=serializer.validated_data.get("url", ""),
        )
        return Response({"recorded": True}, status=status.HTTP_201_CREATED)


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


class SiteMessageAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        firm = getattr(request, "firm", None)
        if not firm or not FirmMembership.objects.filter(
            user=request.user, firm=firm, is_active=True, can_view_reports=True
        ).exists():
            return Response({"detail": "Firm analytics access required"}, status=status.HTTP_403_FORBIDDEN)

        try:
            days = int(request.query_params.get("days", "30"))
        except (ValueError, TypeError):
            days = 30
        days = min(max(days, 1), 90)
        raw_message_id = request.query_params.get("message_id")
        since = timezone.now() - timedelta(days=days)

        impressions = SiteMessageImpression.objects.filter(firm=firm, occurred_at__gte=since)
        if raw_message_id:
            try:
                message_id = int(raw_message_id)
            except (TypeError, ValueError):
                return Response({"detail": "Invalid message_id parameter"}, status=status.HTTP_400_BAD_REQUEST)

        rollups = (
            impressions.values("site_message_id", "site_message__name", "variant")
            .annotate(
                delivered=Count("id", filter=Q(kind="delivered")),
                views=Count("id", filter=Q(kind="view")),
                clicks=Count("id", filter=Q(kind="click")),
            )
            .order_by("-clicks", "-views")
        )

        formatted_rollups = []
        for row in rollups:
            delivered = row["delivered"] or 0
            views = row["views"] or 0
            clicks = row["clicks"] or 0
            formatted_rollups.append(
                {
                    "site_message_id": row["site_message_id"],
                    "site_message_name": row["site_message__name"],
                    "variant": row["variant"] or "",
                    "delivered": delivered,
                    "views": views,
                    "clicks": clicks,
                    "view_rate": round(views / delivered, 4) if delivered else 0,
                    "click_rate": round(clicks / delivered, 4) if delivered else 0,
                }
            )

        top_messages = (
            impressions.values("site_message_id", "site_message__name")
            .annotate(
                delivered=Count("id", filter=Q(kind="delivered")),
                views=Count("id", filter=Q(kind="view")),
                clicks=Count("id", filter=Q(kind="click")),
            )
            .order_by("-clicks", "-views")[:5]
        )

        top_list = []
        for row in top_messages:
            delivered = row["delivered"] or 0
            views = row["views"] or 0
            clicks = row["clicks"] or 0
            top_list.append(
                {
                    "site_message_id": row["site_message_id"],
                    "site_message_name": row["site_message__name"],
                    "delivered": delivered,
                    "views": views,
                    "clicks": clicks,
                    "view_rate": round(views / delivered, 4) if delivered else 0,
                    "click_rate": round(clicks / delivered, 4) if delivered else 0,
                }
            )

        return Response(
            {
                "window_days": days,
                "rollups": formatted_rollups,
                "top_messages": top_list,
                "export_path": "/api/v1/tracking/site-messages/analytics/export/",
            }
        )


class SiteMessageAnalyticsExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        firm = getattr(request, "firm", None)
        if not firm or not FirmMembership.objects.filter(
            user=request.user, firm=firm, is_active=True, can_view_reports=True
        ).exists():
            return Response({"detail": "Firm analytics access required"}, status=status.HTTP_403_FORBIDDEN)

        try:
            days = int(request.query_params.get("days", "30"))
        except (ValueError, TypeError):
            days = 30
        days = min(max(days, 1), 90)
        raw_message_id = request.query_params.get("message_id")
        since = timezone.now() - timedelta(days=days)

        impressions = SiteMessageImpression.objects.filter(firm=firm, occurred_at__gte=since)
        if raw_message_id:
            try:
                message_id = int(raw_message_id)
            except (TypeError, ValueError):
                return Response({"detail": "Invalid message_id parameter"}, status=status.HTTP_400_BAD_REQUEST)
            impressions = impressions.filter(site_message_id=message_id)

        rollups = impressions.values("site_message_id", "site_message__name", "variant").annotate(
            delivered=Count("id", filter=Q(kind="delivered")),
            views=Count("id", filter=Q(kind="view")),
            clicks=Count("id", filter=Q(kind="click")),
        ).order_by("-clicks", "-views")

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "site_message_id",
                "site_message_name",
                "variant",
                "delivered",
                "views",
                "clicks",
                "view_rate",
                "click_rate",
            ]
        )
        for row in rollups:
            delivered = row["delivered"] or 0
            views = row["views"] or 0
            clicks = row["clicks"] or 0
            writer.writerow(
                [
                    row["site_message_id"],
                    row["site_message__name"],
                    row["variant"] or "",
                    delivered,
                    views,
                    clicks,
                    round(views / delivered, 4) if delivered else 0,
                    round(clicks / delivered, 4) if delivered else 0,
                ]
            )

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=site-message-analytics.csv"
        return response
