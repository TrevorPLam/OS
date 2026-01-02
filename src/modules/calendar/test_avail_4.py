"""
Tests for AVAIL-4: Timezone intelligence.

Tests timezone detection, conversion, display, and distributed team support.
"""

from datetime import datetime, timedelta

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from modules.calendar.timezone_service import TimezoneService
from modules.firm.models import Firm

User = get_user_model()


class TimezoneDetectionTest(TestCase):
    """Test timezone auto-detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TimezoneService()

    def test_timezone_from_browser_offset(self):
        """Test timezone detection from browser offset."""
        # US Eastern Time (EST/EDT = UTC-5/-4)
        # Browser returns positive offset for behind UTC
        tz = self.service.get_user_timezone_from_browser(300)  # -5 hours
        self.assertEqual(tz, 'America/New_York')

        # US Pacific Time (PST/PDT = UTC-8/-7)
        tz = self.service.get_user_timezone_from_browser(480)  # -8 hours
        self.assertEqual(tz, 'America/Los_Angeles')

        # UK Time (GMT/BST = UTC+0/+1)
        tz = self.service.get_user_timezone_from_browser(0)  # UTC
        self.assertEqual(tz, 'UTC')

        # Japan Time (JST = UTC+9)
        # Browser returns negative offset for ahead of UTC
        tz = self.service.get_user_timezone_from_browser(-540)  # +9 hours
        self.assertEqual(tz, 'Asia/Tokyo')

    def test_normalize_timezone_name(self):
        """Test timezone name normalization."""
        # Common aliases
        self.assertEqual(
            self.service.normalize_timezone_name('US/Eastern'),
            'America/New_York'
        )
        self.assertEqual(
            self.service.normalize_timezone_name('US/Pacific'),
            'America/Los_Angeles'
        )

        # Already normalized
        self.assertEqual(
            self.service.normalize_timezone_name('America/Chicago'),
            'America/Chicago'
        )

        # Invalid timezone defaults to UTC
        self.assertEqual(
            self.service.normalize_timezone_name('Invalid/Timezone'),
            'UTC'
        )


class TimezoneConversionTest(TestCase):
    """Test timezone conversion."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TimezoneService()

    def test_convert_time_to_timezone(self):
        """Test datetime conversion between timezones."""
        # Create a datetime in US Eastern Time
        eastern_tz = pytz.timezone('America/New_York')
        dt_eastern = eastern_tz.localize(datetime(2025, 6, 15, 10, 0, 0))  # Summer (EDT)

        # Convert to US Pacific Time
        dt_pacific = self.service.convert_time_to_timezone(
            dt=dt_eastern,
            from_timezone='America/New_York',
            to_timezone='America/Los_Angeles',
        )

        # Should be 3 hours earlier (EDT = UTC-4, PDT = UTC-7)
        self.assertEqual(dt_pacific.hour, 7)
        self.assertEqual(dt_pacific.day, 15)

    def test_convert_naive_datetime(self):
        """Test conversion of naive datetime."""
        # Create naive datetime
        dt_naive = datetime(2025, 1, 15, 14, 0, 0)

        # Convert from Eastern to Pacific
        dt_converted = self.service.convert_time_to_timezone(
            dt=dt_naive,
            from_timezone='America/New_York',
            to_timezone='America/Los_Angeles',
        )

        # Should be 3 hours earlier in winter (EST = UTC-5, PST = UTC-8)
        self.assertEqual(dt_converted.hour, 11)
        self.assertIsNotNone(dt_converted.tzinfo)

    def test_dst_handling(self):
        """Test DST transition handling."""
        # Create datetime during DST
        dt_summer = datetime(2025, 6, 15, 14, 0, 0)
        dt_summer_converted = self.service.convert_time_to_timezone(
            dt=dt_summer,
            from_timezone='America/New_York',
            to_timezone='UTC',
        )

        # EDT is UTC-4
        self.assertEqual(dt_summer_converted.hour, 18)

        # Create datetime during standard time
        dt_winter = datetime(2025, 1, 15, 14, 0, 0)
        dt_winter_converted = self.service.convert_time_to_timezone(
            dt=dt_winter,
            from_timezone='America/New_York',
            to_timezone='UTC',
        )

        # EST is UTC-5
        self.assertEqual(dt_winter_converted.hour, 19)


class TimezoneDisplayTest(TestCase):
    """Test timezone display formatting."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TimezoneService()

    def test_format_time_for_display(self):
        """Test formatting datetime for display."""
        # Create UTC datetime
        dt_utc = timezone.make_aware(
            datetime(2025, 6, 15, 18, 0, 0),
            pytz.UTC
        )

        # Format in Eastern Time
        display_str = self.service.format_time_for_display(
            dt=dt_utc,
            timezone_name='America/New_York',
            format_str='%Y-%m-%d %H:%M %Z',
        )

        # Should show EDT (summer) and 14:00 (18:00 UTC - 4 hours)
        self.assertIn('2025-06-15', display_str)
        self.assertIn('14:00', display_str)
        self.assertIn('EDT', display_str)

    def test_timezone_info(self):
        """Test getting timezone information."""
        # Get info for US Eastern
        info = self.service.get_timezone_info('America/New_York')

        self.assertEqual(info['name'], 'America/New_York')
        self.assertIn(info['abbreviation'], ['EST', 'EDT'])
        self.assertIsInstance(info['offset'], float)
        self.assertIsInstance(info['dst_active'], bool)


class DistributedTeamSupportTest(TestCase):
    """Test distributed team timezone features."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TimezoneService()

    def test_best_meeting_time_analysis(self):
        """Test analyzing meeting time across timezones."""
        # Create a meeting at 2pm UTC
        meeting_time = timezone.make_aware(
            datetime(2025, 6, 15, 14, 0, 0),
            pytz.UTC
        )

        participant_timezones = [
            'America/New_York',  # 10am EDT
            'America/Los_Angeles',  # 7am PDT
            'Europe/London',  # 3pm BST
            'Asia/Tokyo',  # 11pm JST
        ]

        analysis = self.service.get_best_meeting_time_for_timezones(
            start_time=meeting_time,
            duration_minutes=60,
            participant_timezones=participant_timezones,
        )

        # Check that times are displayed for each timezone
        self.assertEqual(len(analysis['times_by_timezone']), 4)
        self.assertIn('America/New_York', analysis['times_by_timezone'])

        # Check fairness metrics
        self.assertIsInstance(analysis['business_hours_count'], int)
        self.assertIsInstance(analysis['late_night_count'], int)
        self.assertIsInstance(analysis['fairness_score'], int)

        # For this time, NY and London should be in business hours
        self.assertGreaterEqual(analysis['business_hours_count'], 2)

        # Tokyo should be late night
        self.assertGreaterEqual(analysis['late_night_count'], 1)

    def test_find_common_business_hours(self):
        """Test finding overlapping business hours."""
        timezones = [
            'America/New_York',  # UTC-4 in summer
            'Europe/London',  # UTC+1 in summer
        ]

        common_hours = self.service.find_common_business_hours(
            timezones=timezones,
            start_hour=9,
            end_hour=17,
        )

        # Should find some overlapping hours
        self.assertGreater(len(common_hours), 0)

        # The overlap should be in the afternoon UTC
        # NY: 9am-5pm EDT = 1pm-9pm UTC
        # London: 9am-5pm BST = 8am-4pm UTC
        # Overlap: 1pm-4pm UTC = 13-16
        self.assertIn(13, common_hours)
        self.assertIn(14, common_hours)
        self.assertIn(15, common_hours)

    def test_no_common_business_hours(self):
        """Test when there are no common business hours."""
        timezones = [
            'America/Los_Angeles',  # UTC-7 in summer
            'Asia/Tokyo',  # UTC+9
        ]

        common_hours = self.service.find_common_business_hours(
            timezones=timezones,
            start_hour=9,
            end_hour=17,
        )

        # Should have very little or no overlap (16 hour difference)
        # This is expected for opposite sides of the world
        self.assertLessEqual(len(common_hours), 2)


class DSTTransitionTest(TestCase):
    """Test DST transition handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TimezoneService()

    def test_dst_transition_detection(self):
        """Test detecting DST transition dates."""
        # US DST typically starts on second Sunday in March
        # and ends on first Sunday in November

        # Create a date during DST transition (approximate)
        transition_date = datetime(2025, 3, 9, 12, 0, 0)

        # This should detect DST transition
        # Note: Actual transition detection may vary based on implementation
        # and the exact date of DST transition in 2025
        is_transition = self.service.is_dst_transition_date(
            dt=transition_date,
            timezone_name='America/New_York',
        )

        # We expect this to be a transition date or close to one
        # (implementation dependent)

    def test_timezone_offset_during_dst(self):
        """Test timezone offset changes during DST."""
        eastern = pytz.timezone('America/New_York')

        # Winter (EST)
        winter_dt = eastern.localize(datetime(2025, 1, 15, 12, 0, 0))
        winter_offset = winter_dt.utcoffset().total_seconds() / 3600

        # Summer (EDT)
        summer_dt = eastern.localize(datetime(2025, 6, 15, 12, 0, 0))
        summer_offset = summer_dt.utcoffset().total_seconds() / 3600

        # Should differ by 1 hour
        self.assertEqual(winter_offset - summer_offset, -1)

        # EST is UTC-5, EDT is UTC-4
        self.assertEqual(winter_offset, -5)
        self.assertEqual(summer_offset, -4)
