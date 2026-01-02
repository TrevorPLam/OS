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

from modules.clients.models import Client, ClientHealthScore
from modules.clients.health_score_calculator import HealthScoreCalculator, calculate_all_client_health_scores
from modules.clients.serializers import (
    ClientHealthScoreSerializer,
)
from modules.firm.permissions import HasFirmPermission


class ClientHealthScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and managing client health scores.
    
    Provides endpoints for:
    - Listing all client health scores
    - Getting specific client's score
    - Calculating/updating scores
    - Dashboard summary statistics
    """
    
    serializer_class = ClientHealthScoreSerializer
    permission_classes = [IsAuthenticated, HasFirmPermission]
    
    def get_queryset(self):
        """Filter scores to current firm (via client relationship)."""
        queryset = ClientHealthScore.objects.filter(
            client__firm=self.request.user.firm
        ).select_related("client")
        
        # Filter by at-risk status
        at_risk = self.request.query_params.get("at_risk")
        if at_risk is not None:
            at_risk_bool = at_risk.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(is_at_risk=at_risk_bool)
        
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
                return Response(serializer.data, status=status.HTTP_200_OK)
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
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get health score summary statistics.
        
        GET /api/clients/health-scores/summary/
        """
        firm = request.user.firm
        
        # Get all health scores for firm
        health_scores = ClientHealthScore.objects.filter(
            client__firm=firm
        )
        
        # Calculate statistics
        total_clients = health_scores.count()
        at_risk_count = health_scores.filter(is_at_risk=True).count()
        
        avg_score = health_scores.aggregate(
            avg=Avg("score")
        )["avg"] or 0
        
        # Score distribution
        score_ranges = {
            "0-25": health_scores.filter(score__lte=25).count(),
            "26-50": health_scores.filter(score__gt=25, score__lte=50).count(),
            "51-75": health_scores.filter(score__gt=50, score__lte=75).count(),
            "76-100": health_scores.filter(score__gt=75).count(),
        }
        
        summary_data = {
            "total_clients": total_clients,
            "at_risk_count": at_risk_count,
            "average_score": round(avg_score, 1),
            "score_distribution": score_ranges,
        }
        
        return Response(summary_data)
    
    @action(detail=False, methods=["get"])
    def at_risk(self, request):
        """
        Get list of at-risk clients with their scores.
        
        GET /api/clients/health-scores/at-risk/
        """
        firm = request.user.firm
        
        # Get all at-risk health scores
        at_risk_scores = ClientHealthScore.objects.filter(
            client__firm=firm,
            is_at_risk=True
        ).select_related("client").order_by("score")
        
        serializer = self.get_serializer(at_risk_scores, many=True)
        return Response(serializer.data)
