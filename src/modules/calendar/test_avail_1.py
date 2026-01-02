"""
Tests for AVAIL-1: Expanded calendar integrations.

Tests iCal/vCal feed support, multiple calendar support, all-day event handling,
and tentative/optional event handling.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from modules.calendar.ical_service import ICalService
from modules.calendar.models import AppointmentType, AvailabilityProfile
from modules.calendar.oauth_models import OAuthConnection
from modules.calendar.services import AvailabilityService
from modules.firm.models import Firm

User = get_user_model()


class ICalServiceTest(TestCase):
    """Test iCal/vCal feed parsing and availability checking."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = ICalService()
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_validate_ical_url(self):
        """Test iCal URL validation."""
        # Test invalid URLs
        self.assertFalse(self.service.validate_ical_url("not-a-url"))
        self.assertFalse(self.service.validate_ical_url("ftp://example.com/cal.ics"))

        # Test valid URL schemes
        # Note: Actual validation would require mocking HTTP requests
        # For now, we test the URL parsing logic

    def test_parse_regular_event(self):
        """Test parsing a regular event with date/time."""
        # Mock iCal event component
        from icalendar import Event

        event = Event()
        event.add('uid', 'test-event-1')
        event.add('summary', 'Test Meeting')
        event.add('dtstart', datetime(2025, 12, 15, 10, 0, 0, tzinfo=pytz.UTC))
        event.add('dtend', datetime(2025, 12, 15, 11, 0, 0, tzinfo=pytz.UTC))
        event.add('status', 'CONFIRMED')

        parsed = self.service._parse_event(event)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['id'], 'test-event-1')
        self.assertEqual(parsed['summary'], 'Test Meeting')
        self.assertFalse(parsed['is_all_day'])
        self.assertEqual(parsed['status'], 'CONFIRMED')
        self.assertTrue(parsed['is_busy'])

    def test_parse_all_day_event(self):
        """Test parsing an all-day event."""
        from icalendar import Event
        from datetime import date

        event = Event()
        event.add('uid', 'test-event-2')
        event.add('summary', 'All Day Event')
        event.add('dtstart', date(2025, 12, 15))
        event.add('status', 'CONFIRMED')

        parsed = self.service._parse_event(event)

        self.assertIsNotNone(parsed)
        self.assertTrue(parsed['is_all_day'])

    def test_parse_tentative_event(self):
        """Test parsing a tentative event."""
        from icalendar import Event

        event = Event()
        event.add('uid', 'test-event-3')
        event.add('summary', 'Tentative Meeting')
        event.add('dtstart', datetime(2025, 12, 15, 14, 0, 0, tzinfo=pytz.UTC))
        event.add('dtend', datetime(2025, 12, 15, 15, 0, 0, tzinfo=pytz.UTC))
        event.add('status', 'TENTATIVE')

        parsed = self.service._parse_event(event)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['status'], 'TENTATIVE')

    def test_parse_free_event(self):
        """Test parsing a free/transparent event."""
        from icalendar import Event

        event = Event()
        event.add('uid', 'test-event-4')
        event.add('summary', 'Free Time')
        event.add('dtstart', datetime(2025, 12, 15, 12, 0, 0, tzinfo=pytz.UTC))
        event.add('dtend', datetime(2025, 12, 15, 13, 0, 0, tzinfo=pytz.UTC))
        event.add('transp', 'TRANSPARENT')

        parsed = self.service._parse_event(event)

        self.assertIsNotNone(parsed)
        self.assertFalse(parsed['is_busy'])

    def test_times_overlap(self):
        """Test time overlap detection."""
        dt1 = datetime(2025, 12, 15, 10, 0, 0, tzinfo=pytz.UTC)
        dt2 = datetime(2025, 12, 15, 11, 0, 0, tzinfo=pytz.UTC)
        dt3 = datetime(2025, 12, 15, 10, 30, 0, tzinfo=pytz.UTC)
        dt4 = datetime(2025, 12, 15, 11, 30, 0, tzinfo=pytz.UTC)
        dt5 = datetime(2025, 12, 15, 12, 0, 0, tzinfo=pytz.UTC)

        # Overlapping cases
        self.assertTrue(self.service._times_overlap(dt1, dt2, dt3, dt4))  # Partial overlap
        self.assertTrue(self.service._times_overlap(dt1, dt4, dt3, dt2))  # One contains other

        # Non-overlapping cases
        self.assertFalse(self.service._times_overlap(dt1, dt2, dt2, dt3))  # Adjacent (touching endpoints)
        self.assertFalse(self.service._times_overlap(dt1, dt2, dt4, dt5))  # Separate


class MultipleCalendarSupportTest(TestCase):
    """Test multiple calendar connection support."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.staff_user = User.objects.create_user(username="staff", password="testpass")

        self.appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="30-min Meeting",
            duration_minutes=30,
            buffer_before_minutes=0,
            buffer_after_minutes=0,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff_user,
            created_by=self.user,
        )

        self.profile = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff Availability",
            owner_type="staff",
            owner_staff_user=self.staff_user,
            timezone="UTC",
            weekly_hours={
                "monday": [{"start": "09:00", "end": "17:00"}],
            },
            exceptions=[],
            min_notice_minutes=0,
            max_future_days=30,
            slot_rounding_minutes=15,
            created_by=self.user,
        )

    def test_multiple_connections_allowed(self):
        """Test that a user can have multiple calendar connections."""
        # Create multiple connections for the same user
        google_conn = OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='google',
            status='active',
            sync_enabled=True,
        )

        ical_conn = OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='ical',
            status='active',
            sync_enabled=True,
            ical_feed_url='https://example.com/calendar.ics',
        )

        # Verify both connections exist
        connections = OAuthConnection.objects.filter(user=self.staff_user)
        self.assertEqual(connections.count(), 2)

        # Verify we can distinguish them
        self.assertEqual(google_conn.provider, 'google')
        self.assertEqual(ical_conn.provider, 'ical')

    def test_all_day_event_preferences(self):
        """Test all-day event handling preferences."""
        conn = OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='ical',
            status='active',
            sync_enabled=True,
            ical_feed_url='https://example.com/calendar.ics',
            treat_all_day_as_busy=True,
        )

        self.assertTrue(conn.treat_all_day_as_busy)

        # Create another connection with different preference
        conn2 = OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='apple',
            status='active',
            sync_enabled=True,
            ical_feed_url='https://icloud.com/calendar.ics',
            treat_all_day_as_busy=False,
        )

        self.assertFalse(conn2.treat_all_day_as_busy)

    def test_tentative_event_preferences(self):
        """Test tentative event handling preferences."""
        conn = OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='ical',
            status='active',
            sync_enabled=True,
            ical_feed_url='https://example.com/calendar.ics',
            treat_tentative_as_busy=False,
        )

        self.assertFalse(conn.treat_tentative_as_busy)

    @patch('modules.calendar.services.ICalService.check_availability')
    def test_external_calendar_conflict_checking(self, mock_check_availability):
        """Test that external calendars are checked for conflicts."""
        # Create an iCal connection
        OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='ical',
            status='active',
            sync_enabled=True,
            ical_feed_url='https://example.com/calendar.ics',
            treat_all_day_as_busy=False,
            treat_tentative_as_busy=True,
        )

        # Mock the iCal service to return unavailable (conflict)
        mock_check_availability.return_value = False

        # Try to get available slots
        service = AvailabilityService()
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=30)

        # Check for conflict
        has_conflict = service._has_conflict(
            staff_user=self.staff_user,
            start_time=start_time,
            end_time=end_time,
            appointment_type=self.appointment_type,
        )

        # Verify that external calendar was checked
        self.assertTrue(has_conflict)
        mock_check_availability.assert_called_once()

    @patch('modules.calendar.services.ICalService.check_availability')
    def test_disabled_connections_not_checked(self, mock_check_availability):
        """Test that disabled connections are not checked for conflicts."""
        # Create a disabled connection
        OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='ical',
            status='active',
            sync_enabled=False,  # Disabled
            ical_feed_url='https://example.com/calendar.ics',
        )

        # Try to check for conflicts
        service = AvailabilityService()
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=30)

        has_conflict = service._has_conflict(
            staff_user=self.staff_user,
            start_time=start_time,
            end_time=end_time,
            appointment_type=self.appointment_type,
        )

        # Verify that external calendar was NOT checked
        self.assertFalse(has_conflict)
        mock_check_availability.assert_not_called()

    @patch('modules.calendar.services.ICalService.check_availability')
    def test_multiple_calendars_checked(self, mock_check_availability):
        """Test that all active calendars are checked for conflicts."""
        # Create multiple connections
        OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='ical',
            status='active',
            sync_enabled=True,
            ical_feed_url='https://example.com/calendar1.ics',
        )

        OAuthConnection.objects.create(
            firm=self.firm,
            user=self.staff_user,
            provider='apple',
            status='active',
            sync_enabled=True,
            ical_feed_url='https://icloud.com/calendar.ics',
        )

        # Mock the first calendar as available, second as unavailable
        mock_check_availability.side_effect = [True, False]

        # Try to check for conflicts
        service = AvailabilityService()
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=30)

        has_conflict = service._has_conflict(
            staff_user=self.staff_user,
            start_time=start_time,
            end_time=end_time,
            appointment_type=self.appointment_type,
        )

        # Should detect conflict from the second calendar
        self.assertTrue(has_conflict)
        # Should have checked both calendars
        self.assertEqual(mock_check_availability.call_count, 2)
