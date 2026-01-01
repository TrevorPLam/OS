"""API views for e-signature integrations."""

import base64
import logging
import secrets
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.clients.models import Proposal
from modules.esignature.docusign_service import DocuSignService
from modules.esignature.models import DocuSignConnection, Envelope, WebhookEvent
from modules.esignature.serializers import (
    DocuSignConnectionSerializer,
    EnvelopeSerializer,
    WebhookEventSerializer,
)
from permissions import IsFirmUser

logger = logging.getLogger(__name__)


class DocuSignConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for DocuSign connection management.
    
    Provides read-only access to connection information.
    Connection creation/deletion handled by OAuth flow.
    """
    
    serializer_class = DocuSignConnectionSerializer
    permission_classes = [IsAuthenticated, IsFirmUser]
    
    def get_queryset(self):
        """Return connections for user's firm."""
        return DocuSignConnection.objects.filter(firm=self.request.user.firm)
    
    @action(detail=True, methods=["post"])
    def disconnect(self, request, pk=None):
        """Disconnect (deactivate) a DocuSign connection."""
        connection = self.get_object()
        connection.is_active = False
        connection.save(update_fields=["is_active", "updated_at"])
        
        return Response(
            {"message": "DocuSign connection disconnected successfully"},
            status=status.HTTP_200_OK
        )


class EnvelopeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for envelope information.
    
    Provides read-only access to envelope status and details.
    Envelope creation handled by proposal/contract workflows.
    """
    
    serializer_class = EnvelopeSerializer
    permission_classes = [IsAuthenticated, IsFirmUser]
    
    def get_queryset(self):
        """Return envelopes for user's firm."""
        return Envelope.objects.filter(firm=self.request.user.firm).select_related(
            "firm", "connection", "proposal", "contract"
        )
    
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """Void an envelope."""
        envelope = self.get_object()
        reason = request.data.get("reason", "Voided by user")
        
        # Check if envelope can be voided
        if envelope.status in ["completed", "voided", "declined"]:
            return Response(
                {"error": f"Cannot void envelope with status: {envelope.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Void via DocuSign API
            service = DocuSignService(connection=envelope.connection)
            service.void_envelope(envelope.envelope_id, reason)
            
            # Update local envelope
            envelope.status = "voided"
            envelope.voided_at = timezone.now()
            envelope.voided_reason = reason
            envelope.save(update_fields=["status", "voided_at", "voided_reason", "updated_at"])
            
            return Response(
                {"message": "Envelope voided successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Failed to void envelope {envelope.envelope_id}: {str(e)}")
            return Response(
                {"error": f"Failed to void envelope: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for webhook event logs.
    
    Provides read-only access to webhook events for debugging.
    """
    
    serializer_class = WebhookEventSerializer
    permission_classes = [IsAuthenticated, IsFirmUser]
    
    def get_queryset(self):
        """Return webhook events for user's firm envelopes."""
        return WebhookEvent.objects.filter(
            envelope__firm=self.request.user.firm
        ).select_related("envelope")


# ==================== OAuth Flow Endpoints ====================

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFirmUser])
def docusign_connect(request):
    """
    Initiate DocuSign OAuth flow.
    
    Returns authorization URL for user to visit.
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in session
    request.session["docusign_oauth_state"] = state
    
    # Get authorization URL
    service = DocuSignService()
    auth_url = service.get_authorization_url(state)
    
    return Response({
        "authorization_url": auth_url,
        "state": state,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFirmUser])
def docusign_callback(request):
    """
    Handle DocuSign OAuth callback.
    
    Exchanges authorization code for tokens and stores connection.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    
    # Check for OAuth error
    if error:
        logger.error(f"DocuSign OAuth error: {error}")
        return Response(
            {"error": f"DocuSign authorization failed: {error}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify state for CSRF protection
    stored_state = request.session.get("docusign_oauth_state")
    if not state or state != stored_state:
        return Response(
            {"error": "Invalid state parameter (CSRF protection)"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Clear state from session
    request.session.pop("docusign_oauth_state", None)
    
    try:
        # Exchange code for tokens
        service = DocuSignService()
        token_data = service.exchange_code_for_tokens(code)
        
        # Get user info (account details)
        user_info = service.get_user_info(token_data["access_token"])
        
        # Extract account info (use first account)
        account = user_info["accounts"][0]
        
        # Calculate token expiration
        token_expires_at = timezone.now() + timezone.timedelta(seconds=token_data["expires_in"])
        
        # Create or update connection
        connection, created = DocuSignConnection.objects.update_or_create(
            firm=request.user.firm,
            defaults={
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expires_at": token_expires_at,
                "account_id": account["account_id"],
                "account_name": account["account_name"],
                "base_uri": account["base_uri"],
                "is_active": True,
                "connected_by": request.user,
            }
        )
        
        action = "created" if created else "updated"
        logger.info(f"DocuSign connection {action} for firm {request.user.firm.id}")
        
        return Response({
            "message": f"DocuSign connection {action} successfully",
            "connection": DocuSignConnectionSerializer(connection).data,
        })
        
    except Exception as e:
        logger.error(f"DocuSign OAuth callback error: {str(e)}")
        return Response(
            {"error": f"Failed to complete DocuSign connection: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== Webhook Endpoint ====================

@csrf_exempt
@api_view(["POST"])
@permission_classes([])  # No authentication for webhooks (verified by HMAC)
def docusign_webhook(request):
    """
    Handle DocuSign webhook callbacks.
    
    Processes envelope status updates and stores events.
    """
    try:
        # Get webhook signature for verification
        signature = request.META.get("HTTP_X_DOCUSIGN_SIGNATURE_1", "")
        
        # Get raw payload
        payload_bytes = request.body
        
        # Verify webhook signature
        webhook_secret = getattr(settings, "DOCUSIGN_WEBHOOK_SECRET", None)
        if webhook_secret:
            is_valid = DocuSignService.verify_webhook_signature(
                payload_bytes, signature, webhook_secret
            )
            if not is_valid:
                logger.warning("Invalid DocuSign webhook signature")
                return HttpResponse(status=401)
        
        # Parse payload
        payload_str = payload_bytes.decode("utf-8")
        payload_data = DocuSignService.parse_webhook_payload(payload_str)
        
        # Extract envelope information
        envelope_id = payload_data.get("envelopeId") or payload_data.get("data", {}).get("envelopeId")
        event_type = payload_data.get("event") or payload_data.get("eventType", "unknown")
        event_status = payload_data.get("status") or payload_data.get("data", {}).get("envelopeSummary", {}).get("status", "unknown")
        
        if not envelope_id:
            logger.warning("Webhook payload missing envelope ID")
            return HttpResponse(status=400)
        
        # Find envelope in database
        try:
            envelope = Envelope.objects.get(envelope_id=envelope_id)
        except Envelope.DoesNotExist:
            envelope = None
            logger.warning(f"Received webhook for unknown envelope: {envelope_id}")
        
        # Create webhook event log
        webhook_event = WebhookEvent.objects.create(
            envelope=envelope,
            envelope_id=envelope_id,
            event_type=event_type,
            event_status=event_status,
            payload=payload_data,
            headers={
                "signature": signature,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            },
        )
        
        # Update envelope status if found
        if envelope:
            status_map = {
                "sent": "sent",
                "delivered": "delivered",
                "signed": "signed",
                "completed": "completed",
                "declined": "declined",
                "voided": "voided",
            }
            
            new_status = status_map.get(event_status.lower())
            if new_status and new_status != envelope.status:
                envelope.status = new_status
                
                # Update timestamps based on status
                if new_status == "sent":
                    envelope.sent_at = timezone.now()
                elif new_status == "delivered":
                    envelope.delivered_at = timezone.now()
                elif new_status == "signed":
                    envelope.signed_at = timezone.now()
                elif new_status == "completed":
                    envelope.completed_at = timezone.now()
                    # Update proposal status if linked
                    if envelope.proposal:
                        envelope.proposal.status = "accepted"
                        envelope.proposal.save(update_fields=["status", "updated_at"])
                elif new_status == "voided":
                    envelope.voided_at = timezone.now()
                
                envelope.save()
                logger.info(f"Updated envelope {envelope_id} status to {new_status}")
            
            # Mark webhook event as processed
            webhook_event.processed = True
            webhook_event.processed_at = timezone.now()
            webhook_event.save(update_fields=["processed", "processed_at"])
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error processing DocuSign webhook: {str(e)}")
        return HttpResponse(status=500)
