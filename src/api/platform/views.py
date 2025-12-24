"""
Platform API Views (TIER 0.6).

API endpoints for platform operators and break-glass operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from modules.firm.models import BreakGlassSession, AuditEvent, Firm
from modules.firm.permissions import IsBreakGlassOperator, IsPlatformStaff
from .serializers import (
    BreakGlassActivationSerializer,
    BreakGlassSessionSerializer,
    BreakGlassRevocationSerializer,
    AuditEventSerializer
)


User = get_user_model()


class BreakGlassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for break-glass session management (TIER 0.6).
    
    Only break-glass operators can activate and manage sessions.
    All operations are logged immutably.
    """
    serializer_class = BreakGlassSessionSerializer
    permission_classes = [IsAuthenticated, IsBreakGlassOperator]
    
    def get_queryset(self):
        """Return break-glass sessions for the operator."""
        return BreakGlassSession.objects.filter(
            operator=self.request.user
        ).select_related('firm', 'operator', 'impersonated_user')
    
    @action(detail=False, methods=['post'])
    def activate(self, request):
        """
        Activate a new break-glass session.
        
        POST /api/platform/break-glass/activate/
        {
            "firm_id": 123,
            "reason": "Emergency support for ticket #1234...",
            "duration_hours": 4,
            "impersonated_user_id": 456  // optional
        }
        """
        serializer = BreakGlassActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get firm with exception handling for race conditions
        try:
            firm = Firm.objects.get(id=serializer.validated_data['firm_id'])
        except Firm.DoesNotExist:
            return Response(
                {'error': 'Firm not found or was deleted'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        duration_hours = serializer.validated_data.get('duration_hours', 4)
        impersonated_user_id = serializer.validated_data.get('impersonated_user_id')
        
        # Check if user already has active session for this firm
        existing_active = BreakGlassSession.objects.active().filter(
            operator=request.user,
            firm=firm
        )
        
        if existing_active.exists():
            return Response(
                {
                    'error': 'Active break-glass session already exists for this firm',
                    'session_id': existing_active.first().id
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get impersonated user if specified
        impersonated_user = None
        if impersonated_user_id:
            try:
                impersonated_user = User.objects.get(id=impersonated_user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Impersonated user not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create session
        session = BreakGlassSession.objects.create(
            firm=firm,
            operator=request.user,
            impersonated_user=impersonated_user,
            reason=serializer.validated_data['reason'],
            expires_at=timezone.now() + timedelta(hours=duration_hours)
        )
        
        # Signal will automatically log the activation
        
        response_serializer = BreakGlassSessionSerializer(session)
        return Response(
            {
                'message': 'Break-glass session activated',
                'session': response_serializer.data,
                'warning': 'All actions during this session are logged and auditable'
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """
        Revoke a break-glass session early.
        
        POST /api/platform/break-glass/{id}/revoke/
        {
            "reason": "Support completed early"
        }
        """
        session = self.get_object()
        
        # Can only revoke own active sessions
        if session.operator != request.user:
            return Response(
                {'error': 'Can only revoke your own sessions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if session.status != BreakGlassSession.STATUS_ACTIVE:
            return Response(
                {'error': 'Session is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = BreakGlassRevocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Revoke session
        session.revoke(serializer.validated_data['reason'])
        session.save()
        
        # Signal will automatically log the revocation
        
        response_serializer = BreakGlassSessionSerializer(session)
        return Response(
            {
                'message': 'Break-glass session revoked',
                'session': response_serializer.data
            }
        )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active break-glass sessions for the operator.
        
        GET /api/platform/break-glass/active/
        """
        active_sessions = self.get_queryset().filter(
            status=BreakGlassSession.STATUS_ACTIVE
        ).exclude(
            expires_at__lte=timezone.now()
        )
        
        serializer = self.get_serializer(active_sessions, many=True)
        return Response({
            'count': active_sessions.count(),
            'sessions': serializer.data
        })


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit events (TIER 0.6).
    
    Platform staff can view audit events for security review.
    All events are immutable - no create/update/delete.
    """
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated, IsPlatformStaff]
    
    def get_queryset(self):
        """
        Return audit events with filtering.
        
        Platform operators can view all audit events.
        """
        queryset = AuditEvent.objects.select_related('firm', 'actor')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by firm
        firm_id = self.request.query_params.get('firm_id')
        if firm_id:
            queryset = queryset.filter(firm_id=firm_id)
        
        # Filter by date range
        since = self.request.query_params.get('since')
        if since:
            queryset = queryset.filter(timestamp__gte=since)
        
        return queryset.order_by('-timestamp')
