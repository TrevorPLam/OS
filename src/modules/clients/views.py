"""
API Views for Clients module.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from modules.clients.models import (
    Client,
    ClientPortalUser,
    ClientNote,
    ClientEngagement,
    ClientComment
)
from modules.clients.serializers import (
    ClientSerializer,
    ClientPortalUserSerializer,
    ClientNoteSerializer,
    ClientEngagementSerializer,
    ClientCommentSerializer,
    ClientProjectSerializer,
)


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client management (Post-sale).

    Provides CRUD operations for clients that have been converted from prospects.
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'account_manager', 'portal_enabled']
    search_fields = ['company_name', 'primary_contact_name', 'primary_contact_email']
    ordering_fields = ['company_name', 'client_since', 'total_lifetime_value']
    ordering = ['-client_since']

    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        """
        Get comprehensive client overview.

        Returns client details plus related projects, invoices, and engagements.
        """
        client = self.get_object()
        serializer = self.get_serializer(client)

        # Get related data counts
        overview_data = {
            **serializer.data,
            'projects_count': client.projects.count(),
            'active_projects': client.projects.filter(status='in_progress').count(),
            'invoices_count': client.invoices.count(),
            'outstanding_invoices': client.invoices.filter(status__in=['sent', 'partial', 'overdue']).count(),
            'engagements_count': client.engagements.count(),
            'portal_users_count': client.portal_users.count(),
        }

        return Response(overview_data)

    @action(detail=True, methods=['post'])
    def enable_portal(self, request, pk=None):
        """Enable client portal access for this client."""
        client = self.get_object()
        client.portal_enabled = True
        client.save()
        return Response({'status': 'portal enabled', 'client': ClientSerializer(client).data})

    @action(detail=True, methods=['post'])
    def disable_portal(self, request, pk=None):
        """Disable client portal access for this client."""
        client = self.get_object()
        client.portal_enabled = False
        client.save()
        return Response({'status': 'portal disabled', 'client': ClientSerializer(client).data})


class ClientPortalUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Portal User management.

    Manages client-side users with portal access.
    """
    queryset = ClientPortalUser.objects.all()
    serializer_class = ClientPortalUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['client', 'role']
    search_fields = ['user__username', 'user__email', 'client__company_name']

    def perform_create(self, serializer):
        """Set invited_by to current user."""
        serializer.save(invited_by=self.request.user)


class ClientNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Notes (internal only).

    Notes are NOT visible to clients - for internal team use only.
    """
    queryset = ClientNote.objects.all()
    serializer_class = ClientNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['client', 'author', 'is_pinned']
    search_fields = ['note', 'client__company_name']

    def get_queryset(self):
        """Optionally filter by client_id query param."""
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client_id')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset


class ClientEngagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Engagements.

    Tracks all contracts/engagements with version history.
    """
    queryset = ClientEngagement.objects.all()
    serializer_class = ClientEngagementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'status']
    ordering_fields = ['start_date', 'version', 'contracted_value']
    ordering = ['-start_date']

    @action(detail=False, methods=['get'])
    def by_client(self, request):
        """Get all engagements for a specific client."""
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response({'error': 'client_id query parameter required'}, status=400)

        engagements = self.queryset.filter(client_id=client_id)
        serializer = self.get_serializer(engagements, many=True)
        return Response(serializer.data)


class ClientProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Projects (read-only).

    Shows projects for the authenticated client portal user.
    Clients can view their projects and tasks, but cannot modify them.
    """
    serializer_class = ClientProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['name', 'start_date', 'end_date']
    ordering = ['-start_date']

    def get_queryset(self):
        """
        Filter projects by authenticated client portal user's client.

        Only returns projects for the client that the portal user belongs to.
        """
        from modules.projects.models import Project

        user = self.request.user

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)

            # Check if user has permission to view projects
            if not portal_user.can_view_projects:
                return Project.objects.none()

            # Return projects for this client
            return Project.objects.filter(client=portal_user.client).prefetch_related('tasks_set')

        except ClientPortalUser.DoesNotExist:
            # Not a client portal user - check if firm user
            # Firm users can view all projects (handled by permissions)
            return Project.objects.all()

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """
        Get all tasks for a specific project.

        Returns tasks with client comments.
        """
        project = self.get_object()
        from modules.projects.models import Task
        from modules.clients.serializers import ClientTaskSerializer

        tasks = Task.objects.filter(project=project).order_by('position', '-created_at')
        serializer = ClientTaskSerializer(tasks, many=True)
        return Response(serializer.data)


class ClientCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Comments on Tasks.

    Allows client portal users to comment on tasks in their projects.
    Comments are visible to both firm team and client.
    """
    queryset = ClientComment.objects.all()
    serializer_class = ClientCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task', 'client', 'is_read_by_firm']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter comments based on user type.

        - Client portal users: only see comments for their client
        - Firm users: see all comments
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)
            # Filter to only this client's comments
            queryset = queryset.filter(client=portal_user.client)
        except ClientPortalUser.DoesNotExist:
            # Firm user - can see all comments
            pass

        # Filter by task_id if provided in query params
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset

    def perform_create(self, serializer):
        """
        Create comment with automatic client detection.

        The serializer handles setting author and client from request context.
        """
        serializer.save()

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a client comment as read by firm team.

        Only accessible to firm users (not client portal users).
        """
        comment = self.get_object()

        # Check if user is a firm user (not a client portal user)
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
            return Response(
                {'error': 'Only firm team members can mark comments as read'},
                status=403
            )
        except ClientPortalUser.DoesNotExist:
            # Firm user - can mark as read
            from django.utils import timezone
            comment.is_read_by_firm = True
            comment.read_by = request.user
            comment.read_at = timezone.now()
            comment.save()

            return Response({
                'status': 'marked as read',
                'comment': ClientCommentSerializer(comment).data
            })

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get all unread client comments.

        Only accessible to firm users.
        """
        # Check if user is a firm user
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
            return Response(
                {'error': 'Only firm team members can access this endpoint'},
                status=403
            )
        except ClientPortalUser.DoesNotExist:
            # Firm user - get unread comments
            unread_comments = self.queryset.filter(is_read_by_firm=False)
            serializer = self.get_serializer(unread_comments, many=True)
            return Response(serializer.data)
