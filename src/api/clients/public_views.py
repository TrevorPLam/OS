"""
Public email consent endpoints (no authentication required).

Provides confirmation and unsubscribe endpoints for email compliance workflows.
"""

from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from modules.clients.models import EmailOptInRequest, EmailUnsubscribeToken


class PublicOptInConfirmViewSet(viewsets.ViewSet):
    """Confirm double opt-in requests via public token."""

    permission_classes = [AllowAny]

    def retrieve(self, request, pk=None):
        opt_in_request = EmailOptInRequest.objects.filter(token=pk).select_related("contact").first()
        if not opt_in_request:
            return Response({"error": "Invalid confirmation token"}, status=status.HTTP_404_NOT_FOUND)

        if opt_in_request.is_confirmed:
            return Response({"status": "already_confirmed"}, status=status.HTTP_200_OK)

        if opt_in_request.is_expired:
            return Response({"error": "Confirmation link expired"}, status=status.HTTP_410_GONE)

        confirmed = opt_in_request.confirm(
            actor=None,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        if not confirmed:
            return Response({"error": "Unable to confirm opt-in"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "confirmed"}, status=status.HTTP_200_OK)


class PublicUnsubscribeViewSet(viewsets.ViewSet):
    """Unsubscribe from email communications via public token."""

    permission_classes = [AllowAny]

    def retrieve(self, request, pk=None):
        token = EmailUnsubscribeToken.objects.filter(token=pk).select_related("contact").first()
        if not token:
            return Response({"error": "Invalid unsubscribe token"}, status=status.HTTP_404_NOT_FOUND)

        if token.is_used:
            return Response({"status": "already_unsubscribed"}, status=status.HTTP_200_OK)

        success = token.mark_unsubscribed(
            actor=None,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        if not success:
            return Response({"error": "Unable to unsubscribe"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "unsubscribed"}, status=status.HTTP_200_OK)
