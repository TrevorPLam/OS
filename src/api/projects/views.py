"""
DRF ViewSets for Projects module.

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
from modules.firm.utils import FirmScopedMixin, get_request_firm
from modules.projects.models import Project, Task, TimeEntry

from .serializers import ProjectSerializer, TaskSerializer, TimeEntrySerializer


class ProjectViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Project model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2: Requires authentication.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["client", "status", "billing_type", "project_manager"]
    search_fields = ["project_code", "name"]
    ordering_fields = ["project_code", "created_at", "start_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("client", "contract", "project_manager")
    
    @action(detail=True, methods=["post"])
    def mark_client_accepted(self, request, pk=None):
        """
        Mark project as client-accepted (Medium Feature 2.8).
        
        POST /api/projects/projects/{id}/mark_client_accepted/
        Body: { "notes": "Optional acceptance notes" }
        
        This establishes a gate for invoice generation.
        Projects must be client-accepted before final invoicing.
        """
        try:
            project = self.get_object()
            notes = request.data.get("notes", "")
            project.mark_client_accepted(request.user, notes=notes)
            serializer = self.get_serializer(project)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["get"])
    def can_invoice(self, request, pk=None):
        """
        Check if project can generate invoices (Medium Feature 2.8).
        
        GET /api/projects/projects/{id}/can_invoice/
        
        Returns whether the project can be invoiced and why/why not.
        """
        try:
            project = self.get_object()
            can_invoice, reason = project.can_generate_invoice()
            return Response({
                "can_invoice": can_invoice,
                "reason": reason,
                "client_accepted": project.client_accepted,
                "acceptance_date": project.acceptance_date,
                "accepted_by": project.accepted_by.email if project.accepted_by else None,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=["get"])
    def utilization(self, request, pk=None):
        """
        Get project utilization metrics (Medium Feature 2.9).
        
        GET /api/projects/projects/{id}/utilization/
        Query params:
        - start_date: Optional YYYY-MM-DD format
        - end_date: Optional YYYY-MM-DD format
        
        Returns utilization metrics for the project including billable hours,
        utilization rate, team size, and hours vs budget.
        """
        from datetime import datetime
        
        try:
            project = self.get_object()
            
            # Parse date filters from query params
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")
            
            if start_date:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            metrics = project.calculate_utilization_metrics(start_date, end_date)
            
            return Response({
                "project_id": project.id,
                "project_code": project.project_code,
                "project_name": project.name,
                "metrics": metrics,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({
                "error": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["get"])
    def team_utilization(self, request):
        """
        Get team utilization metrics (Medium Feature 2.9).
        
        GET /api/projects/projects/team_utilization/
        Query params (required):
        - start_date: YYYY-MM-DD format
        - end_date: YYYY-MM-DD format
        - user_id: Optional - specific user ID to calculate for
        
        Returns utilization metrics for team members across all projects.
        """
        from datetime import datetime
        from modules.firm.models import FirmMembership
        
        try:
            # Required date range
            start_date_str = request.query_params.get("start_date")
            end_date_str = request.query_params.get("end_date")
            
            if not start_date_str or not end_date_str:
                return Response({
                    "error": "start_date and end_date query parameters are required (YYYY-MM-DD)"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
            firm = get_request_firm(request)
            user_id = request.query_params.get("user_id")
            
            results = []
            
            if user_id:
                # Single user
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id)
                    metrics = Project.calculate_user_utilization(firm, user, start_date, end_date)
                    results.append(metrics)
                except User.DoesNotExist:
                    return Response({"error": f"User {user_id} not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                # All team members
                memberships = FirmMembership.objects.filter(firm=firm, is_active=True)
                for membership in memberships:
                    metrics = Project.calculate_user_utilization(firm, membership.user, start_date, end_date)
                    results.append(metrics)
            
            return Response({
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "team_members": len(results),
                "utilization_data": results,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({
                "error": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Task model.

    TIER 0: Scoped to request.firm via project relationship.
    TIER 2: Requires authentication.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    Note: Task doesn't have direct firm FK, so we filter via project__firm.
    """

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["project", "status", "priority", "assigned_to"]
    search_fields = ["title", "description"]
    ordering_fields = ["position", "created_at", "due_date"]
    ordering = ["position", "-created_at"]

    def get_queryset(self):
        """
        Override to scope by project__firm.

        TIER 0: Tasks inherit firm context from their Project.
        """
        firm = get_request_firm(self.request)
        return Task.objects.filter(project__firm=firm).select_related("project", "assigned_to")


class TimeEntryViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for TimeEntry model.

    TIER 0: Scoped to request.firm via project relationship.
    TIER 2: Requires authentication.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    Note: TimeEntry doesn't have direct firm FK, so we filter via project__firm.
    """

    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["project", "user", "task", "is_billable", "invoiced", "date"]
    search_fields = ["description"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-date", "-created_at"]

    def get_queryset(self):
        """
        Override to scope by project__firm.

        TIER 0: TimeEntries inherit firm context from their Project.
        """
        firm = get_request_firm(self.request)
        return TimeEntry.objects.filter(project__firm=firm).select_related("project", "task", "user", "invoice")
