"""
QuickBooks Online Integration Service.

Provides OAuth authentication, invoice sync, payment sync, and customer operations
using QuickBooks Online API (Intuit API).

API Documentation: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/invoice
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class QuickBooksService:
    """
    Service for QuickBooks Online integration.

    Handles OAuth flow, token refresh, and accounting operations
    using QuickBooks Online API.

    Environment variables:
    - QUICKBOOKS_CLIENT_ID
    - QUICKBOOKS_CLIENT_SECRET
    - QUICKBOOKS_REDIRECT_URI
    - QUICKBOOKS_ENVIRONMENT (sandbox or production)
    """

    API_VERSION = 'v3'
    SCOPES = [
        'com.intuit.quickbooks.accounting',
    ]

    def __init__(self, environment='production'):
        """Initialize QuickBooks service with credentials."""
        self.client_id = os.getenv('QUICKBOOKS_CLIENT_ID')
        self.client_secret = os.getenv('QUICKBOOKS_CLIENT_SECRET')
        self.redirect_uri = os.getenv('QUICKBOOKS_REDIRECT_URI')
        self.environment = os.getenv('QUICKBOOKS_ENVIRONMENT', environment)

        # Set base URL based on environment
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox-quickbooks.api.intuit.com'
            self.auth_url = 'https://appcenter.intuit.com/connect/oauth2'
        else:
            self.base_url = 'https://quickbooks.api.intuit.com'
            self.auth_url = 'https://appcenter.intuit.com/connect/oauth2'

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning(
                "QuickBooks credentials not configured. "
                "Set QUICKBOOKS_CLIENT_ID, QUICKBOOKS_CLIENT_SECRET, "
                "and QUICKBOOKS_REDIRECT_URI."
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
                - realm_id (str): QuickBooks company ID
                - error (str): Error message if failed
        """
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'

            data = {
                'code': authorization_code,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code',
            }

            auth = HTTPBasicAuth(self.client_id, self.client_secret)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(
                token_url,
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
                    'expires_in': token_data.get('expires_in', 3600),
                    'realm_id': token_data.get('realmId', ''),  # Company ID
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error_description', response.text)
                logger.error(f"QuickBooks OAuth error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            logger.exception(f"QuickBooks authentication error: {e}")
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

            token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'

            data = {
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            }

            auth = HTTPBasicAuth(self.client_id, self.client_secret)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(
                token_url,
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
                    'expires_in': token_data.get('expires_in', 3600),
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error_description', response.text)
                logger.error(f"QuickBooks token refresh error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            logger.exception(f"QuickBooks token refresh error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _make_request(self, method: str, endpoint: str, access_token: str,
                      realm_id: str, data: Optional[Dict] = None) -> Dict:
        """
        Make authenticated API request to QuickBooks.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            access_token: OAuth access token
            realm_id: QuickBooks company ID
            data: Optional request body data

        Returns:
            Response data or error
        """
        try:
            import requests

            url = f"{self.base_url}/{self.API_VERSION}/company/{realm_id}/{endpoint}"
            headers = {
                'Authorization': f'Bearer {access_token}',
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
                error_msg = error_data.get('Fault', {}).get('Error', [{}])[0].get('Message', response.text)
                logger.error(f"QuickBooks API error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            logger.exception(f"QuickBooks API request error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_customer(self, access_token: str, realm_id: str, customer_data: Dict) -> Dict:
        """
        Create a customer in QuickBooks.

        Args:
            access_token: OAuth access token
            realm_id: QuickBooks company ID
            customer_data: Customer data (DisplayName, PrimaryEmailAddr, etc.)

        Returns:
            Created customer data or error
        """
        return self._make_request('POST', 'customer', access_token, realm_id, customer_data)

    def update_customer(self, access_token: str, realm_id: str, customer_id: str, customer_data: Dict) -> Dict:
        """
        Update a customer in QuickBooks.

        Args:
            access_token: OAuth access token
            realm_id: QuickBooks company ID
            customer_id: QuickBooks customer ID
            customer_data: Updated customer data

        Returns:
            Updated customer data or error
        """
        # Need to fetch current version first for SyncToken
        current = self._make_request('GET', f'customer/{customer_id}', access_token, realm_id)
        if not current.get('success'):
            return current

        customer_data['SyncToken'] = current['data']['Customer']['SyncToken']
        customer_data['Id'] = customer_id

        return self._make_request('POST', 'customer', access_token, realm_id, customer_data)

    def get_customer(self, access_token: str, realm_id: str, customer_id: str) -> Dict:
        """
        Get customer details from QuickBooks.

        Args:
            access_token: OAuth access token
            realm_id: QuickBooks company ID
            customer_id: QuickBooks customer ID

        Returns:
            Customer data or error
        """
        return self._make_request('GET', f'customer/{customer_id}', access_token, realm_id)

    def create_invoice(self, access_token: str, realm_id: str, invoice_data: Dict) -> Dict:
        """
        Create an invoice in QuickBooks.

        Args:
            access_token: OAuth access token
            realm_id: QuickBooks company ID
            invoice_data: Invoice data (CustomerRef, Line items, etc.)

        Returns:
            Created invoice data or error
        """
        return self._make_request('POST', 'invoice', access_token, realm_id, invoice_data)

    def get_invoice(self, access_token: str, realm_id: str, invoice_id: str) -> Dict:
        """
        Get invoice details from QuickBooks.

        Args:
            access_token: OAuth access token
            realm_id: QuickBooks company ID
            invoice_id: QuickBooks invoice ID

        Returns:
            Invoice data or error
        """
        return self._make_request('GET', f'invoice/{invoice_id}', access_token, realm_id)

    def query_payments(self, access_token: str, realm_id: str, start_date: Optional[datetime] = None) -> Dict:
        """
        Query payments from QuickBooks.

        Args:
            access_token: OAuth access token
            realm_id: QuickBooks company ID
            start_date: Optional start date to filter payments

        Returns:
            List of payments or error
        """
        query = "SELECT * FROM Payment"
        if start_date:
            query += f" WHERE MetaData.LastUpdatedTime >= '{start_date.strftime('%Y-%m-%d')}'"
        query += " MAXRESULTS 1000"

        endpoint = f'query?query={query}'
        return self._make_request('GET', endpoint, access_token, realm_id)

    def get_payment(self, access_token: str, realm_id: str, payment_id: str) -> Dict:
        """
        Get payment details from QuickBooks.

        Args:
            access_token: OAuth access token
            realm_id: QuickBooks company ID
            payment_id: QuickBooks payment ID

        Returns:
            Payment data or error
        """
        return self._make_request('GET', f'payment/{payment_id}', access_token, realm_id)
