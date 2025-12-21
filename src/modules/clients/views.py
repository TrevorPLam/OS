"""
API Views for Clients module.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from modules.clients.models import Client, ClientPortalUser, ClientNote, ClientEngagement
from modules.clients.serializers import (
    ClientSerializer,
    ClientPortalUserSerializer,
    ClientNoteSerializer,
    ClientEngagementSerializer,
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
