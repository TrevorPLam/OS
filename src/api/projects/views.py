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
from modules.projects.models import (
    Project,
    ProjectTimeline,
    ResourceAllocation,
    ResourceCapacity,
    Task,
    TaskDependency,
    TaskSchedule,
    TimeEntry,
)

from .serializers import (
    ProjectSerializer,
    ProjectTimelineSerializer,
    ResourceAllocationSerializer,
    ResourceCapacitySerializer,
    TaskDependencySerializer,
    TaskScheduleSerializer,
    TaskSerializer,
    TimeEntrySerializer,
)


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
            
            date_errors = []
            if start_date:
                try:
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                except ValueError:
                    date_errors.append("start_date")
            if end_date:
                try:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    date_errors.append("end_date")
            
            if date_errors:
                return Response({
                    "error": f"Invalid date format for {', '.join(date_errors)}. Use YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            metrics = project.calculate_utilization_metrics(start_date, end_date)
            
            return Response({
                "project_id": project.id,
                "project_code": project.project_code,
                "project_name": project.name,
                "metrics": metrics,
            }, status=status.HTTP_200_OK)
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


class ResourceAllocationViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for ResourceAllocation model (Task 3.2).
    
    TIER 0: Scoped to request.firm via project relationship.
    TIER 2: Requires authentication.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """
    
    serializer_class = ResourceAllocationSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["project", "resource", "status", "allocation_type", "is_billable"]
    search_fields = ["role", "notes"]
    ordering_fields = ["start_date", "end_date", "allocation_percentage", "created_at"]
    ordering = ["start_date"]
    
    def get_queryset(self):
        """
        Override to scope by project__firm.
        
        TIER 0: ResourceAllocations inherit firm context from their Project.
        """
        firm = get_request_firm(self.request)
        return ResourceAllocation.objects.filter(
            project__firm=firm
        ).select_related("project", "resource", "created_by")
    
    @action(detail=False, methods=["get"])
    def conflicts(self, request):
        """
        Find resource allocation conflicts (over 100% allocation).
        
        GET /api/projects/resource-allocations/conflicts/
        Query params: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
        
        Returns resources that are over-allocated during the specified period.
        """
        from datetime import datetime
        from django.db.models import Sum
        
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        
        if not start_date or not end_date:
            return Response(
                {"error": "Both start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        firm = get_request_firm(request)
        
        # Find allocations in the date range
        allocations = ResourceAllocation.objects.filter(
            project__firm=firm,
            status__in=["planned", "active"],
            start_date__lte=end_date,
            end_date__gte=start_date,
        ).select_related("resource", "project")
        
        # Group by resource and calculate total allocation
        conflicts = {}
        for alloc in allocations:
            resource_id = alloc.resource_id
            if resource_id not in conflicts:
                conflicts[resource_id] = {
                    "resource": {
                        "id": alloc.resource.id,
                        "name": alloc.resource.get_full_name(),
                        "email": alloc.resource.email,
                    },
                    "total_allocation": 0,
                    "allocations": []
                }
            
            conflicts[resource_id]["total_allocation"] += float(alloc.allocation_percentage)
            conflicts[resource_id]["allocations"].append({
                "id": alloc.id,
                "project": alloc.project.name,
                "allocation_percentage": float(alloc.allocation_percentage),
                "start_date": alloc.start_date,
                "end_date": alloc.end_date,
                "role": alloc.role,
            })
        
        # Filter to only over-allocated resources
        over_allocated = [
            data for data in conflicts.values()
            if data["total_allocation"] > 100
        ]
        
        return Response({
            "start_date": start_date,
            "end_date": end_date,
            "conflicts_count": len(over_allocated),
            "conflicts": over_allocated,
        })


class ResourceCapacityViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for ResourceCapacity model (Task 3.2).
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2: Requires authentication.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """
    
    model = ResourceCapacity
    serializer_class = ResourceCapacitySerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["resource", "date", "unavailability_type"]
    ordering_fields = ["date", "resource", "created_at"]
    ordering = ["date"]
    
    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("resource", "firm")
    
    @action(detail=False, methods=["get"])
    def availability(self, request):
        """
        Get resource availability summary for a date range.
        
        GET /api/projects/resource-capacities/availability/
        Query params: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&resource=<user_id>
        
        Returns availability summary for resources during the specified period.
        """
        from datetime import datetime, timedelta
        from django.db.models import Sum
        
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        resource_id = request.query_params.get("resource")
        
        if not start_date or not end_date:
            return Response(
                {"error": "Both start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        firm = get_request_firm(request)
        
        # Build query
        capacities = ResourceCapacity.objects.filter(
            firm=firm,
            date__gte=start_date,
            date__lte=end_date,
        )
        
        if resource_id:
            capacities = capacities.filter(resource_id=resource_id)
        
        capacities = capacities.select_related("resource")
        
        # Calculate availability by resource
        availability = {}
        for capacity in capacities:
            resource_id = capacity.resource_id
            if resource_id not in availability:
                availability[resource_id] = {
                    "resource": {
                        "id": capacity.resource.id,
                        "name": capacity.resource.get_full_name(),
                        "email": capacity.resource.email,
                    },
                    "total_available_hours": 0,
                    "total_unavailable_hours": 0,
                    "net_available_hours": 0,
                }
            
            availability[resource_id]["total_available_hours"] += float(capacity.available_hours)
            availability[resource_id]["total_unavailable_hours"] += float(capacity.unavailable_hours)
            availability[resource_id]["net_available_hours"] += float(capacity.net_available_hours)
        
        return Response({
            "start_date": start_date,
            "end_date": end_date,
            "availability": list(availability.values()),
        })


class ProjectTimelineViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for ProjectTimeline model (Task 3.6).
    
    Provides CRUD operations for project timelines and Gantt chart data.
    
    TIER 0: Inherits firm from project via OneToOne relationship.
    TIER 2: DenyPortalAccess - portal users cannot access.
    """
    
    serializer_class = ProjectTimelineSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, BoundedSearchFilter]
    filterset_fields = ["project", "planned_start_date", "planned_end_date"]
    search_fields = ["project__project_code", "project__name"]
    ordering_fields = ["planned_start_date", "planned_end_date", "created_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Get timelines scoped to user's firm."""
        firm = get_request_firm(self.request)
        return ProjectTimeline.objects.filter(project__firm=firm).select_related("project")
    
    @action(detail=True, methods=["post"])
    def recalculate(self, request, pk=None):
        """
        Recalculate critical path and timeline data.
        
        This would trigger the critical path algorithm to update:
        - critical_path_task_ids
        - critical_path_duration_days
        - TaskSchedule early/late dates
        - TaskSchedule slack values
        
        Uses CPM-style critical path calculation to update scheduling fields
        and critical path metadata.
        """
        timeline = self.get_object()

        from django.utils import timezone
        from modules.projects.critical_path import (
            TaskNode,
            DependencyEdge,
            calculate_critical_path,
        )
        from modules.projects.models import TaskDependency, TaskSchedule

        project = timeline.project
        schedules = TaskSchedule.objects.filter(task__project=project).select_related("task")
        dependencies = TaskDependency.objects.filter(predecessor__project=project)

        tasks = [
            TaskNode(
                task_id=schedule.task_id,
                duration_days=schedule.planned_duration_days or 1,
                planned_start_date=schedule.planned_start_date,
            )
            for schedule in schedules
        ]
        dependency_edges = [
            DependencyEdge(
                predecessor_id=dependency.predecessor_id,
                successor_id=dependency.successor_id,
                dependency_type=dependency.dependency_type,
                lag_days=dependency.lag_days,
            )
            for dependency in dependencies
        ]

        try:
            schedule_map, critical_ids, critical_duration = calculate_critical_path(
                tasks=tasks,
                dependencies=dependency_edges,
                project_start_date=project.start_date,
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_at = timezone.now()
        milestone_count = 0
        completed_tasks = 0

        for schedule in schedules:
            computed = schedule_map.get(schedule.task_id)
            if not computed:
                continue
            schedule.early_start_date = computed.early_start
            schedule.early_finish_date = computed.early_finish
            schedule.late_start_date = computed.late_start
            schedule.late_finish_date = computed.late_finish
            schedule.total_slack_days = computed.total_slack_days
            schedule.is_on_critical_path = computed.is_critical
            schedule.save(
                update_fields=[
                    "early_start_date",
                    "early_finish_date",
                    "late_start_date",
                    "late_finish_date",
                    "total_slack_days",
                    "is_on_critical_path",
                    "updated_at",
                ]
            )

            if schedule.is_milestone:
                milestone_count += 1
            if schedule.task.status == "done":
                completed_tasks += 1

        timeline.critical_path_task_ids = critical_ids
        timeline.critical_path_duration_days = critical_duration
        timeline.total_tasks = schedules.count()
        timeline.completed_tasks = completed_tasks
        timeline.milestone_count = milestone_count
        timeline.last_calculated_at = updated_at
        timeline.calculation_metadata = {
            "calculated_at": updated_at.isoformat(),
            "dependency_types": ["finish_to_start", "start_to_start", "finish_to_finish", "start_to_finish"],
            "complexity": "O(V+E)",
            "notes": "Planned start dates are treated as minimum constraints.",
        }
        timeline.save()

        serializer = self.get_serializer(timeline)
        return Response(serializer.data)


class TaskScheduleViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for TaskSchedule model (Task 3.6).
    
    Provides CRUD operations for task scheduling data.
    
    TIER 0: Inherits firm from task.project via OneToOne relationship.
    TIER 2: DenyPortalAccess - portal users cannot access.
    """
    
    serializer_class = TaskScheduleSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, BoundedSearchFilter]
    filterset_fields = [
        "task",
        "task__project",
        "is_on_critical_path",
        "is_milestone",
        "constraint_type",
        "planned_start_date",
    ]
    search_fields = ["task__title", "task__project__name"]
    ordering_fields = ["planned_start_date", "planned_end_date", "completion_percentage"]
    ordering = ["planned_start_date"]
    
    def get_queryset(self):
        """Get schedules scoped to user's firm."""
        firm = get_request_firm(self.request)
        return TaskSchedule.objects.filter(
            task__project__firm=firm
        ).select_related("task", "task__project")
    
    @action(detail=False, methods=["get"])
    def critical_path_tasks(self, request):
        """
        Get all tasks on the critical path for a project.
        
        Query params:
        - project: Project ID (required)
        """
        project_id = request.query_params.get("project")
        if not project_id:
            return Response(
                {"error": "project parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        firm = get_request_firm(request)
        schedules = self.get_queryset().filter(
            task__project_id=project_id,
            task__project__firm=firm,
            is_on_critical_path=True
        )
        
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def milestones(self, request):
        """
        Get all milestones for a project.
        
        Query params:
        - project: Project ID (required)
        """
        project_id = request.query_params.get("project")
        if not project_id:
            return Response(
                {"error": "project parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        firm = get_request_firm(request)
        schedules = self.get_queryset().filter(
            task__project_id=project_id,
            task__project__firm=firm,
            is_milestone=True
        ).order_by("milestone_date")
        
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)


class TaskDependencyViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for TaskDependency model (Task 3.6).
    
    Provides CRUD operations for task dependencies.
    
    TIER 0: Inherits firm from predecessor/successor tasks.
    TIER 2: DenyPortalAccess - portal users cannot access.
    """
    
    serializer_class = TaskDependencySerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["predecessor", "successor", "predecessor__project", "dependency_type"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Get dependencies scoped to user's firm."""
        firm = get_request_firm(self.request)
        return TaskDependency.objects.filter(
            predecessor__project__firm=firm
        ).select_related(
            "predecessor",
            "successor",
            "predecessor__project",
            "successor__project"
        )
    
    @action(detail=False, methods=["get"])
    def project_dependencies(self, request):
        """
        Get all dependencies for a project.
        
        Query params:
        - project: Project ID (required)
        """
        project_id = request.query_params.get("project")
        if not project_id:
            return Response(
                {"error": "project parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        firm = get_request_firm(request)
        dependencies = self.get_queryset().filter(
            predecessor__project_id=project_id,
            predecessor__project__firm=firm
        )
        
        serializer = self.get_serializer(dependencies, many=True)
        return Response(serializer.data)
