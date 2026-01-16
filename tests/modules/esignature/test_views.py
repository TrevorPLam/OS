"""Tests for e-signature API views."""

import base64
import hashlib
import hmac
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from modules.esignature.models import DocuSignConnection, Envelope, WebhookEvent
from tests.utils.query_budget import assert_max_queries


pytestmark = pytest.mark.django_db


class TestDocuSignConnectionViewSet:
    """Test DocuSign connection API endpoints."""

    def test_list_connections_authenticated(self, user, docusign_connection):
        """Test listing connections for authenticated user."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("docusign-connection-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["account_id"] == docusign_connection.account_id

    def test_list_connections_unauthenticated(self):
        """Test listing connections requires authentication."""
        client = APIClient()
        url = reverse("docusign-connection-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_connection(self, user, docusign_connection):
        """Test retrieving a single connection."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("docusign-connection-detail", kwargs={"pk": docusign_connection.pk})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["account_id"] == docusign_connection.account_id

    def test_disconnect_connection(self, user, docusign_connection):
        """Test disconnecting a DocuSign connection."""
        client = APIClient()
        client.force_authenticate(user=user)

        assert docusign_connection.is_active is True

        url = reverse("docusign-connection-disconnect", kwargs={"pk": docusign_connection.pk})
        response = client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify connection was deactivated
        docusign_connection.refresh_from_db()
        assert docusign_connection.is_active is False


class TestEnvelopeViewSet:
    """Test Envelope API endpoints."""

    @pytest.mark.performance
    def test_list_envelopes_authenticated(self, user, envelope):
        """Test listing envelopes for authenticated user."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("envelope-list")
        # Query budget guard for the envelope list endpoint.
        with assert_max_queries(12):
            response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_envelope(self, user, envelope):
        """Test retrieving a single envelope."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("envelope-detail", kwargs={"pk": envelope.pk})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["envelope_id"] == envelope.envelope_id

    @patch('modules.esignature.views.DocuSignService')
    def test_void_envelope_success(self, mock_service_class, user, envelope):
        """Test voiding an envelope."""
        # Mock the service
        mock_service = Mock()
        mock_service.void_envelope.return_value = {"status": "voided"}
        mock_service_class.return_value = mock_service

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("envelope-void", kwargs={"pk": envelope.pk})
        response = client.post(url, {"reason": "User requested"})

        assert response.status_code == status.HTTP_200_OK
        assert "voided successfully" in response.data["message"]

        # Verify envelope was updated
        envelope.refresh_from_db()
        assert envelope.status == "voided"
        assert envelope.voided_reason == "User requested"

    def test_void_completed_envelope_fails(self, user, envelope):
        """Test cannot void a completed envelope."""
        envelope.status = "completed"
        envelope.save()

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("envelope-void", kwargs={"pk": envelope.pk})
        response = client.post(url, {"reason": "Test"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot void" in response.data["error"]


class TestOAuthFlow:
    """Test DocuSign OAuth flow endpoints."""

    @patch('modules.esignature.views.DocuSignService')
    def test_docusign_connect(self, mock_service_class, user):
        """Test initiating DocuSign OAuth flow."""
        # Mock the service
        mock_service = Mock()
        mock_service.get_authorization_url.return_value = "https://account.docusign.com/oauth/auth?..."
        mock_service_class.return_value = mock_service

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("docusign-connect")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "authorization_url" in response.data
        assert "state" in response.data

    def test_docusign_connect_unauthenticated(self):
        """Test OAuth flow requires authentication."""
        client = APIClient()
        url = reverse("docusign-connect")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('modules.esignature.views.DocuSignService')
    def test_docusign_callback_success(self, mock_service_class, user):
        """Test successful OAuth callback."""
        # Mock the service
        mock_service = Mock()
        mock_service.exchange_code_for_tokens.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        mock_service.get_user_info.return_value = {
            "accounts": [
                {
                    "account_id": "test_account",
                    "account_name": "Test Account",
                    "base_uri": "https://demo.docusign.net",
                }
            ]
        }
        mock_service_class.return_value = mock_service

        client = APIClient()
        client.force_authenticate(user=user)

        # Set state in session
        session = client.session
        session["docusign_oauth_state"] = "test_state"
        session.save()

        url = reverse("docusign-callback")
        response = client.get(url, {"code": "test_code", "state": "test_state"})

        assert response.status_code == status.HTTP_200_OK
        assert "connection" in response.data

        # Verify connection was created
        assert DocuSignConnection.objects.filter(firm=user.firm).exists()

    def test_docusign_callback_invalid_state(self, user):
        """Test OAuth callback with invalid state fails."""
        client = APIClient()
        client.force_authenticate(user=user)

        # Set different state in session
        session = client.session
        session["docusign_oauth_state"] = "valid_state"
        session.save()

        url = reverse("docusign-callback")
        response = client.get(url, {"code": "test_code", "state": "invalid_state"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid state" in response.data["error"]

    def test_docusign_callback_oauth_error(self, user):
        """Test OAuth callback with error parameter."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("docusign-callback")
        response = client.get(url, {"error": "access_denied", "error_description": "User denied access"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "access_denied" in response.data["error"]


class TestDocuSignWebhook:
    """Test DocuSign webhook endpoint."""

    def test_webhook_valid_signature(self, envelope):
        """Test webhook with valid signature."""
        payload = {
            "event": "envelope-completed",
            "envelopeId": envelope.envelope_id,
            "status": "completed",
            "data": {
                "envelopeSummary": {
                    "status": "completed",
                }
            }
        }
        payload_str = str(payload)
        payload_bytes = payload_str.encode("utf-8")

        # Compute signature
        secret = "test_secret"
        signature = base64.b64encode(
            hmac.new(
                secret.encode("utf-8"),
                payload_bytes,
                hashlib.sha256
            ).digest()
        ).decode("utf-8")

        client = APIClient()
        url = reverse("docusign-webhook")

        with patch('modules.esignature.views.settings.DOCUSIGN_WEBHOOK_SECRET', secret):
            with patch('modules.esignature.views.DocuSignService.parse_webhook_payload', return_value=payload):
                response = client.post(
                    url,
                    payload_str,
                    content_type="application/json",
                    HTTP_X_DOCUSIGN_SIGNATURE_1=signature,
                )

        assert response.status_code == status.HTTP_200_OK

        # Verify webhook event was created
        assert WebhookEvent.objects.filter(envelope_id=envelope.envelope_id).exists()

    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature."""
        payload = {"test": "data"}

        client = APIClient()
        url = reverse("docusign-webhook")

        with patch('modules.esignature.views.settings.DOCUSIGN_WEBHOOK_SECRET', "test_secret"):
            response = client.post(
                url,
                payload,
                content_type="application/json",
                HTTP_X_DOCUSIGN_SIGNATURE_1="invalid_signature",
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_webhook_updates_envelope_status(self, envelope):
        """Test webhook updates envelope status."""
        payload = {
            "event": "envelope-completed",
            "envelopeId": envelope.envelope_id,
            "status": "completed",
        }

        client = APIClient()
        url = reverse("docusign-webhook")

        # No signature verification if no secret
        with patch('modules.esignature.views.settings.DOCUSIGN_WEBHOOK_SECRET', None):
            with patch('modules.esignature.views.DocuSignService.parse_webhook_payload', return_value=payload):
                response = client.post(
                    url,
                    str(payload),
                    content_type="application/json",
                )

        assert response.status_code == status.HTTP_200_OK

        # Verify envelope status was updated
        envelope.refresh_from_db()
        assert envelope.status == "completed"
        assert envelope.completed_at is not None

    def test_webhook_unknown_envelope(self):
        """Test webhook for unknown envelope."""
        payload = {
            "event": "envelope-sent",
            "envelopeId": "unknown_envelope_id",
            "status": "sent",
        }

        client = APIClient()
        url = reverse("docusign-webhook")

        with patch('modules.esignature.views.settings.DOCUSIGN_WEBHOOK_SECRET', None):
            with patch('modules.esignature.views.DocuSignService.parse_webhook_payload', return_value=payload):
                response = client.post(
                    url,
                    str(payload),
                    content_type="application/json",
                )

        # Should still succeed but log warning
        assert response.status_code == status.HTTP_200_OK

        # Event should be created without linked envelope
        event = WebhookEvent.objects.filter(envelope_id="unknown_envelope_id").first()
        assert event is not None
        assert event.envelope is None
