"""DocuSign API service for OAuth authentication and envelope management."""

import base64
import hashlib
import hmac
import json
import logging
from datetime import timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from modules.esignature.models import DocuSignConnection, Envelope

logger = logging.getLogger(__name__)


class DocuSignService:
    """
    Service for interacting with DocuSign eSignature API.

    Meta-commentary:
    - **Current Status:** Webhook signature verification is optional when `DOCUSIGN_WEBHOOK_SECRET` is unset, leaving Connect callbacks unauthenticated in some deployments.
    - **Follow-up (T-067):** Add retry/backoff with idempotency keys for envelope create/send calls so transient network errors don't produce duplicate envelopes.
    - **Assumption:** Connection tokens are refreshed externally when `DocuSignConnection` is shared; `ensure_valid_token` only updates the bound connection instance and does not refresh per-request when no connection is provided.
    - **Limitation:** Envelope status reconciliation is one-way; there is no periodic audit to detect missing webhook events or reconcile completed envelopes back to source records.
    """
    
    # DocuSign OAuth and API endpoints
    OAUTH_BASE_URL = "https://account.docusign.com"
    OAUTH_BASE_URL_SANDBOX = "https://account-d.docusign.com"
    
    def __init__(self, connection: Optional[DocuSignConnection] = None):
        """
        Initialize DocuSign service.
        
        Args:
            connection: Existing DocuSign connection (optional)
        """
        self.connection = connection
        
        # Get configuration from settings
        self.client_id = getattr(settings, "DOCUSIGN_CLIENT_ID", None)
        self.client_secret = getattr(settings, "DOCUSIGN_CLIENT_SECRET", None)
        self.redirect_uri = getattr(settings, "DOCUSIGN_REDIRECT_URI", None)
        self.webhook_secret = getattr(settings, "DOCUSIGN_WEBHOOK_SECRET", None)
        self.environment = getattr(settings, "DOCUSIGN_ENVIRONMENT", "production")
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ImproperlyConfigured(
                "DocuSign configuration incomplete. Set DOCUSIGN_CLIENT_ID, "
                "DOCUSIGN_CLIENT_SECRET, and DOCUSIGN_REDIRECT_URI."
            )
        
        self.oauth_base_url = (
            self.OAUTH_BASE_URL_SANDBOX if self.environment == "sandbox" 
            else self.OAUTH_BASE_URL
        )
    
    # ==================== OAuth 2.0 Authentication ====================
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate DocuSign OAuth authorization URL.
        
        Args:
            state: Random state string for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "response_type": "code",
            "scope": "signature impersonation",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        
        return f"{self.oauth_base_url}/oauth/auth?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dictionary with access_token, refresh_token, expires_in, etc.
            
        Raises:
            requests.HTTPError: If token exchange fails
        """
        url = f"{self.oauth_base_url}/oauth/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        auth = (self.client_id, self.client_secret)
        
        response = requests.post(url, data=data, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: OAuth refresh token
            
        Returns:
            Dictionary with new access_token, expires_in, etc.
            
        Raises:
            requests.HTTPError: If token refresh fails
        """
        url = f"{self.oauth_base_url}/oauth/token"
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        auth = (self.client_id, self.client_secret)
        
        response = requests.post(url, data=data, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Get DocuSign user information using access token.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            Dictionary with user info including account_id, account_name, base_uri
            
        Raises:
            requests.HTTPError: If user info request fails
        """
        url = f"{self.oauth_base_url}/oauth/userinfo"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def ensure_valid_token(self) -> str:
        """
        Ensure connection has valid access token, refreshing if necessary.
        
        Returns:
            Valid access token
            
        Raises:
            ValueError: If no connection is set
        """
        if not self.connection:
            raise ValueError("No DocuSign connection set")
        
        # Check if token is expired or will expire in next 5 minutes
        if self.connection.is_token_expired() or (
            timezone.now() >= self.connection.token_expires_at - timedelta(minutes=5)
        ):
            # Refresh token
            token_data = self.refresh_access_token(self.connection.refresh_token)
            
            # Update connection
            self.connection.access_token = token_data["access_token"]
            self.connection.token_expires_at = timezone.now() + timedelta(
                seconds=token_data["expires_in"]
            )
            self.connection.save(update_fields=["access_token", "token_expires_at", "updated_at"])
            
            logger.info(f"Refreshed DocuSign access token for firm {self.connection.firm_id}")
        
        return self.connection.access_token
    
    # ==================== Envelope Management ====================
    
    def create_envelope(
        self,
        document_base64: str,
        document_name: str,
        recipients: List[Dict],
        email_subject: str,
        email_message: str = "",
        status: str = "sent",
    ) -> Dict:
        """
        Create and optionally send a DocuSign envelope.
        
        Args:
            document_base64: Base64-encoded document content
            document_name: Name of the document
            recipients: List of recipient dictionaries with email, name, recipient_id
            email_subject: Email subject for envelope
            email_message: Email message body (optional)
            status: Envelope status - "created" (draft) or "sent" (send immediately)
            
        Returns:
            Dictionary with envelope_id, status, uri, etc.
            
        Raises:
            requests.HTTPError: If envelope creation fails
        """
        access_token = self.ensure_valid_token()
        
        url = f"{self.connection.base_uri}/restapi/v2.1/accounts/{self.connection.account_id}/envelopes"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        # Build envelope definition
        envelope_definition = {
            "emailSubject": email_subject,
            "emailBlurb": email_message,
            "status": status,
            "documents": [
                {
                    "documentBase64": document_base64,
                    "name": document_name,
                    "fileExtension": "pdf",
                    "documentId": "1",
                }
            ],
            "recipients": {
                "signers": [
                    {
                        "email": recipient["email"],
                        "name": recipient["name"],
                        "recipientId": str(recipient["recipient_id"]),
                        "routingOrder": str(recipient.get("routing_order", 1)),
                        "tabs": {
                            "signHereTabs": [
                                {
                                    "anchorString": "/sn1/",
                                    "anchorUnits": "pixels",
                                    "anchorXOffset": "20",
                                    "anchorYOffset": "10",
                                }
                            ]
                        },
                    }
                    for recipient in recipients
                ]
            },
        }
        
        response = requests.post(url, headers=headers, json=envelope_definition)
        response.raise_for_status()
        
        return response.json()
    
    def get_envelope_status(self, envelope_id: str) -> Dict:
        """
        Get current status of an envelope.
        
        Args:
            envelope_id: DocuSign envelope ID
            
        Returns:
            Dictionary with envelope status information
            
        Raises:
            requests.HTTPError: If status request fails
        """
        access_token = self.ensure_valid_token()
        
        url = f"{self.connection.base_uri}/restapi/v2.1/accounts/{self.connection.account_id}/envelopes/{envelope_id}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_recipient_view_url(
        self,
        envelope_id: str,
        recipient_email: str,
        recipient_name: str,
        return_url: str,
    ) -> Dict:
        """
        Get embedded signing URL for a recipient.
        
        Args:
            envelope_id: DocuSign envelope ID
            recipient_email: Email of the signer
            recipient_name: Name of the signer
            return_url: URL to redirect to after signing
            
        Returns:
            Dictionary with 'url' key containing the signing URL
            
        Raises:
            requests.HTTPError: If view request fails
        """
        access_token = self.ensure_valid_token()
        
        url = f"{self.connection.base_uri}/restapi/v2.1/accounts/{self.connection.account_id}/envelopes/{envelope_id}/views/recipient"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        data = {
            "returnUrl": return_url,
            "authenticationMethod": "none",
            "email": recipient_email,
            "userName": recipient_name,
            "clientUserId": recipient_email,  # Use email as client user ID
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def void_envelope(self, envelope_id: str, reason: str) -> Dict:
        """
        Void an envelope (cancel it).
        
        Args:
            envelope_id: DocuSign envelope ID
            reason: Reason for voiding
            
        Returns:
            Dictionary with updated envelope information
            
        Raises:
            requests.HTTPError: If void request fails
        """
        access_token = self.ensure_valid_token()
        
        url = f"{self.connection.base_uri}/restapi/v2.1/accounts/{self.connection.account_id}/envelopes/{envelope_id}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        data = {
            "status": "voided",
            "voidedReason": reason,
        }
        
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    # ==================== Webhook Handling ====================
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify DocuSign webhook HMAC signature.
        
        Args:
            payload: Raw webhook payload bytes
            signature: HMAC signature from X-DocuSign-Signature-1 header
            secret: Webhook secret key
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        # Compute HMAC-SHA256
        computed_signature = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).digest()
        
        # Base64 encode
        computed_signature_b64 = base64.b64encode(computed_signature).decode("utf-8")
        
        return hmac.compare_digest(computed_signature_b64, signature)
    
    @staticmethod
    def parse_webhook_payload(payload: str) -> Dict:
        """
        Parse DocuSign webhook payload.
        
        Args:
            payload: Webhook payload string (XML or JSON)
            
        Returns:
            Parsed payload as dictionary
        """
        # Try parsing as JSON first (newer webhooks)
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            # If JSON parsing fails, it might be XML (legacy webhooks)
            # For now, we'll just store it as-is and log a warning
            logger.warning("Received XML webhook payload, JSON parsing recommended")
            return {"raw_xml": payload}
