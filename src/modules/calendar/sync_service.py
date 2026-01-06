"""
Calendar Sync Service.

Orchestrates bi-directional sync between internal appointments
and external calendar providers (Google, Microsoft).
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from .models import Appointment
from .oauth_models import OAuthConnection
from .google_service import GoogleCalendarService
from .microsoft_service import MicrosoftCalendarService

logger = logging.getLogger(__name__)


class CalendarSyncService:
    """
    Service for bi-directional calendar sync.

    Handles syncing appointments between internal system and
    external calendar providers (Google Calendar, Microsoft Outlook).

    Meta-commentary:
    - **Current Status:** Sync flow is last-write-wins across providers and the local DB; inbound updates can overwrite local
      changes without per-field conflict resolution or revision checks.
    - **Follow-up (T-067):** Add sync-scoped locks plus provider ETag/version comparisons so concurrent push/pull cycles do
      not interleave and to detect when remote updates should be merged instead of clobbered.
    - **Assumption:** OAuthConnection.last_sync_cursor represents a reliable watermark; there is no audit to detect stale
      cursors or deleted mappings, so removed external events may linger internally.
    - **Limitation:** Sync operations do not reconcile orphaned Appointment↔external event mappings; missing webhook events or
      provider-side deletes are not detected without manual review.
    """

    def __init__(self):
        """Initialize sync service."""
        self.google_service = GoogleCalendarService()
        self.microsoft_service = MicrosoftCalendarService()

    def perform_sync(self, connection: OAuthConnection) -> Dict:
        """
        Perform full bi-directional sync for a connection.

        Args:
            connection: OAuth connection to sync

        Returns:
            Dict containing sync results:
                - success (bool): Whether sync succeeded
                - pulled (int): Events pulled from external
                - pushed (int): Events pushed to external
                - errors (List[str]): Error messages
        """
        if not connection.sync_enabled:
            return {
                'success': False,
                'error': 'Sync not enabled for this connection'
            }

        if connection.status != 'active':
            return {
                'success': False,
                'error': f'Connection status is {connection.status}'
            }

        # Refresh token if needed
        if connection.needs_refresh():
            refresh_result = self._refresh_connection_token(connection)
            if not refresh_result['success']:
                return {
                    'success': False,
                    'error': f"Token refresh failed: {refresh_result.get('error')}"
                }

        pulled = 0
        pushed = 0
        errors = []

        try:
            # Pull external events
            pull_result = self.pull_external_events(connection)
            if pull_result['success']:
                pulled = pull_result['count']
            else:
                errors.append(f"Pull failed: {pull_result.get('error')}")

            # Push internal events
            push_result = self.push_internal_events(connection)
            if push_result['success']:
                pushed = push_result['count']
            else:
                errors.append(f"Push failed: {push_result.get('error')}")

            # Update connection sync timestamp
            connection.last_sync_at = timezone.now()
            connection.save(update_fields=['last_sync_at'])

            return {
                'success': len(errors) == 0,
                'pulled': pulled,
                'pushed': pushed,
                'errors': errors,
            }

        except Exception as e:
            logger.error(f"Sync error for connection {connection.id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'pulled': pulled,
                'pushed': pushed,
                'errors': errors + [str(e)],
            }

    def pull_external_events(self, connection: OAuthConnection) -> Dict:
        """
        Pull events from external calendar and create/update appointments.

        Args:
            connection: OAuth connection

        Returns:
            Dict with success, count, and error
        """
        # Get service for provider
        if connection.provider == 'google':
            service = self.google_service
            sync_result = service.sync_events(
                access_token=connection.access_token,
                sync_window_days=connection.sync_window_days,
                sync_token=connection.last_sync_cursor,
            )
        elif connection.provider == 'microsoft':
            service = self.microsoft_service
            sync_result = service.sync_events(
                access_token=connection.access_token,
                sync_window_days=connection.sync_window_days,
                delta_link=connection.last_sync_cursor,
            )
        else:
            return {
                'success': False,
                'error': f'Unsupported provider: {connection.provider}'
            }

        if not sync_result['success']:
            return {
                'success': False,
                'error': sync_result.get('error'),
                'count': 0,
            }

        # Process events
        count = 0
        for event in sync_result.get('events', []):
            try:
                self._process_external_event(connection, event)
                count += 1
            except Exception as e:
                logger.error(f"Error processing event {event.get('id')}: {e}")

        # Update sync cursor
        if sync_result.get('next_sync_token'):
            connection.last_sync_cursor = sync_result['next_sync_token']
            connection.save(update_fields=['last_sync_cursor'])
        elif sync_result.get('next_delta_link'):
            connection.last_sync_cursor = sync_result['next_delta_link']
            connection.save(update_fields=['last_sync_cursor'])

        return {
            'success': True,
            'count': count,
        }

    def push_internal_events(self, connection: OAuthConnection) -> Dict:
        """
        Push internal appointments to external calendar.

        Args:
            connection: OAuth connection

        Returns:
            Dict with success, count, and error
        """
        # Get appointments that need syncing (no external_event_id yet)
        # and belong to the connection's user
        now = timezone.now()
        sync_window_start = now - timedelta(days=connection.sync_window_days)
        sync_window_end = now + timedelta(days=connection.sync_window_days)

        appointments = Appointment.objects.filter(
            firm=connection.firm,
            staff_user=connection.user,
            start_time__gte=sync_window_start,
            start_time__lte=sync_window_end,
            external_event_id='',  # Not yet synced
            status='confirmed',
        )

        count = 0
        for appointment in appointments:
            try:
                result = self._push_appointment_to_external(connection, appointment)
                if result['success']:
                    count += 1
            except Exception as e:
                logger.error(f"Error pushing appointment {appointment.id}: {e}")

        return {
            'success': True,
            'count': count,
        }

    def reconcile_conflicts(
        self,
        internal_event: Appointment,
        external_event: Dict
    ) -> str:
        """
        Reconcile conflicts between internal and external events.

        Args:
            internal_event: Internal appointment
            external_event: External calendar event

        Returns:
            Action to take: 'keep_internal', 'keep_external', or 'merge'
        """
        # Simple last-modified wins strategy
        internal_modified = internal_event.updated_at
        external_modified_str = external_event.get('updated') or external_event.get('lastModifiedDateTime')

        if external_modified_str:
            try:
                external_modified = datetime.fromisoformat(external_modified_str.replace('Z', '+00:00'))
                if external_modified > internal_modified:
                    return 'keep_external'
            except:
                pass

        return 'keep_internal'

    def handle_sync_error(self, connection: OAuthConnection, error: Exception) -> None:
        """
        Handle sync error with retry logic.

        Args:
            connection: OAuth connection
            error: Exception that occurred
        """
        logger.error(f"Sync error for connection {connection.id}: {error}")

        connection.error_message = str(error)

        # Check if token expired
        if 'invalid_grant' in str(error).lower() or 'expired' in str(error).lower():
            connection.status = 'expired'
        else:
            connection.status = 'error'

        connection.save(update_fields=['status', 'error_message'])

    def _refresh_connection_token(self, connection: OAuthConnection) -> Dict:
        """
        Refresh OAuth token for connection.

        Args:
            connection: OAuth connection

        Returns:
            Dict with success status
        """
        if connection.provider == 'google':
            service = self.google_service
            result = service.refresh_token(connection.refresh_token)
        elif connection.provider == 'microsoft':
            service = self.microsoft_service
            result = service.refresh_token(connection.refresh_token)
        else:
            return {'success': False, 'error': 'Unsupported provider'}

        if result['success']:
            connection.access_token = result['access_token']
            connection.token_expires_at = timezone.now() + timedelta(
                seconds=result.get('expires_in', 3600)
            )
            connection.status = 'active'
            connection.save(update_fields=['access_token', 'token_expires_at', 'status'])

        return result

    def _process_external_event(self, connection: OAuthConnection, event: Dict):
        """
        Process external event and create/update appointment.

        Args:
            connection: OAuth connection
            event: External event data
        """
        # Extract event ID
        event_id = event.get('id')
        if not event_id:
            return

        # Check if appointment already exists
        existing = Appointment.objects.filter(
            firm=connection.firm,
            external_event_id=event_id,
        ).first()

        # Parse event times
        start_time = self._parse_event_time(event, 'start', connection.provider)
        end_time = self._parse_event_time(event, 'end', connection.provider)

        if not start_time or not end_time:
            logger.warning(f"Could not parse times for event {event_id}")
            return

        # Create or update appointment
        with transaction.atomic():
            if existing:
                # Update existing
                if self.reconcile_conflicts(existing, event) == 'keep_external':
                    existing.start_time = start_time
                    existing.end_time = end_time
                    existing.save(update_fields=['start_time', 'end_time'])
            else:
                # Create new (simplified - would need appointment type, etc.)
                logger.info(f"Would create appointment from event {event_id}")
                # In real implementation, create appointment with proper fields

    def _push_appointment_to_external(
        self,
        connection: OAuthConnection,
        appointment: Appointment
    ) -> Dict:
        """
        Push internal appointment to external calendar.

        Args:
            connection: OAuth connection
            appointment: Appointment to push

        Returns:
            Dict with success status
        """
        # Build event data
        event_data = {
            'summary': appointment.appointment_type.name,
            'start': {
                'dateTime': appointment.start_time.isoformat(),
                'timeZone': appointment.timezone,
            },
            'end': {
                'dateTime': appointment.end_time.isoformat(),
                'timeZone': appointment.timezone,
            },
        }

        # Create event in external calendar
        if connection.provider == 'google':
            service = self.google_service
            result = service.create_event(connection.access_token, event_data)
        elif connection.provider == 'microsoft':
            service = self.microsoft_service
            result = service.create_event(connection.access_token, event_data)
        else:
            return {'success': False, 'error': 'Unsupported provider'}

        if result['success']:
            # Save external ID
            appointment.external_event_id = result['event_id']
            appointment.save(update_fields=['external_event_id'])

        return result

    def _parse_event_time(self, event: Dict, field: str, provider: str) -> Optional[datetime]:
        """
        Parse event time from external event.

        Args:
            event: External event data
            field: Field name ('start' or 'end')
            provider: Provider name ('google' or 'microsoft')

        Returns:
            Parsed datetime or None
        """
        try:
            if provider == 'google':
                time_data = event.get(field, {})
                time_str = time_data.get('dateTime')
                if time_str:
                    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            elif provider == 'microsoft':
                time_data = event.get(field, {})
                time_str = time_data.get('dateTime')
                if time_str:
                    return datetime.fromisoformat(time_str + '+00:00')
        except Exception as e:
            logger.error(f"Error parsing time from {provider} event: {e}")

        return None
