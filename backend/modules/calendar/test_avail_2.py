"""
Tests for AVAIL-2: Comprehensive availability rules.

Tests recurring unavailability, holiday blocking, and meeting gap configuration.
"""

from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from modules.calendar.holiday_service import HolidayService
from modules.calendar.models import Appointment, AppointmentType, AvailabilityProfile
from modules.calendar.services import AvailabilityService
from modules.firm.models import Firm

User = get_user_model()


class HolidayServiceTest(TestCase):
    """Test holiday detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = HolidayService()

    def test_us_holidays_2025(self):
        """Test US holiday detection for 2025."""
        holidays = self.service.get_us_holidays(2025)

        # Check that we have all major holidays
        holiday_names = [h['name'] for h in holidays]
        self.assertIn("New Year's Day", holiday_names)
        self.assertIn("Independence Day", holiday_names)
        self.assertIn("Thanksgiving Day", holiday_names)
        self.assertIn("Christmas Day", holiday_names)
        self.assertIn("Memorial Day", holiday_names)
        self.assertIn("Labor Day", holiday_names)

    def test_thanksgiving_calculation(self):
        """Test Thanksgiving calculation (4th Thursday in November)."""
        holidays = self.service.get_us_holidays(2025)
        thanksgiving = [h for h in holidays if h['name'] == "Thanksgiving Day"][0]

        # In 2025, Thanksgiving is November 27
        self.assertEqual(thanksgiving['date'], '2025-11-27')

        # Verify it's a Thursday
        thanksgiving_date = datetime.strptime(thanksgiving['date'], '%Y-%m-%d').date()
        self.assertEqual(thanksgiving_date.weekday(), 3)  # Thursday

    def test_is_holiday(self):
        """Test holiday checking."""
        # New Year's Day 2025
        self.assertTrue(
            self.service.is_holiday(
                check_date=date(2025, 1, 1),
                timezone_name='America/New_York',
            )
        )

        # Regular day
        self.assertFalse(
            self.service.is_holiday(
                check_date=date(2025, 3, 15),
                timezone_name='America/New_York',
            )
        )

    def test_custom_holidays(self):
        """Test custom holiday support."""
        custom_holidays = [
            {'date': '2025-06-15', 'name': 'Company Holiday'},
        ]

        self.assertTrue(
            self.service.is_holiday(
                check_date=date(2025, 6, 15),
                timezone_name='America/New_York',
                custom_holidays=custom_holidays,
            )
        )


class RecurringUnavailabilityTest(TestCase):
    """Test recurring unavailability blocks."""

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

        self.service = AvailabilityService()

    def test_lunch_break_unavailability(self):
        """Test that lunch breaks block availability."""
        profile = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff Availability",
            owner_type="staff",
            owner_staff_user=self.staff_user,
            timezone="America/New_York",
            weekly_hours={
                "monday": [{"start": "09:00", "end": "17:00"}],
            },
            recurring_unavailability=[
                {
                    "day_of_week": "monday",
                    "start": "12:00",
                    "end": "13:00",
                    "reason": "Lunch",
                }
            ],
            exceptions=[],
            min_notice_minutes=0,
            max_future_days=30,
            slot_rounding_minutes=30,
            created_by=self.user,
        )

        # Get a Monday in the future
        today = date.today()
        days_until_monday = (0 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)

        slots = self.service.compute_available_slots(
            profile=profile,
            appointment_type=self.appointment_type,
            start_date=next_monday,
            end_date=next_monday,
            staff_user=self.staff_user,
        )

        # Check that no slots overlap with lunch (12:00-13:00)
        ny_tz = pytz.timezone("America/New_York")
        lunch_start = ny_tz.localize(
            datetime.combine(next_monday, datetime.min.time()).replace(hour=12)
        )
        lunch_end = ny_tz.localize(
            datetime.combine(next_monday, datetime.min.time()).replace(hour=13)
        )

        for start, end in slots:
            start_ny = start.astimezone(ny_tz)
            end_ny = end.astimezone(ny_tz)

            # Verify no overlap with lunch
            self.assertFalse(
                start_ny < lunch_end and end_ny > lunch_start,
                f"Slot {start_ny}-{end_ny} overlaps with lunch {lunch_start}-{lunch_end}",
            )

    def test_multiple_recurring_blocks(self):
        """Test multiple recurring unavailability blocks."""
        profile = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff Availability",
            owner_type="staff",
            owner_staff_user=self.staff_user,
            timezone="UTC",
            weekly_hours={
                "monday": [{"start": "09:00", "end": "17:00"}],
            },
            recurring_unavailability=[
                {
                    "day_of_week": "monday",
                    "start": "10:00",
                    "end": "10:30",
                    "reason": "Team standup",
                },
                {
                    "day_of_week": "monday",
                    "start": "12:00",
                    "end": "13:00",
                    "reason": "Lunch",
                },
            ],
            exceptions=[],
            min_notice_minutes=0,
            max_future_days=30,
            slot_rounding_minutes=30,
            created_by=self.user,
        )

        # Test _apply_recurring_unavailability directly
        day_hours = [{"start": "09:00", "end": "17:00"}]
        result = self.service._apply_recurring_unavailability(
            day_hours, "monday", profile.recurring_unavailability
        )

        # Should have 3 segments: 09:00-10:00, 10:30-12:00, 13:00-17:00
        self.assertEqual(len(result), 3)

        # Verify segments
        self.assertEqual(result[0]['start'], '09:00')
        self.assertEqual(result[0]['end'], '10:00')
        self.assertEqual(result[1]['start'], '10:30')
        self.assertEqual(result[1]['end'], '12:00')
        self.assertEqual(result[2]['start'], '13:00')
        self.assertEqual(result[2]['end'], '17:00')


class MeetingGapTest(TestCase):
    """Test meeting gap configuration."""

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

        self.service = AvailabilityService()

    def test_minimum_gap_enforcement(self):
        """Test that minimum gap between meetings is enforced."""
        profile = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff Availability",
            owner_type="staff",
            owner_staff_user=self.staff_user,
            timezone="UTC",
            weekly_hours={},
            exceptions=[],
            min_notice_minutes=0,
            max_future_days=30,
            slot_rounding_minutes=30,
            min_gap_between_meetings_minutes=15,  # Require 15-minute gap
            created_by=self.user,
        )

        # Create an existing appointment
        existing_start = timezone.now() + timedelta(hours=2)
        existing_end = existing_start + timedelta(minutes=30)

        Appointment.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            staff_user=self.staff_user,
            start_time=existing_start,
            end_time=existing_end,
            status="confirmed",
            booked_by=self.user,
        )

        # Try to book immediately after (should fail due to min gap)
        proposed_start = existing_end
        proposed_end = proposed_start + timedelta(minutes=30)

        has_conflict = self.service._has_conflict(
            staff_user=self.staff_user,
            start_time=proposed_start,
            end_time=proposed_end,
            appointment_type=self.appointment_type,
            profile=profile,
        )

        self.assertTrue(has_conflict, "Should detect insufficient gap")

        # Try to book with 15-minute gap (should succeed)
        proposed_start = existing_end + timedelta(minutes=15)
        proposed_end = proposed_start + timedelta(minutes=30)

        has_conflict = self.service._has_conflict(
            staff_user=self.staff_user,
            start_time=proposed_start,
            end_time=proposed_end,
            appointment_type=self.appointment_type,
            profile=profile,
        )

        self.assertFalse(has_conflict, "Should allow sufficient gap")

    def test_back_to_back_allowed(self):
        """Test that back-to-back meetings are allowed when min_gap=0."""
        profile = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff Availability",
            owner_type="staff",
            owner_staff_user=self.staff_user,
            timezone="UTC",
            weekly_hours={},
            exceptions=[],
            min_notice_minutes=0,
            max_future_days=30,
            slot_rounding_minutes=30,
            min_gap_between_meetings_minutes=0,  # Allow back-to-back
            created_by=self.user,
        )

        # Create an existing appointment
        existing_start = timezone.now() + timedelta(hours=2)
        existing_end = existing_start + timedelta(minutes=30)

        Appointment.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            staff_user=self.staff_user,
            start_time=existing_start,
            end_time=existing_end,
            status="confirmed",
            booked_by=self.user,
        )

        # Try to book immediately after (should succeed)
        proposed_start = existing_end
        proposed_end = proposed_start + timedelta(minutes=30)

        has_conflict = self.service._has_conflict(
            staff_user=self.staff_user,
            start_time=proposed_start,
            end_time=proposed_end,
            appointment_type=self.appointment_type,
            profile=profile,
        )

        self.assertFalse(has_conflict, "Should allow back-to-back meetings")
