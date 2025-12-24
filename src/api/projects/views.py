"""
DRF ViewSets for Projects module.
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from modules.projects.models import Project, Task, TimeEntry
from modules.firm.viewsets import FirmScopedViewSetMixin
from .serializers import ProjectSerializer, TaskSerializer, TimeEntrySerializer


class ProjectViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for Project model."""
    queryset = Project.objects.select_related('client', 'contract', 'project_manager')
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'status', 'billing_type', 'project_manager']
    search_fields = ['project_code', 'name', 'client__company_name']
    ordering_fields = ['project_code', 'created_at', 'start_date']
    ordering = ['-created_at']


class TaskViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for Task model."""
    queryset = Task.objects.select_related('project', 'assigned_to')
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'priority', 'assigned_to']
    search_fields = ['title', 'description', 'project__name']
    ordering_fields = ['position', 'created_at', 'due_date']
    ordering = ['position', '-created_at']


class TimeEntryViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for TimeEntry model."""
    queryset = TimeEntry.objects.select_related('project', 'task', 'user', 'invoice')
    serializer_class = TimeEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'user', 'task', 'is_billable', 'invoiced', 'date']
    search_fields = ['description', 'project__name', 'user__username']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date', '-created_at']
