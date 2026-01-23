"""
DRF ViewSets for Webhooks module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.core.observability import get_correlation_id
from modules.firm.utils import FirmScopedMixin, get_request_firm
from modules.webhooks.models import WebhookDelivery, WebhookEndpoint
from modules.webhooks.queue import queue_webhook_delivery

from .serializers import (
    WebhookDeliverySerializer,
    WebhookEndpointSerializer,
    WebhookEventSerializer,
)


class WebhookEndpointViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for WebhookEndpoint model (Task 3.7).
    
    Provides CRUD operations for webhook endpoints and event subscription management.
    
    TIER 0: FirmScopedMixin ensures firm-level isolation.
    TIER 2: DenyPortalAccess - portal users cannot access.
    """
    
    serializer_class = WebhookEndpointSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, BoundedSearchFilter]
    filterset_fields = ["status", "created_at"]
    search_fields = ["name", "url", "description"]
    ordering_fields = ["name", "created_at", "last_delivery_at", "total_deliveries"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Get webhooks scoped to user's firm."""
        firm = get_request_firm(self.request)
        return WebhookEndpoint.objects.filter(firm=firm).select_related("firm", "created_by")
    
    @action(detail=True, methods=["post"])
    def regenerate_secret(self, request, pk=None):
        """
        Regenerate the webhook secret key.
        
        This will invalidate the old secret. Use this if the secret is compromised
        or needs to be rotated for security purposes.
        """
        webhook = self.get_object()
        webhook.secret = webhook._generate_secret()
        webhook.save()
        
        serializer = self.get_serializer(webhook)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """
        Pause this webhook endpoint.
        
        Paused webhooks will not receive any events until reactivated.
        """
        webhook = self.get_object()
        webhook.status = "paused"
        webhook.save()
        
        serializer = self.get_serializer(webhook)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """
        Activate this webhook endpoint.
        
        Activated webhooks will start receiving events again.
        """
        webhook = self.get_object()
        webhook.status = "active"
        webhook.save()
        
        serializer = self.get_serializer(webhook)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """
        Test this webhook endpoint by sending a test event.
        
        Request body:
        {
            "event_type": "test.event",
            "payload": {"message": "Test event"}
        }
        
        This will create a webhook delivery and attempt to send it to the endpoint.
        """
        webhook = self.get_object()
        
        # Validate request data
        event_serializer = WebhookEventSerializer(data=request.data)
        event_serializer.is_valid(raise_exception=True)
        
        event_type = event_serializer.validated_data["event_type"]
        payload = event_serializer.validated_data["payload"]
        
        # Create delivery
        import uuid
        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=webhook,
            event_type=event_type,
            event_id=f"test-{uuid.uuid4()}",
            payload=payload,
            status="pending"
        )

        correlation_id = get_correlation_id(request)
        queue_webhook_delivery(delivery, correlation_id=correlation_id)
        
        delivery_serializer = WebhookDeliverySerializer(delivery)
        return Response({
            "message": "Test event queued for delivery",
            "delivery": delivery_serializer.data
        })
    
    @action(detail=True, methods=["get"])
    def statistics(self, request, pk=None):
        """
        Get detailed statistics for this webhook endpoint.
        
        Returns:
        - Success rate
        - Total deliveries
        - Successful deliveries
        - Failed deliveries
        - Average response time
        - Recent delivery history
        """
        webhook = self.get_object()
        
        # Get recent deliveries for trend analysis
        recent_deliveries = webhook.deliveries.order_by("-created_at")[:100]
        
        # Calculate average response time
        completed_deliveries = recent_deliveries.filter(completed_at__isnull=False)
        total_duration = 0
        count = 0
        for delivery in completed_deliveries:
            if delivery.duration_seconds:
                total_duration += delivery.duration_seconds
                count += 1
        
        avg_response_time = total_duration / count if count > 0 else 0
        
        # Group by status
        status_counts = {}
        for delivery in recent_deliveries:
            status_counts[delivery.status] = status_counts.get(delivery.status, 0) + 1
        
        return Response({
            "webhook_id": webhook.id,
            "webhook_name": webhook.name,
            "total_deliveries": webhook.total_deliveries,
            "successful_deliveries": webhook.successful_deliveries,
            "failed_deliveries": webhook.failed_deliveries,
            "success_rate": webhook.success_rate,
            "average_response_time_seconds": round(avg_response_time, 2),
            "last_delivery_at": webhook.last_delivery_at,
            "last_success_at": webhook.last_success_at,
            "last_failure_at": webhook.last_failure_at,
            "recent_status_breakdown": status_counts,
        })


class WebhookDeliveryViewSet(QueryTimeoutMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WebhookDelivery model (Task 3.7).
    
    Provides read-only access to webhook deliveries for monitoring and debugging.
    
    TIER 0: Inherits firm from webhook_endpoint.
    TIER 2: DenyPortalAccess - portal users cannot access.
    """
    
    serializer_class = WebhookDeliverySerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["webhook_endpoint", "event_type", "status", "http_status_code"]
    ordering_fields = ["created_at", "completed_at", "attempts"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Get deliveries scoped to user's firm."""
        firm = get_request_firm(self.request)
        return WebhookDelivery.objects.filter(
            webhook_endpoint__firm=firm
        ).select_related("webhook_endpoint")
    
    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        """
        Retry a failed delivery.
        
        Only deliveries that have not exceeded max retries can be retried.
        """
        delivery = self.get_object()
        
        if not delivery.should_retry():
            return Response(
                {
                    "error": "Delivery cannot be retried",
                    "reason": "Max retries exceeded or delivery already succeeded"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark for retry
        delivery.status = "retrying"
        delivery.next_retry_at = delivery.calculate_next_retry_time()
        delivery.save()

        correlation_id = get_correlation_id(request)
        queue_webhook_delivery(
            delivery,
            correlation_id=correlation_id,
            scheduled_at=delivery.next_retry_at,
        )
        
        serializer = self.get_serializer(delivery)
        return Response({
            "message": "Delivery marked for retry",
            "delivery": serializer.data
        })
    
    @action(detail=False, methods=["get"])
    def failed(self, request):
        """
        Get all failed deliveries.
        
        Query params:
        - webhook_endpoint: Filter by webhook endpoint ID
        - event_type: Filter by event type
        """
        queryset = self.get_queryset().filter(status="failed")
        
        # Apply filters
        webhook_id = request.query_params.get("webhook_endpoint")
        if webhook_id:
            queryset = queryset.filter(webhook_endpoint_id=webhook_id)
        
        event_type = request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def pending_retries(self, request):
        """
        Get all deliveries pending retry.
        
        Returns deliveries with status 'retrying' that have a next_retry_at set.
        """
        from django.utils import timezone
        
        queryset = self.get_queryset().filter(
            status="retrying",
            next_retry_at__lte=timezone.now()
        ).order_by("next_retry_at")
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
