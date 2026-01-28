"""
Snippets Module Views.

Provides API endpoints for snippet management and usage.
Implements HubSpot-style text snippets with shortcuts and variables.
"""

from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.query_guards import QueryTimeoutMixin
from modules.auth.role_permissions import IsStaffUser
from modules.firm.utils import FirmScopedMixin

from .models import Snippet, SnippetUsageLog, SnippetFolder
from .serializers import (
    SnippetSerializer,
    SnippetUsageLogSerializer,
    SnippetFolderSerializer,
    SnippetRenderSerializer,
    SnippetUseSerializer,
)


class SnippetViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Snippet management.

    Snippets are reusable text blocks with shortcuts and variables.
    Staff can create personal snippets or share them with team.
    """

    model = Snippet
    serializer_class = SnippetSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['is_shared', 'is_active', 'context', 'folder', 'created_by']
    search_fields = ['shortcut', 'name', 'content']
    ordering_fields = ['shortcut', 'name', 'usage_count', 'created_at']
    ordering = ['shortcut']

    def get_queryset(self):
        """
        Filter snippets by firm context and user permissions.

        Users can see:
        - Their own personal snippets (is_shared=False, created_by=user)
        - Team-wide shared snippets (is_shared=True)
        """
        queryset = super().get_queryset()

        user = self.request.user

        # Filter to snippets the user can access
        queryset = queryset.filter(
            Q(created_by=user, is_shared=False) |  # Personal snippets
            Q(is_shared=True)  # Team snippets
        )

        return queryset.select_related('created_by', 'folder')

    def perform_create(self, serializer):
        """Create snippet with firm and creator."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        """
        Render snippet with variables.

        Replaces variables in snippet content with provided values.

        Request body:
            {
                "context_data": {
                    "contact_name": "John Doe",
                    "my_name": "Jane Smith",
                    "company_name": "Acme Corp"
                }
            }

        Response:
            {
                "rendered_content": "...",
                "original_content": "...",
                "variables_replaced": ["contact_name", "my_name"]
            }
        """
        snippet = self.get_object()
        serializer = SnippetRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        context_data = serializer.validated_data.get('context_data', {})

        # Render snippet
        rendered_content = snippet.render(context_data)

        # Track which variables were replaced
        variables_replaced = [
            var for var in snippet.extract_variables()
            if var in context_data
        ]

        return Response({
            'rendered_content': rendered_content,
            'original_content': snippet.content,
            'variables_replaced': variables_replaced,
            'available_variables': snippet.get_available_variables(),
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """
        Log snippet usage and increment counter.

        Records when and where snippet was used for analytics.

        Request body:
            {
                "context": "email",
                "context_object_type": "ticket",
                "context_object_id": "123",
                "variables_used": {"contact_name": "John Doe"}
            }

        Response:
            {
                "message": "Snippet usage logged",
                "snippet": {...},
                "usage_count": 42
            }
        """
        snippet = self.get_object()
        serializer = SnippetUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Log usage
        usage_log = SnippetUsageLog.objects.create(
            snippet=snippet,
            used_by=request.user,
            context=serializer.validated_data.get('context', 'unknown'),
            context_object_type=serializer.validated_data.get('context_object_type', ''),
            context_object_id=serializer.validated_data.get('context_object_id', ''),
            variables_used=serializer.validated_data.get('variables_used', {}),
            rendered_length=len(snippet.content),
        )

        # Increment usage counter
        snippet.increment_usage()

        return Response({
            'message': 'Snippet usage logged',
            'snippet': SnippetSerializer(snippet).data,
            'usage_count': snippet.usage_count,
            'usage_log_id': usage_log.id,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search snippets by shortcut or name.

        Query parameters:
            - q: Search query (searches shortcut and name)
            - context: Filter by context (email, ticket, message, note)

        Response: List of matching snippets
        """
        queryset = self.get_queryset()

        # Search query
        query = request.query_params.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(shortcut__icontains=query) |
                Q(name__icontains=query)
            )

        # Context filter
        context = request.query_params.get('context', '')
        if context:
            queryset = queryset.filter(
                Q(context=context) | Q(context='all')
            )

        # Only active snippets
        queryset = queryset.filter(is_active=True)

        # Order by usage
        queryset = queryset.order_by('-usage_count', 'shortcut')

        # Limit results
        queryset = queryset[:20]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def my_snippets(self, request):
        """
        Get current user's personal snippets.

        Returns only snippets created by the current user that are not shared.

        Response: List of personal snippets
        """
        queryset = self.get_queryset().filter(
            created_by=request.user,
            is_shared=False
        ).order_by('-usage_count', 'shortcut')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def team_snippets(self, request):
        """
        Get shared team snippets.

        Returns snippets that are shared with the team.

        Response: List of team snippets
        """
        queryset = self.get_queryset().filter(
            is_shared=True
        ).order_by('-usage_count', 'shortcut')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SnippetUsageLogViewSet(QueryTimeoutMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for SnippetUsageLog (read-only).

    Usage logs are created automatically when snippets are used.
    Provides analytics on snippet usage patterns.
    """

    queryset = SnippetUsageLog.objects.all()
    serializer_class = SnippetUsageLogSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['snippet', 'used_by', 'context', 'context_object_type']
    ordering_fields = ['used_at']
    ordering = ['-used_at']

    def get_queryset(self):
        """Filter by firm context through snippet relationship."""
        queryset = super().get_queryset()

        # Filter to logs for snippets in user's firm
        queryset = queryset.filter(snippet__firm=self.request.firm)

        return queryset.select_related('snippet', 'used_by')


class SnippetFolderViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SnippetFolder management.

    Folders help organize snippets into categories.
    """

    model = SnippetFolder
    serializer_class = SnippetFolderSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['is_shared', 'created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """
        Filter folders by firm context and user permissions.

        Users can see:
        - Their own personal folders (is_shared=False, created_by=user)
        - Team-wide shared folders (is_shared=True)
        """
        queryset = super().get_queryset()

        user = self.request.user

        # Filter to folders the user can access
        queryset = queryset.filter(
            Q(created_by=user, is_shared=False) |  # Personal folders
            Q(is_shared=True)  # Team folders
        )

        return queryset.select_related('created_by')

    def perform_create(self, serializer):
        """Create folder with firm and creator."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )
