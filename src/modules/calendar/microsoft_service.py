"""
Microsoft Calendar Integration Service.

Provides OAuth authentication, event sync, and calendar operations
using Microsoft Graph API (for Outlook/Office 365).
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


class MicrosoftCalendarService:
    """
    Service for Microsoft Outlook/Office 365 calendar integration.

    Handles OAuth flow, token refresh, and calendar event operations
    using Microsoft Graph API.

    Environment variables:
    - MICROSOFT_CALENDAR_CLIENT_ID
    - MICROSOFT_CALENDAR_CLIENT_SECRET
    - MICROSOFT_CALENDAR_REDIRECT_URI
    """

    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    SCOPES = [
        'Calendars.ReadWrite',
        'Calendars.ReadWrite.Shared',
        'offline_access',
    ]

    def __init__(self):
        """Initialize Microsoft Calendar service with credentials."""
        self.client_id = os.getenv('MICROSOFT_CALENDAR_CLIENT_ID')
        self.client_secret = os.getenv('MICROSOFT_CALENDAR_CLIENT_SECRET')
        self.redirect_uri = os.getenv('MICROSOFT_CALENDAR_REDIRECT_URI')

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning(
                "Microsoft Calendar credentials not configured. "
                "Set MICROSOFT_CALENDAR_CLIENT_ID, MICROSOFT_CALENDAR_CLIENT_SECRET, "
                "and MICROSOFT_CALENDAR_REDIRECT_URI."
            )

    def get_authorization_url(self, state_token: str) -> str:
        """Get OAuth authorization URL."""
        from urllib.parse import urlencode

        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'response_mode': 'query',
            'scope': ' '.join(self.SCOPES),
            'state': state_token,
        }

        base_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
        return f"{base_url}?{urlencode(params)}"

    def authenticate(self, authorization_code: str) -> Dict:
        """Exchange authorization code for tokens."""
        try:
            import requests

            token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code',
            }

            response = requests.post(token_url, data=data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data.get('refresh_token', ''),
                    'expires_in': token_data.get('expires_in', 3600),
                    'scope': token_data.get('scope', ''),
                }
            else:
                error_data = response.json()
                logger.error(f"Microsoft OAuth failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error_description', 'Authentication failed')
                }

        except Exception as e:
            logger.error(f"Error authenticating with Microsoft: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh expired access token."""
        try:
            import requests

            token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            }

            response = requests.post(token_url, data=data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data['access_token'],
                    'expires_in': token_data.get('expires_in', 3600),
                }
            else:
                error_data = response.json()
                logger.error(f"Microsoft token refresh failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error_description', 'Token refresh failed')
                }

        except Exception as e:
            logger.error(f"Error refreshing Microsoft token: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def sync_events(
        self,
        access_token: str,
        sync_window_days: int = 30,
        delta_link: Optional[str] = None
    ) -> Dict:
        """Sync events from Microsoft Calendar."""
        try:
            import requests

            if delta_link:
                url = delta_link
            else:
                now = timezone.now()
                start_dt = (now - timedelta(days=sync_window_days)).strftime('%Y-%m-%dT%H:%M:%S')
                end_dt = (now + timedelta(days=sync_window_days)).strftime('%Y-%m-%dT%H:%M:%S')

                url = (
                    f'{self.GRAPH_API_ENDPOINT}/me/calendarView/delta'
                    f'?startDateTime={start_dt}&endDateTime={end_dt}'
                )

            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'events': data.get('value', []),
                    'next_delta_link': data.get('@odata.deltaLink', ''),
                }
            else:
                error_data = response.json()
                logger.error(f"Microsoft Calendar sync failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Sync failed'),
                    'events': [],
                }

        except Exception as e:
            logger.error(f"Error syncing Microsoft Calendar: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'events': []}

    def create_event(self, access_token: str, event_data: Dict) -> Dict:
        """Create event in Microsoft Calendar."""
        try:
            import requests

            url = f'{self.GRAPH_API_ENDPOINT}/me/calendar/events'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.post(url, headers=headers, json=event_data, timeout=10)

            if response.status_code == 201:
                event = response.json()
                return {'success': True, 'event_id': event['id'], 'event': event}
            else:
                error_data = response.json()
                logger.error(f"Microsoft event creation failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Creation failed')
                }

        except Exception as e:
            logger.error(f"Error creating Microsoft event: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def update_event(self, access_token: str, event_id: str, event_data: Dict) -> Dict:
        """Update event in Microsoft Calendar."""
        try:
            import requests

            url = f'{self.GRAPH_API_ENDPOINT}/me/calendar/events/{event_id}'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.patch(url, headers=headers, json=event_data, timeout=10)

            if response.status_code == 200:
                event = response.json()
                return {'success': True, 'event': event}
            else:
                error_data = response.json()
                logger.error(f"Microsoft event update failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Update failed')
                }

        except Exception as e:
            logger.error(f"Error updating Microsoft event: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def delete_event(self, access_token: str, event_id: str) -> Dict:
        """Delete event from Microsoft Calendar."""
        try:
            import requests

            url = f'{self.GRAPH_API_ENDPOINT}/me/calendar/events/{event_id}'
            headers = {'Authorization': f'Bearer {access_token}'}

            response = requests.delete(url, headers=headers, timeout=10)

            if response.status_code == 204:
                return {'success': True}
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"Microsoft event deletion failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Deletion failed')
                }

        except Exception as e:
            logger.error(f"Error deleting Microsoft event: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def send_invitation(
        self,
        access_token: str,
        event_data: Dict,
        attendees: List[str]
    ) -> Dict:
        """Create event with attendees."""
        event_data['attendees'] = [
            {'emailAddress': {'address': email}, 'type': 'required'}
            for email in attendees
        ]
        return self.create_event(access_token, event_data)
