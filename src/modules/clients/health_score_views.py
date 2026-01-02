"""
Client Health Score Views

API endpoints for managing and viewing client health scores.
"""

from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.clients.models import Client
from modules.clients.health_score import (
    ClientHealthScore,
    ClientHealthScoreConfig,
    ClientHealthScoreAlert,
)
from modules.clients.health_score_calculator import HealthScoreCalculator, calculate_all_client_health_scores
from modules.clients.serializers import (
    ClientHealthScoreConfigSerializer,
    ClientHealthScoreSerializer,
    ClientHealthScoreAlertSerializer,
    ClientHealthScoreSummarySerializer,
)
from modules.firm.permissions import HasFirmPermission


class ClientHealthScoreConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing health score configuration.
    
    Allows firms to customize their health score calculation parameters.
    """
    
    serializer_class = ClientHealthScoreConfigSerializer
    permission_classes = [IsAuthenticated, HasFirmPermission]
    
    def get_queryset(self):
        """Filter configs to current firm."""
        return ClientHealthScoreConfig.objects.filter(
            firm=self.request.user.firm
        )
    
    def perform_create(self, serializer):
        """Set firm and created_by on creation."""
        serializer.save(
            firm=self.request.user.firm,
            created_by=self.request.user
        )


class ClientHealthScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing client health scores.
    
    Provides endpoints for:
    - Listing all client health scores
    - Getting specific client's score history
    - Calculating new scores
    - Dashboard summary statistics
    """
    
    serializer_class = ClientHealthScoreSerializer
    permission_classes = [IsAuthenticated, HasFirmPermission]
    
    def get_queryset(self):
        """Filter scores to current firm."""
        queryset = ClientHealthScore.objects.filter(
            firm=self.request.user.firm
        ).select_related("client")
        
        # Filter by client if specified
        client_id = self.request.query_params.get("client_id")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by at-risk status
        at_risk = self.request.query_params.get("at_risk")
        if at_risk is not None:
            at_risk_bool = at_risk.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(is_at_risk=at_risk_bool)
        
        # Filter by date range
        days = self.request.query_params.get("days")
        if days:
            try:
                days_int = int(days)
                start_date = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(calculated_at__gte=start_date)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=["post"])
    def calculate(self, request):
        """
        Calculate health score for a specific client or all clients.
        
        POST /api/clients/health-scores/calculate/
        Body: {"client_id": 123} or {} for all clients
        """
        client_id = request.data.get("client_id")
        
        if client_id:
            # Calculate for specific client
            try:
                client = Client.objects.get(
                    id=client_id,
                    firm=request.user.firm
                )
                calculator = HealthScoreCalculator(client)
                health_score = calculator.calculate()
                
                serializer = self.get_serializer(health_score)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Client.DoesNotExist:
                return Response(
                    {"error": "Client not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Calculate for all active clients
            count = calculate_all_client_health_scores(request.user.firm.id)
            return Response(
                {
                    "message": f"Calculated health scores for {count} clients",
                    "count": count
                },
                status=status.HTTP_201_CREATED
            )
    
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get health score summary statistics.
        
        GET /api/clients/health-scores/summary/
        """
        firm = request.user.firm
        
        # Get latest score for each client
        from django.db.models import Max
        
        latest_scores = ClientHealthScore.objects.filter(
            firm=firm
        ).values("client").annotate(
            latest_date=Max("calculated_at")
        )
        
        latest_score_ids = []
        for item in latest_scores:
            score = ClientHealthScore.objects.filter(
                firm=firm,
                client_id=item["client"],
                calculated_at=item["latest_date"]
            ).first()
            if score:
                latest_score_ids.append(score.id)
        
        latest_scores_qs = ClientHealthScore.objects.filter(
            id__in=latest_score_ids
        )
        
        # Calculate statistics
        total_clients = latest_scores_qs.count()
        at_risk_count = latest_scores_qs.filter(is_at_risk=True).count()
        
        avg_score = latest_scores_qs.aggregate(
            avg=Avg("score")
        )["avg"] or 0
        
        # Pending alerts
        pending_alerts = ClientHealthScoreAlert.objects.filter(
            firm=firm,
            status="pending"
        ).count()
        
        # Score distribution
        score_ranges = {
            "0-25": latest_scores_qs.filter(score__lte=25).count(),
            "26-50": latest_scores_qs.filter(score__gt=25, score__lte=50).count(),
            "51-75": latest_scores_qs.filter(score__gt=50, score__lte=75).count(),
            "76-100": latest_scores_qs.filter(score__gt=75).count(),
        }
        
        summary_data = {
            "total_clients": total_clients,
            "at_risk_count": at_risk_count,
            "pending_alerts": pending_alerts,
            "average_score": round(avg_score, 1),
            "score_distribution": score_ranges,
        }
        
        serializer = ClientHealthScoreSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def at_risk(self, request):
        """
        Get list of at-risk clients with their latest scores.
        
        GET /api/clients/health-scores/at-risk/
        """
        firm = request.user.firm
        
        # Get latest score for each at-risk client
        from django.db.models import Max
        
        latest_scores = ClientHealthScore.objects.filter(
            firm=firm,
            is_at_risk=True
        ).values("client").annotate(
            latest_date=Max("calculated_at")
        )
        
        at_risk_scores = []
        for item in latest_scores:
            score = ClientHealthScore.objects.filter(
                firm=firm,
                client_id=item["client"],
                calculated_at=item["latest_date"]
            ).select_related("client").first()
            if score:
                at_risk_scores.append(score)
        
        # Sort by score (lowest first)
        at_risk_scores.sort(key=lambda x: x.score)
        
        serializer = self.get_serializer(at_risk_scores, many=True)
        return Response(serializer.data)


class ClientHealthScoreAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing health score alerts.
    
    Allows viewing and managing alerts for significant score drops.
    """
    
    serializer_class = ClientHealthScoreAlertSerializer
    permission_classes = [IsAuthenticated, HasFirmPermission]
    
    def get_queryset(self):
        """Filter alerts to current firm."""
        queryset = ClientHealthScoreAlert.objects.filter(
            firm=self.request.user.firm
        ).select_related("client", "health_score")
        
        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by client
        client_id = self.request.query_params.get("client_id")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        return queryset
    
    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        """
        Acknowledge an alert.
        
        POST /api/clients/health-score-alerts/{id}/acknowledge/
        """
        alert = self.get_object()
        
        if alert.status != "pending":
            return Response(
                {"error": "Only pending alerts can be acknowledged"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert.status = "acknowledged"
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """
        Resolve an alert with notes.
        
        POST /api/clients/health-score-alerts/{id}/resolve/
        Body: {"resolution_notes": "explanation"}
        """
        alert = self.get_object()
        
        if alert.status == "resolved":
            return Response(
                {"error": "Alert is already resolved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resolution_notes = request.data.get("resolution_notes", "")
        
        alert.status = "resolved"
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.resolution_notes = resolution_notes
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        """
        Dismiss an alert.
        
        POST /api/clients/health-score-alerts/{id}/dismiss/
        """
        alert = self.get_object()
        
        alert.status = "dismissed"
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
