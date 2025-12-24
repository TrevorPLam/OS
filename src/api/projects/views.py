"""
DRF ViewSets for Projects module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from modules.clients.permissions import DenyPortalAccess
from modules.projects.models import Project, Task, TimeEntry
from modules.firm.utils import FirmScopedMixin, get_request_firm
from .serializers import ProjectSerializer, TaskSerializer, TimeEntrySerializer


class ProjectViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Project model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2: Requires authentication.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'status', 'billing_type', 'project_manager']
    search_fields = ['project_code', 'name']
    ordering_fields = ['project_code', 'created_at', 'start_date']
    ordering = ['-created_at']

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related('client', 'contract', 'project_manager')


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task model.

    TIER 0: Scoped to request.firm via project relationship.
    TIER 2: Requires authentication.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    Note: Task doesn't have direct firm FK, so we filter via project__firm.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'priority', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['position', 'created_at', 'due_date']
    ordering = ['position', '-created_at']

    def get_queryset(self):
        """
        Override to scope by project__firm.

        TIER 0: Tasks inherit firm context from their Project.
        """
        firm = get_request_firm(self.request)
        return Task.objects.filter(project__firm=firm).select_related('project', 'assigned_to')


class TimeEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TimeEntry model.

    TIER 0: Scoped to request.firm via project relationship.
    TIER 2: Requires authentication.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    Note: TimeEntry doesn't have direct firm FK, so we filter via project__firm.
    """
    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'user', 'task', 'is_billable', 'invoiced', 'date']
    search_fields = ['description']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        """
        Override to scope by project__firm.

        TIER 0: TimeEntries inherit firm context from their Project.
        """
        firm = get_request_firm(self.request)
        return TimeEntry.objects.filter(project__firm=firm).select_related('project', 'task', 'user', 'invoice')
