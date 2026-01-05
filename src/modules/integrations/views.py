from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.firm.models import FirmMembership
from modules.integrations.models import (
    GoogleAnalyticsConfig,
    SalesforceConnection,
    SalesforceSyncLog,
    SlackIntegration,
    SlackMessageLog,
)
from modules.integrations.serializers import (
    GoogleAnalyticsConfigSerializer,
    GoogleAnalyticsEventSerializer,
    SalesforceConnectionSerializer,
    SalesforceSyncRequestSerializer,
    SlackIntegrationSerializer,
    SlackTestMessageSerializer,
)
from modules.integrations.services import GoogleAnalyticsService, SalesforceService, SlackService


class BaseFirmScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    model = None  # type: ignore

    def get_queryset(self):
        firm = getattr(self.request, "firm", None)
        if not firm or not self._can_manage_settings(firm):
            return self.model.objects.none()
        return self.model.objects.filter(firm=firm)

    def perform_create(self, serializer):
        firm = getattr(self.request, "firm", None)
        if not firm or not self._can_manage_settings(firm):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Firm context and manage-settings permission required.")
        serializer.save(firm=firm, created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def _can_manage_settings(self, firm) -> bool:
        return FirmMembership.objects.filter(
            user=self.request.user, firm=firm, is_active=True, can_manage_settings=True
        ).exists()


class SalesforceConnectionViewSet(BaseFirmScopedViewSet):
    serializer_class = SalesforceConnectionSerializer
    model = SalesforceConnection

    @action(detail=True, methods=["post"])
    def refresh(self, request, pk=None):
        connection = self.get_object()
        service = SalesforceService(connection)
        result = service.refresh_access_token()
        status_code = status.HTTP_200_OK if result.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        serializer = SalesforceSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        connection = self.get_object()
        service = SalesforceService(connection)
        object_type = serializer.validated_data["object_type"]
        payload = serializer.validated_data["payload"]
        if object_type == "contact":
            log = service.upsert_contact(payload=payload)
        elif object_type == "lead":
            log = service.upsert_lead(payload=payload)
        else:
            log = service.sync_opportunity(payload=payload)
        return Response(
            {"status": log.status, "message": log.message, "payload_snippet": log.payload_snippet},
            status=status.HTTP_200_OK if log.status == "success" else status.HTTP_400_BAD_REQUEST,
        )


class SlackIntegrationViewSet(BaseFirmScopedViewSet):
    serializer_class = SlackIntegrationSerializer
    model = SlackIntegration

    @action(detail=True, methods=["post"])
    def send_test(self, request, pk=None):
        integration = self.get_object()
        serializer = SlackTestMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        service = SlackService(integration)
        ok = service.send_message(text=payload["text"], channel=payload.get("channel"))
        return Response({"ok": ok}, status=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST)


class GoogleAnalyticsConfigViewSet(BaseFirmScopedViewSet):
    serializer_class = GoogleAnalyticsConfigSerializer
    model = GoogleAnalyticsConfig

    @action(detail=True, methods=["post"], url_path="send-test")
    def send_test(self, request, pk=None):
        config = self.get_object()
        serializer = GoogleAnalyticsEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        service = GoogleAnalyticsService(config)
        result = service.send_events(client_id=payload["client_id"], events=payload["events"])
        status_code = status.HTTP_200_OK if result.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)


class IntegrationHealthView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        firm = getattr(request, "firm", None)
        if not firm or not FirmMembership.objects.filter(
            user=request.user, firm=firm, is_active=True, can_manage_settings=True
        ).exists():
            return Response({"detail": "Firm settings access required"}, status=status.HTTP_403_FORBIDDEN)

        since = timezone.now() - timedelta(days=1)
        alerts = []

        salesforce_cards = []
        for connection in SalesforceConnection.objects.filter(firm=firm):
            error_count = SalesforceSyncLog.objects.filter(
                firm=firm, connection=connection, status="error", occurred_at__gte=since
            ).count()
            token_expiring = bool(connection.expires_at and connection.expires_at <= timezone.now() + timedelta(days=3))
            status_label = "warning" if error_count >= 3 or token_expiring else connection.status
            salesforce_cards.append(
                {
                    "id": connection.id,
                    "status": status_label,
                    "last_synced_at": connection.last_synced_at,
                    "expires_at": connection.expires_at,
                    "last_error": connection.last_error,
                    "error_count_24h": error_count,
                    "token_expiring": token_expiring,
                }
            )
            if error_count >= 3:
                alerts.append(
                    {
                        "integration": "salesforce",
                        "level": "warning",
                        "message": "Repeated Salesforce sync failures detected in the last 24 hours.",
                        "connection_id": connection.id,
                    }
                )
            if token_expiring:
                alerts.append(
                    {
                        "integration": "salesforce",
                        "level": "warning",
                        "message": "Salesforce token is nearing expiration.",
                        "connection_id": connection.id,
                    }
                )

        slack_cards = []
        for integration in SlackIntegration.objects.filter(firm=firm):
            error_count = SlackMessageLog.objects.filter(
                firm=firm, integration=integration, status="error", occurred_at__gte=since
            ).count()
            status_label = "warning" if error_count >= 3 else integration.status
            slack_cards.append(
                {
                    "id": integration.id,
                    "status": status_label,
                    "last_health_check": integration.last_health_check,
                    "last_error": integration.last_error,
                    "error_count_24h": error_count,
                }
            )
            if error_count >= 3:
                alerts.append(
                    {
                        "integration": "slack",
                        "level": "warning",
                        "message": "Repeated Slack delivery failures detected in the last 24 hours.",
                        "integration_id": integration.id,
                    }
                )

        ga_cards = []
        for config in GoogleAnalyticsConfig.objects.filter(firm=firm):
            status_label = "warning" if config.status == "error" else config.status
            ga_cards.append(
                {
                    "id": config.id,
                    "status": status_label,
                    "last_event_at": config.last_event_at,
                    "last_error": config.last_error,
                }
            )
            if config.status == "error":
                alerts.append(
                    {
                        "integration": "google_analytics",
                        "level": "warning",
                        "message": "Google Analytics integration is reporting errors.",
                        "config_id": config.id,
                    }
                )

        return Response(
            {
                "generated_at": timezone.now().isoformat(),
                "cards": {
                    "salesforce": salesforce_cards,
                    "slack": slack_cards,
                    "google_analytics": ga_cards,
                },
                "alerts": alerts,
            }
        )
