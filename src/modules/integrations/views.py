from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from modules.firm.models import FirmMembership
from modules.integrations.models import GoogleAnalyticsConfig, SalesforceConnection, SlackIntegration
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
