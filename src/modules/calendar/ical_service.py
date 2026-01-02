"""
iCal/vCal Calendar Integration Service.

Provides support for iCloud Calendar and generic iCal/vCal feed integration.
Implements AVAIL-1: Expand calendar integrations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from django.utils import timezone
from icalendar import Calendar

logger = logging.getLogger(__name__)


class ICalService:
    """
    Service for iCal/vCal calendar integration.

    Supports:
    - iCloud Calendar via iCal feed URLs
    - Generic iCal/vCal feed support
    - All-day event handling
    - Tentative/optional event handling
    """

    def __init__(self):
        """Initialize iCal service."""
        self.timeout = 30  # Request timeout in seconds

    def validate_ical_url(self, url: str) -> bool:
        """
        Validate that a URL is a valid iCal feed.

        Args:
            url: iCal feed URL to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme in ['http', 'https', 'webcal']:
                return False

            # Convert webcal:// to https://
            if parsed.scheme == 'webcal':
                url = url.replace('webcal://', 'https://')

            # Try to fetch and parse the feed
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Try to parse as iCal
            Calendar.from_ical(response.content)
            return True

        except Exception as e:
            logger.warning(f"iCal URL validation failed: {e}")
            return False

    def fetch_events(
        self,
        feed_url: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_all_day: bool = True,
        include_tentative: bool = True,
    ) -> List[Dict]:
        """
        Fetch events from an iCal feed.

        Args:
            feed_url: iCal feed URL
            start_date: Filter events starting after this date
            end_date: Filter events ending before this date
            include_all_day: Whether to include all-day events (default: True)
            include_tentative: Whether to include tentative/optional events (default: True)

        Returns:
            List of event dictionaries
        """
        try:
            # Convert webcal:// to https://
            if feed_url.startswith('webcal://'):
                feed_url = feed_url.replace('webcal://', 'https://')

            # Fetch the iCal feed
            response = requests.get(feed_url, timeout=self.timeout)
            response.raise_for_status()

            # Parse the iCal feed
            cal = Calendar.from_ical(response.content)

            events = []
            for component in cal.walk():
                if component.name != 'VEVENT':
                    continue

                event = self._parse_event(component)
                if not event:
                    continue

                # Filter by date range
                if start_date and event['end'] < start_date:
                    continue
                if end_date and event['start'] > end_date:
                    continue

                # Filter all-day events
                if event.get('is_all_day') and not include_all_day:
                    continue

                # Filter tentative events
                if event.get('status') in ['TENTATIVE', 'CANCELLED'] and not include_tentative:
                    continue

                events.append(event)

            return events

        except Exception as e:
            logger.error(f"Failed to fetch iCal events: {e}")
            raise

    def _parse_event(self, component) -> Optional[Dict]:
        """
        Parse an iCal VEVENT component into a dictionary.

        Args:
            component: iCalendar VEVENT component

        Returns:
            Event dictionary or None if parsing fails
        """
        try:
            # Extract basic fields
            uid = str(component.get('UID', ''))
            summary = str(component.get('SUMMARY', ''))
            description = str(component.get('DESCRIPTION', ''))
            location = str(component.get('LOCATION', ''))
            status = str(component.get('STATUS', 'CONFIRMED'))

            # Parse start and end times
            dtstart = component.get('DTSTART')
            dtend = component.get('DTEND')

            if not dtstart:
                return None

            # Handle all-day events
            is_all_day = False
            if hasattr(dtstart.dt, 'date') and not hasattr(dtstart.dt, 'hour'):
                is_all_day = True
                start_time = timezone.make_aware(
                    datetime.combine(dtstart.dt, datetime.min.time())
                )
                if dtend:
                    end_time = timezone.make_aware(
                        datetime.combine(dtend.dt, datetime.min.time())
                    )
                else:
                    end_time = start_time + timedelta(days=1)
            else:
                # Regular event with time
                start_time = dtstart.dt
                if not timezone.is_aware(start_time):
                    start_time = timezone.make_aware(start_time)

                if dtend:
                    end_time = dtend.dt
                    if not timezone.is_aware(end_time):
                        end_time = timezone.make_aware(end_time)
                else:
                    # Default duration: 1 hour
                    end_time = start_time + timedelta(hours=1)

            # Parse recurrence rules if present
            rrule = component.get('RRULE')
            recurrence_rule = str(rrule) if rrule else None

            # Parse attendees and organizer
            attendees = []
            for attendee in component.get('ATTENDEE', []):
                if isinstance(attendee, list):
                    attendees.extend([str(a) for a in attendee])
                else:
                    attendees.append(str(attendee))

            organizer = component.get('ORGANIZER')
            organizer_email = str(organizer) if organizer else None

            # Parse transparency (for busy/free status)
            transparency = str(component.get('TRANSP', 'OPAQUE'))
            is_busy = transparency == 'OPAQUE'

            return {
                'id': uid,
                'summary': summary,
                'description': description,
                'location': location,
                'start': start_time,
                'end': end_time,
                'is_all_day': is_all_day,
                'status': status,
                'is_busy': is_busy,
                'recurrence_rule': recurrence_rule,
                'attendees': attendees,
                'organizer': organizer_email,
            }

        except Exception as e:
            logger.warning(f"Failed to parse iCal event: {e}")
            return None

    def check_availability(
        self,
        feed_url: str,
        start_time: datetime,
        end_time: datetime,
        treat_all_day_as_busy: bool = False,
        treat_tentative_as_busy: bool = True,
    ) -> bool:
        """
        Check if a time slot is available based on iCal feed.

        Args:
            feed_url: iCal feed URL
            start_time: Start of time slot to check
            end_time: End of time slot to check
            treat_all_day_as_busy: Whether to treat all-day events as busy (default: False)
            treat_tentative_as_busy: Whether to treat tentative events as busy (default: True)

        Returns:
            True if available (no conflicts), False if busy
        """
        try:
            # Fetch events in the time window
            events = self.fetch_events(
                feed_url=feed_url,
                start_date=start_time - timedelta(days=1),
                end_date=end_time + timedelta(days=1),
                include_all_day=treat_all_day_as_busy,
                include_tentative=treat_tentative_as_busy,
            )

            # Check for conflicts
            for event in events:
                # Skip cancelled events
                if event.get('status') == 'CANCELLED':
                    continue

                # Skip free/transparent events
                if not event.get('is_busy'):
                    continue

                # Skip all-day events if configured
                if event.get('is_all_day') and not treat_all_day_as_busy:
                    continue

                # Skip tentative events if configured
                if event.get('status') == 'TENTATIVE' and not treat_tentative_as_busy:
                    continue

                # Check for overlap
                event_start = event['start']
                event_end = event['end']

                if self._times_overlap(start_time, end_time, event_start, event_end):
                    logger.debug(
                        f"Conflict found: {event.get('summary')} "
                        f"({event_start} - {event_end})"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            # Default to busy if we can't check
            return False

    def _times_overlap(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime,
    ) -> bool:
        """
        Check if two time ranges overlap.

        Args:
            start1: Start of first time range
            end1: End of first time range
            start2: Start of second time range
            end2: End of second time range

        Returns:
            True if ranges overlap, False otherwise
        """
        return start1 < end2 and end1 > start2
