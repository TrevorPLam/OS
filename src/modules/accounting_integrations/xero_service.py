"""
Xero Accounting Integration Service.

Provides OAuth authentication, invoice sync, payment sync, and contact operations
using Xero Accounting API.

API Documentation: https://developer.xero.com/documentation/api/accounting/overview
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class XeroService:
    """
    Service for Xero Accounting integration.

    Handles OAuth flow, token refresh, and accounting operations
    using Xero Accounting API.

    Environment variables:
    - XERO_CLIENT_ID
    - XERO_CLIENT_SECRET
    - XERO_REDIRECT_URI
    """

    API_VERSION = '2.0'
    SCOPES = [
        'accounting.transactions',
        'accounting.contacts',
        'accounting.settings',
    ]

    def __init__(self):
        """Initialize Xero service with credentials."""
        self.client_id = os.getenv('XERO_CLIENT_ID')
        self.client_secret = os.getenv('XERO_CLIENT_SECRET')
        self.redirect_uri = os.getenv('XERO_REDIRECT_URI')
        self.base_url = 'https://api.xero.com/api.xro/2.0'
        self.auth_url = 'https://login.xero.com/identity/connect/authorize'
        self.token_url = 'https://identity.xero.com/connect/token'

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning(
                "Xero credentials not configured. "
                "Set XERO_CLIENT_ID, XERO_CLIENT_SECRET, "
                "and XERO_REDIRECT_URI."
            )

    def get_authorization_url(self, state_token: str) -> str:
        """
        Get OAuth authorization URL.

        Args:
            state_token: CSRF protection token

        Returns:
            Authorization URL to redirect user to
        """
        from urllib.parse import urlencode

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.SCOPES),
            'state': state_token,
        }

        return f"{self.auth_url}?{urlencode(params)}"

    def authenticate(self, authorization_code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: OAuth authorization code

        Returns:
            Dict containing:
                - success (bool): Whether authentication succeeded
                - access_token (str): Access token
                - refresh_token (str): Refresh token
                - expires_in (int): Token expiration in seconds
                - error (str): Error message if failed
        """
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            data = {
                'code': authorization_code,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code',
            }

            auth = HTTPBasicAuth(self.client_id, self.client_secret)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(
                self.token_url,
                data=data,
                auth=auth,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_in': token_data.get('expires_in', 1800),
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error_description', response.text)
                logger.error(f"Xero OAuth error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            logger.exception(f"Xero authentication error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            Dict containing new tokens or error
        """
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            data = {
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            }

            auth = HTTPBasicAuth(self.client_id, self.client_secret)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(
                self.token_url,
                data=data,
                auth=auth,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_in': token_data.get('expires_in', 1800),
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error_description', response.text)
                logger.error(f"Xero token refresh error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            logger.exception(f"Xero token refresh error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_connections(self, access_token: str) -> Dict:
        """
        Get list of Xero tenant connections.

        Args:
            access_token: OAuth access token

        Returns:
            List of tenant connections or error
        """
        try:
            import requests

            url = 'https://api.xero.com/connections'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                error_msg = response.text
                logger.error(f"Xero connections error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            logger.exception(f"Xero connections error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _make_request(self, method: str, endpoint: str, access_token: str,
                      tenant_id: str, data: Optional[Dict] = None) -> Dict:
        """
        Make authenticated API request to Xero.

        Args:
            method: HTTP method (GET, POST, PUT)
            endpoint: API endpoint path
            access_token: OAuth access token
            tenant_id: Xero tenant ID
            data: Optional request body data

        Returns:
            Response data or error
        """
        try:
            import requests

            url = f"{self.base_url}/{endpoint}"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Xero-Tenant-Id': tenant_id,
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('Message', response.text)
                logger.error(f"Xero API error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            logger.exception(f"Xero API request error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_contact(self, access_token: str, tenant_id: str, contact_data: Dict) -> Dict:
        """
        Create a contact in Xero.

        Args:
            access_token: OAuth access token
            tenant_id: Xero tenant ID
            contact_data: Contact data (Name, EmailAddress, etc.)

        Returns:
            Created contact data or error
        """
        payload = {'Contacts': [contact_data]}
        return self._make_request('POST', 'Contacts', access_token, tenant_id, payload)

    def update_contact(self, access_token: str, tenant_id: str, contact_id: str, contact_data: Dict) -> Dict:
        """
        Update a contact in Xero.

        Args:
            access_token: OAuth access token
            tenant_id: Xero tenant ID
            contact_id: Xero contact ID
            contact_data: Updated contact data

        Returns:
            Updated contact data or error
        """
        contact_data['ContactID'] = contact_id
        payload = {'Contacts': [contact_data]}
        return self._make_request('POST', f'Contacts/{contact_id}', access_token, tenant_id, payload)

    def get_contact(self, access_token: str, tenant_id: str, contact_id: str) -> Dict:
        """
        Get contact details from Xero.

        Args:
            access_token: OAuth access token
            tenant_id: Xero tenant ID
            contact_id: Xero contact ID

        Returns:
            Contact data or error
        """
        return self._make_request('GET', f'Contacts/{contact_id}', access_token, tenant_id)

    def create_invoice(self, access_token: str, tenant_id: str, invoice_data: Dict) -> Dict:
        """
        Create an invoice in Xero.

        Args:
            access_token: OAuth access token
            tenant_id: Xero tenant ID
            invoice_data: Invoice data (Contact, LineItems, etc.)

        Returns:
            Created invoice data or error
        """
        payload = {'Invoices': [invoice_data]}
        return self._make_request('POST', 'Invoices', access_token, tenant_id, payload)

    def get_invoice(self, access_token: str, tenant_id: str, invoice_id: str) -> Dict:
        """
        Get invoice details from Xero.

        Args:
            access_token: OAuth access token
            tenant_id: Xero tenant ID
            invoice_id: Xero invoice ID

        Returns:
            Invoice data or error
        """
        return self._make_request('GET', f'Invoices/{invoice_id}', access_token, tenant_id)

    def get_payments(self, access_token: str, tenant_id: str, modified_since: Optional[datetime] = None) -> Dict:
        """
        Get payments from Xero.

        Args:
            access_token: OAuth access token
            tenant_id: Xero tenant ID
            modified_since: Optional filter for payments modified since date

        Returns:
            List of payments or error
        """
        endpoint = 'Payments'
        if modified_since:
            # Xero uses If-Modified-Since header
            # For simplicity, we'll use query parameter
            endpoint += f'?where=UpdatedDateUTC>=DateTime({modified_since.year},{modified_since.month},{modified_since.day})'

        return self._make_request('GET', endpoint, access_token, tenant_id)

    def get_payment(self, access_token: str, tenant_id: str, payment_id: str) -> Dict:
        """
        Get payment details from Xero.

        Args:
            access_token: OAuth access token
            tenant_id: Xero tenant ID
            payment_id: Xero payment ID

        Returns:
            Payment data or error
        """
        return self._make_request('GET', f'Payments/{payment_id}', access_token, tenant_id)
