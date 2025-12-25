"""
Firm Module API Views.

Provides endpoints for firm-level operations and break-glass session management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from modules.firm.models import Firm, BreakGlassSession
from modules.firm.utils import get_active_break_glass_session


class BreakGlassStatusViewSet(viewsets.ViewSet):
    """
    API endpoint for checking break-glass impersonation status.

    This provides a dedicated endpoint for frontend UI components to:
    1. Check if the current request is in break-glass mode
    2. Get impersonation session details for displaying banners
    3. Monitor session expiration

    TIER 0.6: Impersonation mode indicator requirement.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='status')
    def get_status(self, request):
        """
        Get current break-glass impersonation status.

        Returns:
            {
                "is_impersonating": bool,
                "session": {
                    "id": int,
                    "impersonated_user": str,
                    "operator": str,
                    "reason": str,
                    "activated_at": str,
                    "expires_at": str,
                    "time_remaining_seconds": int
                } | null
            }
        """
        # Check if user is a platform operator
        if not hasattr(request.user, 'platform_profile'):
            return Response({
                'is_impersonating': False,
                'session': None
            })

        # Check if user has an active break-glass session
        if not hasattr(request, 'firm') or request.firm is None:
            return Response({
                'is_impersonating': False,
                'session': None
            })

        session = get_active_break_glass_session(request.firm)

        if not session or session.operator_id != request.user.id:
            return Response({
                'is_impersonating': False,
                'session': None
            })

        # Calculate time remaining
        now = timezone.now()
        time_remaining = (session.expires_at - now).total_seconds()

        impersonated_user = session.impersonated_user
        session_data = {
            'id': session.id,
            'impersonated_user': (
                impersonated_user.get_full_name() or
                impersonated_user.email or
                impersonated_user.username
                if impersonated_user else None
            ),
            'operator': request.user.email,
            'reason': session.reason,
            'activated_at': session.activated_at.isoformat(),
            'expires_at': session.expires_at.isoformat(),
            'time_remaining_seconds': max(0, int(time_remaining))
        }

        return Response({
            'is_impersonating': True,
            'session': session_data
        })

    @action(detail=False, methods=['post'], url_path='end-session')
    def end_session(self, request):
        """
        End the current break-glass session early.

        Requires:
            reason: str - Reason for ending the session

        Returns:
            {"success": true, "message": str}
        """
        reason = request.data.get('reason', '')
        if not reason:
            return Response(
                {'error': 'Reason is required to end break-glass session'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for active session
        if not hasattr(request, 'firm') or request.firm is None:
            return Response(
                {'error': 'No firm context found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = get_active_break_glass_session(request.firm)

        if not session or session.operator_id != request.user.id:
            return Response(
                {'error': 'No active break-glass session found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Revoke the session
        session.revoke(reason)
        session.save()

        return Response({
            'success': True,
            'message': 'Break-glass session ended successfully'
        })
