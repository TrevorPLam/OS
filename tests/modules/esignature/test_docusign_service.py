"""Tests for DocuSign service."""

import base64
import hashlib
import hmac
from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from modules.esignature.docusign_service import DocuSignService
from modules.esignature.models import DocuSignConnection


pytestmark = pytest.mark.django_db


class TestDocuSignServiceInit:
    """Test DocuSignService initialization."""

    def test_init_without_connection(self):
        """Test service can be initialized without a connection."""
        service = DocuSignService()
        assert service.connection is None
        assert service.client_id is not None

    def test_init_with_connection(self, docusign_connection):
        """Test service can be initialized with a connection."""
        service = DocuSignService(connection=docusign_connection)
        assert service.connection == docusign_connection

    @patch('modules.esignature.docusign_service.settings')
    def test_init_missing_config_raises_error(self, mock_settings):
        """Test initialization fails if configuration is missing."""
        mock_settings.DOCUSIGN_CLIENT_ID = None
        mock_settings.DOCUSIGN_CLIENT_SECRET = None
        mock_settings.DOCUSIGN_REDIRECT_URI = None

        with pytest.raises(ImproperlyConfigured):
            DocuSignService()

    def test_oauth_base_url_sandbox(self):
        """Test OAuth base URL for sandbox environment."""
        with patch.object(settings, 'DOCUSIGN_ENVIRONMENT', 'sandbox'):
            service = DocuSignService()
            assert service.oauth_base_url == DocuSignService.OAUTH_BASE_URL_SANDBOX

    def test_oauth_base_url_production(self):
        """Test OAuth base URL for production environment."""
        with patch.object(settings, 'DOCUSIGN_ENVIRONMENT', 'production'):
            service = DocuSignService()
            assert service.oauth_base_url == DocuSignService.OAUTH_BASE_URL


class TestDocuSignOAuth:
    """Test OAuth 2.0 authentication methods."""

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        service = DocuSignService()
        state = "random_state_string"

        auth_url = service.get_authorization_url(state)

        assert service.oauth_base_url in auth_url
        assert "oauth/auth" in auth_url
        assert f"state={state}" in auth_url
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=signature%20impersonation" in auth_url

    @patch('modules.esignature.docusign_service.requests.post')
    def test_exchange_code_for_tokens_success(self, mock_post):
        """Test successful token exchange."""
        service = DocuSignService()

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        result = service.exchange_code_for_tokens("test_code")

        assert result["access_token"] == "test_access_token"
        assert result["refresh_token"] == "test_refresh_token"
        assert result["expires_in"] == 3600

        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "oauth/token" in call_args[0][0]
        assert call_args[1]["data"]["grant_type"] == "authorization_code"
        assert call_args[1]["data"]["code"] == "test_code"

    @patch('modules.esignature.docusign_service.requests.post')
    def test_exchange_code_for_tokens_failure(self, mock_post):
        """Test token exchange failure."""
        service = DocuSignService()

        # Mock failed response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("Invalid code")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            service.exchange_code_for_tokens("invalid_code")

    @patch('modules.esignature.docusign_service.requests.post')
    def test_refresh_access_token_success(self, mock_post):
        """Test successful token refresh."""
        service = DocuSignService()

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        result = service.refresh_access_token("test_refresh_token")

        assert result["access_token"] == "new_access_token"
        assert result["expires_in"] == 3600

        # Verify request
        call_args = mock_post.call_args
        assert call_args[1]["data"]["grant_type"] == "refresh_token"
        assert call_args[1]["data"]["refresh_token"] == "test_refresh_token"

    @patch('modules.esignature.docusign_service.requests.get')
    def test_get_user_info_success(self, mock_get):
        """Test getting user info."""
        service = DocuSignService()

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "sub": "user_id",
            "name": "Test User",
            "email": "test@example.com",
            "accounts": [
                {
                    "account_id": "test_account_id",
                    "account_name": "Test Account",
                    "base_uri": "https://demo.docusign.net",
                    "is_default": True,
                }
            ],
        }
        mock_get.return_value = mock_response

        result = service.get_user_info("test_access_token")

        assert result["sub"] == "user_id"
        assert len(result["accounts"]) == 1
        assert result["accounts"][0]["account_id"] == "test_account_id"

        # Verify authorization header
        call_args = mock_get.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_access_token"

    def test_ensure_valid_token_no_connection_raises_error(self):
        """Test ensure_valid_token fails without connection."""
        service = DocuSignService()

        with pytest.raises(ValueError, match="No DocuSign connection set"):
            service.ensure_valid_token()

    def test_ensure_valid_token_not_expired(self, docusign_connection):
        """Test ensure_valid_token returns token if not expired."""
        # Set expiration to future
        docusign_connection.token_expires_at = timezone.now() + timedelta(hours=1)
        docusign_connection.save()

        service = DocuSignService(connection=docusign_connection)
        token = service.ensure_valid_token()

        assert token == docusign_connection.access_token

    @patch('modules.esignature.docusign_service.DocuSignService.refresh_access_token')
    def test_ensure_valid_token_refreshes_if_expired(self, mock_refresh, docusign_connection):
        """Test ensure_valid_token refreshes expired token."""
        # Set expiration to past
        docusign_connection.token_expires_at = timezone.now() - timedelta(hours=1)
        docusign_connection.save()

        # Mock refresh response
        mock_refresh.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }

        service = DocuSignService(connection=docusign_connection)
        token = service.ensure_valid_token()

        assert token == "new_access_token"
        mock_refresh.assert_called_once_with(docusign_connection.refresh_token)

        # Verify connection was updated
        docusign_connection.refresh_from_db()
        assert docusign_connection.access_token == "new_access_token"


class TestDocuSignEnvelopeManagement:
    """Test envelope management methods."""

    @patch('modules.esignature.docusign_service.DocuSignService.ensure_valid_token')
    @patch('modules.esignature.docusign_service.requests.post')
    def test_create_envelope_success(self, mock_post, mock_ensure_token, docusign_connection):
        """Test successful envelope creation."""
        mock_ensure_token.return_value = "test_access_token"

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "envelopeId": "test_envelope_id",
            "status": "sent",
            "uri": "/envelopes/test_envelope_id",
        }
        mock_post.return_value = mock_response

        service = DocuSignService(connection=docusign_connection)

        result = service.create_envelope(
            document_base64="base64_content",
            document_name="test.pdf",
            recipients=[
                {"email": "signer@example.com", "name": "Test Signer", "recipient_id": 1}
            ],
            email_subject="Please sign",
            email_message="Please sign this document",
        )

        assert result["envelopeId"] == "test_envelope_id"
        assert result["status"] == "sent"

        # Verify request
        call_args = mock_post.call_args
        assert docusign_connection.base_uri in call_args[0][0]
        assert "envelopes" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_access_token"
        assert call_args[1]["json"]["emailSubject"] == "Please sign"

    @patch('modules.esignature.docusign_service.DocuSignService.ensure_valid_token')
    @patch('modules.esignature.docusign_service.requests.get')
    def test_get_envelope_status_success(self, mock_get, mock_ensure_token, docusign_connection):
        """Test getting envelope status."""
        mock_ensure_token.return_value = "test_access_token"

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "envelopeId": "test_envelope_id",
            "status": "completed",
            "completedDateTime": "2024-01-01T12:00:00Z",
        }
        mock_get.return_value = mock_response

        service = DocuSignService(connection=docusign_connection)
        result = service.get_envelope_status("test_envelope_id")

        assert result["status"] == "completed"
        assert "envelopeId" in result

    @patch('modules.esignature.docusign_service.DocuSignService.ensure_valid_token')
    @patch('modules.esignature.docusign_service.requests.post')
    def test_get_recipient_view_url_success(self, mock_post, mock_ensure_token, docusign_connection):
        """Test getting embedded signing URL."""
        mock_ensure_token.return_value = "test_access_token"

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "url": "https://demo.docusign.net/Signing/MTRedeem/v1?slt=test_token",
        }
        mock_post.return_value = mock_response

        service = DocuSignService(connection=docusign_connection)
        result = service.get_recipient_view_url(
            envelope_id="test_envelope_id",
            recipient_email="signer@example.com",
            recipient_name="Test Signer",
            return_url="https://example.com/return",
        )

        assert "url" in result
        assert "docusign.net" in result["url"]

    @patch('modules.esignature.docusign_service.DocuSignService.ensure_valid_token')
    @patch('modules.esignature.docusign_service.requests.put')
    def test_void_envelope_success(self, mock_put, mock_ensure_token, docusign_connection):
        """Test voiding an envelope."""
        mock_ensure_token.return_value = "test_access_token"

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "envelopeId": "test_envelope_id",
            "status": "voided",
            "voidedReason": "User request",
        }
        mock_put.return_value = mock_response

        service = DocuSignService(connection=docusign_connection)
        result = service.void_envelope("test_envelope_id", "User request")

        assert result["status"] == "voided"

        # Verify request
        call_args = mock_put.call_args
        assert call_args[1]["json"]["status"] == "voided"
        assert call_args[1]["json"]["voidedReason"] == "User request"


class TestDocuSignWebhooks:
    """Test webhook handling methods."""

    def test_verify_webhook_signature_valid(self):
        """Test webhook signature verification with valid signature."""
        payload = b'{"test": "data"}'
        secret = "test_secret"

        # Compute expected signature
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(computed_sig).decode("utf-8")

        is_valid = DocuSignService.verify_webhook_signature(payload, signature, secret)

        assert is_valid is True

    def test_verify_webhook_signature_invalid(self):
        """Test webhook signature verification with invalid signature."""
        payload = b'{"test": "data"}'
        secret = "test_secret"
        invalid_signature = "invalid_signature"

        is_valid = DocuSignService.verify_webhook_signature(payload, invalid_signature, secret)

        assert is_valid is False

    def test_verify_webhook_signature_no_secret(self):
        """Test webhook signature verification with no secret configured."""
        payload = b'{"test": "data"}'

        # Should return True (skip verification) if no secret
        is_valid = DocuSignService.verify_webhook_signature(payload, "any_sig", None)

        assert is_valid is True

    def test_parse_webhook_payload_json(self):
        """Test parsing JSON webhook payload."""
        json_payload = '{"envelopeId": "test_id", "status": "completed"}'

        result = DocuSignService.parse_webhook_payload(json_payload)

        assert result["envelopeId"] == "test_id"
        assert result["status"] == "completed"

    def test_parse_webhook_payload_xml(self):
        """Test parsing XML webhook payload (legacy)."""
        xml_payload = '<?xml version="1.0"?><root><test>data</test></root>'

        result = DocuSignService.parse_webhook_payload(xml_payload)

        # Should return dict with raw_xml key for unsupported XML
        assert "raw_xml" in result
        assert xml_payload in result["raw_xml"]
