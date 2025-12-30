"""
Calendar OAuth Views.

Provides API endpoints for OAuth connection management and calendar sync.
"""

import logging
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from modules.auth.role_permissions import IsStaffUser
from modules.firm.utils import FirmScopedMixin

from .oauth_models import OAuthConnection, OAuthAuthorizationCode
from .oauth_serializers import (
    OAuthConnectionSerializer,
    OAuthInitiateSerializer,
    OAuthCallbackSerializer,
    CalendarSyncStatusSerializer,
)
from .google_service import GoogleCalendarService
from .microsoft_service import MicrosoftCalendarService
from .sync_service import CalendarSyncService

logger = logging.getLogger(__name__)


class OAuthConnectionViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for OAuth connection management.

    Staff users can manage their own calendar connections.
    Provides OAuth flow initiation, callback handling, and sync control.
    """

    model = OAuthConnection
    serializer_class = OAuthConnectionSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['provider', 'status', 'sync_enabled']
    ordering_fields = ['created_at', 'last_sync_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter to user's own connections."""
        queryset = super().get_queryset()
        # Staff users can only see their own connections
        return queryset.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def initiate_google_oauth(self, request):
        """
        Initiate Google Calendar OAuth flow.

        Creates authorization code record and returns OAuth URL.
        """
        return self._initiate_oauth(request, 'google')

    @action(detail=False, methods=['post'])
    def initiate_microsoft_oauth(self, request):
        """
        Initiate Microsoft Calendar OAuth flow.

        Creates authorization code record and returns OAuth URL.
        """
        return self._initiate_oauth(request, 'microsoft')

    def _initiate_oauth(self, request, provider: str):
        """
        Internal method to initiate OAuth flow.

        Args:
            request: Request object
            provider: Provider name ('google' or 'microsoft')

        Returns:
            Response with authorization URL
        """
        # Check if connection already exists
        existing = OAuthConnection.objects.filter(
            firm=request.firm,
            user=request.user,
            provider=provider,
        ).first()

        if existing and existing.status == 'active':
            return Response(
                {'error': f'{provider.title()} calendar already connected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create authorization code record
        with transaction.atomic():
            auth_code = OAuthAuthorizationCode.objects.create(
                firm=request.firm,
                user=request.user,
                provider=provider,
                redirect_uri=request.build_absolute_uri('/api/calendar/oauth/callback/'),
            )

            # Get authorization URL from service
            if provider == 'google':
                service = GoogleCalendarService()
            elif provider == 'microsoft':
                service = MicrosoftCalendarService()
            else:
                return Response(
                    {'error': 'Unsupported provider'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            auth_url = service.get_authorization_url(str(auth_code.state_token))

        logger.info(
            f"Initiated {provider} OAuth for user {request.user.id}, "
            f"state={auth_code.state_token}"
        )

        return Response({
            'authorization_url': auth_url,
            'state': str(auth_code.state_token),
            'provider': provider,
        })

    @action(detail=False, methods=['post', 'get'])
    def oauth_callback(self, request):
        """
        Handle OAuth callback from provider.

        Exchanges authorization code for tokens and creates connection.
        """
        # Support both POST and GET (providers use GET redirects)
        data = request.data if request.method == 'POST' else request.query_params

        serializer = OAuthCallbackSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        state_token = serializer.validated_data['state']

        # Find authorization code record
        try:
            auth_code = OAuthAuthorizationCode.objects.get(
                state_token=state_token,
                state='pending',
            )
        except OAuthAuthorizationCode.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired authorization'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check expiration
        if auth_code.is_expired():
            auth_code.state = 'expired'
            auth_code.save(update_fields=['state'])
            return Response(
                {'error': 'Authorization code expired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Exchange code for tokens
        if auth_code.provider == 'google':
            service = GoogleCalendarService()
        elif auth_code.provider == 'microsoft':
            service = MicrosoftCalendarService()
        else:
            return Response(
                {'error': 'Unsupported provider'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = service.authenticate(code)

        if not result['success']:
            auth_code.state = 'error'
            auth_code.error_message = result.get('error', 'Authentication failed')
            auth_code.save(update_fields=['state', 'error_message'])

            return Response(
                {'error': result.get('error', 'Authentication failed')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update connection
        with transaction.atomic():
            connection, created = OAuthConnection.objects.update_or_create(
                firm=auth_code.firm,
                user=auth_code.user,
                provider=auth_code.provider,
                defaults={
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token', ''),
                    'token_expires_at': timezone.now() + timedelta(
                        seconds=result.get('expires_in', 3600)
                    ),
                    'scopes': result.get('scope', '').split(),
                    'status': 'active',
                    'sync_enabled': True,
                }
            )

            # Update authorization code
            auth_code.state = 'exchanged'
            auth_code.authorization_code = code
            auth_code.connection = connection
            auth_code.exchanged_at = timezone.now()
            auth_code.save(update_fields=[
                'state',
                'authorization_code',
                'connection',
                'exchanged_at',
            ])

        logger.info(
            f"{'Created' if created else 'Updated'} {auth_code.provider} "
            f"connection for user {auth_code.user.id}"
        )

        return Response({
            'message': 'Calendar connected successfully',
            'connection': OAuthConnectionSerializer(connection).data,
        })

    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """
        Revoke OAuth connection.

        Marks connection as revoked and disables sync.
        """
        connection = self.get_object()

        connection.status = 'revoked'
        connection.sync_enabled = False
        connection.save(update_fields=['status', 'sync_enabled'])

        logger.info(
            f"Disconnected {connection.provider} calendar for user {connection.user.id}"
        )

        return Response({
            'message': 'Calendar disconnected successfully',
            'connection': OAuthConnectionSerializer(connection).data,
        })

    @action(detail=True, methods=['post'])
    def sync_now(self, request, pk=None):
        """
        Trigger manual calendar sync.

        Performs bi-directional sync immediately.
        """
        connection = self.get_object()

        if not connection.sync_enabled:
            return Response(
                {'error': 'Sync is not enabled for this connection'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if connection.status != 'active':
            return Response(
                {'error': f'Connection status is {connection.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Perform sync
        sync_service = CalendarSyncService()
        result = sync_service.perform_sync(connection)

        if result['success']:
            return Response({
                'message': 'Sync completed successfully',
                'pulled': result.get('pulled', 0),
                'pushed': result.get('pushed', 0),
                'last_sync_at': connection.last_sync_at,
            })
        else:
            return Response(
                {
                    'error': result.get('error', 'Sync failed'),
                    'errors': result.get('errors', []),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def sync_status(self, request, pk=None):
        """
        Get current sync status for connection.

        Returns connection details and last sync information.
        """
        connection = self.get_object()

        return Response({
            'connection': OAuthConnectionSerializer(connection).data,
            'last_sync_at': connection.last_sync_at,
            'sync_enabled': connection.sync_enabled,
            'status': connection.status,
            'error_message': connection.error_message,
            'is_token_expired': connection.is_token_expired(),
            'needs_refresh': connection.needs_refresh(),
        })
