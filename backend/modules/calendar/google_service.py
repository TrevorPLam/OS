"""
Google Calendar Integration Service.

Provides OAuth authentication, event sync, and calendar operations
using Google Calendar API v3.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """
    Service for Google Calendar integration.

    Handles OAuth flow, token refresh, and calendar event operations
    using Google Calendar API v3.

    Environment variables:
    - GOOGLE_CALENDAR_CLIENT_ID
    - GOOGLE_CALENDAR_CLIENT_SECRET
    - GOOGLE_CALENDAR_REDIRECT_URI
    """

    API_VERSION = 'v3'
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/calendar.readonly',
    ]

    def __init__(self):
        """Initialize Google Calendar service with credentials."""
        self.client_id = os.getenv('GOOGLE_CALENDAR_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_CALENDAR_REDIRECT_URI')

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning(
                "Google Calendar credentials not configured. "
                "Set GOOGLE_CALENDAR_CLIENT_ID, GOOGLE_CALENDAR_CLIENT_SECRET, "
                "and GOOGLE_CALENDAR_REDIRECT_URI."
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
            'access_type': 'offline',  # Request refresh token
            'prompt': 'consent',  # Force consent screen for refresh token
        }

        base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        return f"{base_url}?{urlencode(params)}"

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
                - scope (str): Granted scopes
                - error (str): Error message if failed
        """
        try:
            import requests

            token_url = 'https://oauth2.googleapis.com/token'

            data = {
                'code': authorization_code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
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
                logger.error(f"Google OAuth token exchange failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error_description', 'Token exchange failed')
                }

        except Exception as e:
            logger.error(f"Error authenticating with Google: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh expired access token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            Dict containing:
                - success (bool): Whether refresh succeeded
                - access_token (str): New access token
                - expires_in (int): Token expiration in seconds
                - error (str): Error message if failed
        """
        try:
            import requests

            token_url = 'https://oauth2.googleapis.com/token'

            data = {
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
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
                logger.error(f"Google token refresh failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error_description', 'Token refresh failed')
                }

        except Exception as e:
            logger.error(f"Error refreshing Google token: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def sync_events(
        self,
        access_token: str,
        sync_window_days: int = 30,
        sync_token: Optional[str] = None
    ) -> Dict:
        """
        Sync events from Google Calendar (bi-directional).

        Args:
            access_token: OAuth access token
            sync_window_days: Number of days to sync (past and future)
            sync_token: Sync token for incremental sync

        Returns:
            Dict containing:
                - success (bool): Whether sync succeeded
                - events (List[Dict]): Event data
                - next_sync_token (str): Token for next incremental sync
                - error (str): Error message if failed
        """
        try:
            import requests

            # Use incremental sync if token provided
            if sync_token:
                url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
                params = {
                    'syncToken': sync_token,
                }
            else:
                # Full sync with time window
                url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
                now = timezone.now()
                time_min = (now - timedelta(days=sync_window_days)).isoformat()
                time_max = (now + timedelta(days=sync_window_days)).isoformat()

                params = {
                    'timeMin': time_min,
                    'timeMax': time_max,
                    'singleEvents': True,
                    'orderBy': 'startTime',
                }

            headers = {
                'Authorization': f'Bearer {access_token}',
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'events': data.get('items', []),
                    'next_sync_token': data.get('nextSyncToken', ''),
                }
            else:
                error_data = response.json()
                logger.error(f"Google Calendar sync failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Sync failed'),
                    'events': [],
                }

        except Exception as e:
            logger.error(f"Error syncing Google Calendar: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'events': [],
            }

    def create_event(
        self,
        access_token: str,
        event_data: Dict
    ) -> Dict:
        """
        Create event in Google Calendar.

        Args:
            access_token: OAuth access token
            event_data: Event data (summary, start, end, description, etc.)

        Returns:
            Dict containing:
                - success (bool): Whether creation succeeded
                - event_id (str): Google Calendar event ID
                - event (Dict): Full event data
                - error (str): Error message if failed
        """
        try:
            import requests

            url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.post(
                url,
                headers=headers,
                json=event_data,
                timeout=10
            )

            if response.status_code == 200:
                event = response.json()
                return {
                    'success': True,
                    'event_id': event['id'],
                    'event': event,
                }
            else:
                error_data = response.json()
                logger.error(f"Google Calendar event creation failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Event creation failed')
                }

        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def update_event(
        self,
        access_token: str,
        event_id: str,
        event_data: Dict
    ) -> Dict:
        """
        Update event in Google Calendar.

        Args:
            access_token: OAuth access token
            event_id: Google Calendar event ID
            event_data: Updated event data

        Returns:
            Dict containing:
                - success (bool): Whether update succeeded
                - event (Dict): Updated event data
                - error (str): Error message if failed
        """
        try:
            import requests

            url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}'

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.put(
                url,
                headers=headers,
                json=event_data,
                timeout=10
            )

            if response.status_code == 200:
                event = response.json()
                return {
                    'success': True,
                    'event': event,
                }
            else:
                error_data = response.json()
                logger.error(f"Google Calendar event update failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Event update failed')
                }

        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def delete_event(
        self,
        access_token: str,
        event_id: str
    ) -> Dict:
        """
        Delete event from Google Calendar.

        Args:
            access_token: OAuth access token
            event_id: Google Calendar event ID

        Returns:
            Dict containing:
                - success (bool): Whether deletion succeeded
                - error (str): Error message if failed
        """
        try:
            import requests

            url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}'

            headers = {
                'Authorization': f'Bearer {access_token}',
            }

            response = requests.delete(url, headers=headers, timeout=10)

            if response.status_code == 204:
                return {'success': True}
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"Google Calendar event deletion failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Event deletion failed')
                }

        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def send_invitation(
        self,
        access_token: str,
        event_data: Dict,
        attendees: List[str]
    ) -> Dict:
        """
        Create event with attendees and send invitations.

        Args:
            access_token: OAuth access token
            event_data: Event data
            attendees: List of attendee email addresses

        Returns:
            Dict containing:
                - success (bool): Whether invitation succeeded
                - event_id (str): Google Calendar event ID
                - event (Dict): Full event data
                - error (str): Error message if failed
        """
        # Add attendees to event data
        event_data['attendees'] = [{'email': email} for email in attendees]
        event_data['sendNotifications'] = True

        return self.create_event(access_token, event_data)
