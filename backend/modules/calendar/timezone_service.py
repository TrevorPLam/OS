"""
Timezone Intelligence Service.

Provides timezone detection, conversion, and display features.
Implements AVAIL-4: Timezone intelligence.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pytz
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


class TimezoneService:
    """
    Service for timezone intelligence features.

    Implements AVAIL-4:
    - Auto-detect invitee timezone
    - Display times in invitee's local timezone
    - Timezone conversion for all availability calculations
    - Daylight saving time handling
    - Multiple timezone support for distributed teams
    """

    # Common timezone mappings for auto-detection
    COMMON_TIMEZONES = {
        'US/Eastern': 'America/New_York',
        'US/Central': 'America/Chicago',
        'US/Mountain': 'America/Denver',
        'US/Pacific': 'America/Los_Angeles',
        'US/Alaska': 'America/Anchorage',
        'US/Hawaii': 'Pacific/Honolulu',
        'UK': 'Europe/London',
        'GMT': 'GMT',
        'UTC': 'UTC',
    }

    @staticmethod
    def get_user_timezone_from_browser(timezone_offset_minutes: int) -> str:
        """
        Auto-detect user timezone from browser timezone offset.

        Args:
            timezone_offset_minutes: Browser timezone offset in minutes (from JS Date.getTimezoneOffset())
                                    Note: This is negative for timezones ahead of UTC

        Returns:
            Best guess timezone name (e.g., 'America/New_York')
        """
        # Convert offset to hours
        offset_hours = -timezone_offset_minutes / 60  # Negate because JS returns negative for ahead of UTC

        # Map offset to likely timezone
        # This is a simple heuristic - more sophisticated detection would use Intl API data
        offset_to_timezone = {
            -12: 'Pacific/Majuro',
            -11: 'Pacific/Midway',
            -10: 'Pacific/Honolulu',
            -9: 'America/Anchorage',
            -8: 'America/Los_Angeles',
            -7: 'America/Denver',
            -6: 'America/Chicago',
            -5: 'America/New_York',
            -4: 'America/Halifax',
            -3: 'America/Sao_Paulo',
            -2: 'Atlantic/South_Georgia',
            -1: 'Atlantic/Azores',
            0: 'UTC',
            1: 'Europe/London',  # or Europe/Paris during DST
            2: 'Europe/Athens',
            3: 'Europe/Moscow',
            4: 'Asia/Dubai',
            5: 'Asia/Karachi',
            5.5: 'Asia/Kolkata',
            6: 'Asia/Dhaka',
            7: 'Asia/Bangkok',
            8: 'Asia/Shanghai',
            9: 'Asia/Tokyo',
            10: 'Australia/Sydney',
            11: 'Pacific/Noumea',
            12: 'Pacific/Auckland',
        }

        timezone_name = offset_to_timezone.get(offset_hours, 'UTC')
        logger.debug(f"Detected timezone {timezone_name} from offset {offset_hours}")
        return timezone_name

    @staticmethod
    def normalize_timezone_name(timezone_name: str) -> str:
        """
        Normalize timezone name to standard IANA format.

        Args:
            timezone_name: Timezone name (may be abbreviation or old format)

        Returns:
            Normalized timezone name
        """
        # Handle common aliases
        if timezone_name in TimezoneService.COMMON_TIMEZONES:
            return TimezoneService.COMMON_TIMEZONES[timezone_name]

        # Validate it's a real timezone
        try:
            pytz.timezone(timezone_name)
            return timezone_name
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Unknown timezone {timezone_name}, defaulting to UTC")
            return 'UTC'

    @staticmethod
    def convert_time_to_timezone(
        dt: datetime,
        from_timezone: str,
        to_timezone: str,
    ) -> datetime:
        """
        Convert datetime from one timezone to another.

        Handles DST transitions automatically.

        Args:
            dt: Datetime to convert (can be naive or aware)
            from_timezone: Source timezone name
            to_timezone: Target timezone name

        Returns:
            Datetime in target timezone (aware)
        """
        from_tz = pytz.timezone(from_timezone)
        to_tz = pytz.timezone(to_timezone)

        # If datetime is naive, localize it to source timezone
        if dt.tzinfo is None:
            dt_aware = from_tz.localize(dt)
        else:
            dt_aware = dt

        # Convert to target timezone
        dt_converted = dt_aware.astimezone(to_tz)

        return dt_converted

    @staticmethod
    def format_time_for_display(
        dt: datetime,
        timezone_name: str,
        format_str: str = "%Y-%m-%d %H:%M %Z",
    ) -> str:
        """
        Format datetime for display in a specific timezone.

        Args:
            dt: Datetime to format (aware)
            timezone_name: Timezone to display in
            format_str: Format string (default includes timezone abbreviation)

        Returns:
            Formatted datetime string
        """
        tz = pytz.timezone(timezone_name)
        dt_local = dt.astimezone(tz)
        return dt_local.strftime(format_str)

    @staticmethod
    def get_timezone_info(timezone_name: str) -> Dict:
        """
        Get information about a timezone.

        Args:
            timezone_name: Timezone name

        Returns:
            Dictionary with timezone info:
            - name: Timezone name
            - abbreviation: Current abbreviation (e.g., 'EST', 'EDT')
            - offset: Current UTC offset in hours
            - dst_active: Whether DST is currently active
        """
        tz = pytz.timezone(timezone_name)
        now = django_timezone.now()
        dt_in_tz = now.astimezone(tz)

        # Get UTC offset in hours
        offset_seconds = dt_in_tz.utcoffset().total_seconds()
        offset_hours = offset_seconds / 3600

        # Get timezone abbreviation
        abbreviation = dt_in_tz.strftime('%Z')

        # Check if DST is active (heuristic: check if abbreviation contains 'D')
        dst_active = 'D' in abbreviation or offset_hours != tz.localize(datetime(2000, 1, 1)).utcoffset().total_seconds() / 3600

        return {
            'name': timezone_name,
            'abbreviation': abbreviation,
            'offset': offset_hours,
            'dst_active': dst_active,
        }

    @staticmethod
    def get_best_meeting_time_for_timezones(
        start_time: datetime,
        duration_minutes: int,
        participant_timezones: List[str],
    ) -> Dict:
        """
        Analyze meeting time across multiple timezones.

        Useful for distributed teams to find convenient times.

        Args:
            start_time: Proposed meeting start time (aware)
            duration_minutes: Meeting duration
            participant_timezones: List of participant timezones

        Returns:
            Dictionary with:
            - times_by_timezone: Dict of timezone -> local time display
            - business_hours_count: Number of participants for whom it's business hours
            - late_night_count: Number of participants for whom it's late night
            - early_morning_count: Number of participants for whom it's early morning
            - fairness_score: 0-100, higher is better (100 = all in business hours)
        """
        times_by_timezone = {}
        business_hours_count = 0
        late_night_count = 0
        early_morning_count = 0

        for tz_name in participant_timezones:
            tz = pytz.timezone(tz_name)
            local_time = start_time.astimezone(tz)
            times_by_timezone[tz_name] = local_time.strftime("%H:%M %Z")

            hour = local_time.hour

            # Business hours: 9am - 5pm
            if 9 <= hour < 17:
                business_hours_count += 1
            # Late night: 10pm - 3am
            elif 22 <= hour or hour < 3:
                late_night_count += 1
            # Early morning: 5am - 8am
            elif 5 <= hour < 9:
                early_morning_count += 1

        total_participants = len(participant_timezones)
        fairness_score = int((business_hours_count / total_participants) * 100) if total_participants > 0 else 0

        return {
            'times_by_timezone': times_by_timezone,
            'business_hours_count': business_hours_count,
            'late_night_count': late_night_count,
            'early_morning_count': early_morning_count,
            'fairness_score': fairness_score,
        }

    @staticmethod
    def find_common_business_hours(
        timezones: List[str],
        start_hour: int = 9,
        end_hour: int = 17,
    ) -> List[Tuple[int, int]]:
        """
        Find overlapping business hours across multiple timezones.

        Args:
            timezones: List of timezone names
            start_hour: Start of business hours (default: 9am)
            end_hour: End of business hours (default: 5pm)

        Returns:
            List of (hour, hour) tuples representing common business hours in UTC
        """
        if not timezones:
            return []

        # For simplicity, we'll check each hour of the day
        common_hours = []

        for hour in range(24):
            # Check if this UTC hour is within business hours for all timezones
            is_common = True

            for tz_name in timezones:
                tz = pytz.timezone(tz_name)
                # Create a datetime for today at this UTC hour
                now = django_timezone.now()
                utc_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                local_time = utc_time.astimezone(tz)

                local_hour = local_time.hour

                # Check if within business hours
                if not (start_hour <= local_hour < end_hour):
                    is_common = False
                    break

            if is_common:
                common_hours.append(hour)

        # Convert to ranges
        ranges = []
        if common_hours:
            range_start = common_hours[0]
            range_end = common_hours[0]

            for hour in common_hours[1:]:
                if hour == range_end + 1:
                    range_end = hour
                else:
                    ranges.append((range_start, range_end + 1))
                    range_start = hour
                    range_end = hour

            ranges.append((range_start, range_end + 1))

        return ranges

    @staticmethod
    def is_dst_transition_date(dt: datetime, timezone_name: str) -> bool:
        """
        Check if a date is a DST transition date.

        Args:
            dt: Date to check
            timezone_name: Timezone name

        Returns:
            True if date is a DST transition date
        """
        tz = pytz.timezone(timezone_name)

        # Check the day before and after
        prev_day = dt - django_timezone.timedelta(days=1)
        next_day = dt + django_timezone.timedelta(days=1)

        try:
            dt_local = tz.normalize(tz.localize(dt.replace(hour=12, minute=0)))
            prev_local = tz.normalize(tz.localize(prev_day.replace(hour=12, minute=0)))
            next_local = tz.normalize(tz.localize(next_day.replace(hour=12, minute=0)))

            # Check if UTC offset changed
            return (dt_local.utcoffset() != prev_local.utcoffset() or
                    dt_local.utcoffset() != next_local.utcoffset())
        except Exception as e:
            logger.warning(f"Error checking DST transition: {e}")
            return False
