"""
TEAM-1: Collective Events Tests.

Tests for collective event functionality including:
- Venn diagram availability logic (overlapping availability for all required hosts)
- Multi-host support (2-10 hosts per event)
- Host substitution workflow
- Required vs optional host configuration
"""

from datetime import date, datetime, timedelta

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from modules.calendar.models import Appointment, AppointmentType, AvailabilityProfile
from modules.calendar.services import AvailabilityService, BookingService
from modules.firm.models import Firm

User = get_user_model()


class CollectiveEventAvailabilityTest(TestCase):
    """Test collective event Venn diagram availability logic (TEAM-1)."""

    def setUp(self):
        """Set up test fixtures for collective events."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Create 3 staff users for collective events
        self.staff1 = User.objects.create_user(username="staff1", password="testpass")
        self.staff2 = User.objects.create_user(username="staff2", password="testpass")
        self.staff3 = User.objects.create_user(username="staff3", password="testpass")

        # Create collective appointment type
        self.collective_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Collective Strategy Session",
            event_category="collective",
            duration_minutes=60,
            buffer_before_minutes=0,
            buffer_after_minutes=0,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        # Add required hosts
        self.collective_type.required_hosts.set([self.staff1, self.staff2])
        # Add optional host
        self.collective_type.optional_hosts.set([self.staff3])

        # Create availability profiles for all staff
        # Staff1: Available Monday 9-17
        self.profile1 = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff1 Availability",
            owner_type="staff",
            owner_staff_user=self.staff1,
            timezone="America/New_York",
            weekly_hours={
                "monday": [{"start": "09:00", "end": "17:00"}],
                "tuesday": [{"start": "09:00", "end": "17:00"}],
            },
            exceptions=[],
            min_notice_minutes=60,
            max_future_days=30,
            slot_rounding_minutes=60,
            created_by=self.user,
        )

        # Staff2: Available Monday 10-18 (1 hour offset from Staff1)
        self.profile2 = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff2 Availability",
            owner_type="staff",
            owner_staff_user=self.staff2,
            timezone="America/New_York",
            weekly_hours={
                "monday": [{"start": "10:00", "end": "18:00"}],
                "tuesday": [{"start": "09:00", "end": "17:00"}],
            },
            exceptions=[],
            min_notice_minutes=60,
            max_future_days=30,
            slot_rounding_minutes=60,
            created_by=self.user,
        )

        # Staff3 (optional): Available Monday 11-19
        self.profile3 = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff3 Availability",
            owner_type="staff",
            owner_staff_user=self.staff3,
            timezone="America/New_York",
            weekly_hours={
                "monday": [{"start": "11:00", "end": "19:00"}],
                "tuesday": [{"start": "09:00", "end": "17:00"}],
            },
            exceptions=[],
            min_notice_minutes=60,
            max_future_days=30,
            slot_rounding_minutes=60,
            created_by=self.user,
        )

    def test_overlapping_availability_two_required_hosts(self):
        """Test that collective events only show slots where ALL required hosts are available."""
        service = AvailabilityService()
        
        # Get collective slots for a Monday in the future
        start_date = date(2025, 12, 15)  # A Monday
        end_date = date(2025, 12, 15)

        slots_with_hosts = service.compute_collective_available_slots(
            appointment_type=self.collective_type,
            start_date=start_date,
            end_date=end_date,
        )

        # Staff1 available: 9-17
        # Staff2 available: 10-18
        # Overlap: 10-17 (7 hours = 7 slots with 60min duration)
        # Expected slots: 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00
        self.assertGreater(len(slots_with_hosts), 0, "Should find overlapping slots")

        # Verify all slots are within the overlap window (10:00-17:00)
        for start_time, end_time, hosts in slots_with_hosts:
            start_ny = start_time.astimezone(pytz.timezone("America/New_York"))
            end_ny = end_time.astimezone(pytz.timezone("America/New_York"))
            
            # Should start at or after 10:00
            self.assertGreaterEqual(start_ny.hour, 10)
            # Should end at or before 17:00
            self.assertLessEqual(end_ny.hour, 17)
            
            # Should include both required hosts
            host_ids = [h.id for h in hosts]
            self.assertIn(self.staff1.id, host_ids)
            self.assertIn(self.staff2.id, host_ids)

    def test_optional_host_included_when_available(self):
        """Test that optional hosts are included in slots when they're available."""
        service = AvailabilityService()
        
        start_date = date(2025, 12, 15)  # A Monday
        end_date = date(2025, 12, 15)

        slots_with_hosts = service.compute_collective_available_slots(
            appointment_type=self.collective_type,
            start_date=start_date,
            end_date=end_date,
        )

        # Staff3 (optional) available: 11-19
        # For slots at 11:00 and later, staff3 should be included
        slots_with_optional = [
            (start, end, hosts) for start, end, hosts in slots_with_hosts
            if self.staff3 in hosts
        ]

        self.assertGreater(len(slots_with_optional), 0, "Should find slots with optional host")

        # Verify optional host is only in slots where they're available
        for start_time, end_time, hosts in slots_with_optional:
            start_ny = start_time.astimezone(pytz.timezone("America/New_York"))
            # Staff3 available from 11:00
            self.assertGreaterEqual(start_ny.hour, 11)

    def test_no_slots_when_required_host_unavailable(self):
        """Test that no slots are returned if a required host has no availability."""
        # Create a new collective type with a host that has no profile
        staff_no_profile = User.objects.create_user(username="staff_no_profile", password="testpass")
        
        collective_type_no_avail = AppointmentType.objects.create(
            firm=self.firm,
            name="Collective With Unavailable Host",
            event_category="collective",
            duration_minutes=60,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        # Add required host with no availability profile
        collective_type_no_avail.required_hosts.set([self.staff1, staff_no_profile])

        service = AvailabilityService()
        start_date = date(2025, 12, 15)
        end_date = date(2025, 12, 15)

        slots_with_hosts = service.compute_collective_available_slots(
            appointment_type=collective_type_no_avail,
            start_date=start_date,
            end_date=end_date,
        )

        # Should return empty list since one required host has no profile
        self.assertEqual(len(slots_with_hosts), 0)


class CollectiveEventBookingTest(TestCase):
    """Test collective event booking functionality (TEAM-1)."""

    def setUp(self):
        """Set up test fixtures for collective event booking."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Create 2 staff users
        self.staff1 = User.objects.create_user(username="staff1", password="testpass")
        self.staff2 = User.objects.create_user(username="staff2", password="testpass")

        # Create collective appointment type
        self.collective_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Collective Meeting",
            event_category="collective",
            duration_minutes=60,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        self.collective_type.required_hosts.set([self.staff1, self.staff2])

    def test_book_collective_appointment(self):
        """Test booking a collective event with multiple hosts."""
        service = BookingService()
        
        start_time = timezone.make_aware(
            datetime(2025, 12, 15, 10, 0, 0),
            pytz.timezone("America/New_York")
        )
        end_time = start_time + timedelta(minutes=60)

        appointment = service.book_collective_appointment(
            appointment_type=self.collective_type,
            start_time=start_time,
            end_time=end_time,
            collective_hosts=[self.staff1, self.staff2],
            booked_by=self.user,
        )

        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.appointment_type, self.collective_type)
        self.assertEqual(appointment.status, "confirmed")
        
        # Verify both hosts are assigned
        collective_host_ids = [h.id for h in appointment.collective_hosts.all()]
        self.assertIn(self.staff1.id, collective_host_ids)
        self.assertIn(self.staff2.id, collective_host_ids)

    def test_book_collective_prevents_double_booking(self):
        """Test that collective booking prevents conflicts for all hosts."""
        service = BookingService()
        
        start_time = timezone.make_aware(
            datetime(2025, 12, 15, 10, 0, 0),
            pytz.timezone("America/New_York")
        )
        end_time = start_time + timedelta(minutes=60)

        # Book first appointment
        appointment1 = service.book_collective_appointment(
            appointment_type=self.collective_type,
            start_time=start_time,
            end_time=end_time,
            collective_hosts=[self.staff1, self.staff2],
            booked_by=self.user,
        )

        # Try to book overlapping appointment
        with self.assertRaises(ValueError) as context:
            service.book_collective_appointment(
                appointment_type=self.collective_type,
                start_time=start_time,
                end_time=end_time,
                collective_hosts=[self.staff1, self.staff2],
                booked_by=self.user,
            )

        self.assertIn("conflict", str(context.exception).lower())


class CollectiveEventHostSubstitutionTest(TestCase):
    """Test host substitution functionality for collective events (TEAM-1)."""

    def setUp(self):
        """Set up test fixtures for host substitution."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Create 3 staff users
        self.staff1 = User.objects.create_user(username="staff1", password="testpass")
        self.staff2 = User.objects.create_user(username="staff2", password="testpass")
        self.staff3 = User.objects.create_user(username="staff3", password="testpass")

        # Create collective appointment type
        self.collective_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Collective Meeting",
            event_category="collective",
            duration_minutes=60,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        self.collective_type.required_hosts.set([self.staff1, self.staff2])

        # Create a collective appointment
        start_time = timezone.make_aware(
            datetime(2025, 12, 15, 10, 0, 0),
            pytz.timezone("America/New_York")
        )
        end_time = start_time + timedelta(minutes=60)

        booking_service = BookingService()
        self.appointment = booking_service.book_collective_appointment(
            appointment_type=self.collective_type,
            start_time=start_time,
            end_time=end_time,
            collective_hosts=[self.staff1, self.staff2],
            booked_by=self.user,
        )

    def test_substitute_host_successfully(self):
        """Test successfully substituting a host in a collective event."""
        service = BookingService()
        
        # Substitute staff2 with staff3
        updated_appointment = service.substitute_collective_host(
            appointment=self.appointment,
            old_host=self.staff2,
            new_host=self.staff3,
            substituted_by=self.user,
            reason="Staff2 unavailable",
        )

        # Verify staff2 is removed and staff3 is added
        collective_host_ids = [h.id for h in updated_appointment.collective_hosts.all()]
        self.assertNotIn(self.staff2.id, collective_host_ids)
        self.assertIn(self.staff3.id, collective_host_ids)
        self.assertIn(self.staff1.id, collective_host_ids)

    def test_substitute_host_with_conflict_fails(self):
        """Test that substitution fails if new host has a conflict."""
        service = BookingService()
        
        # Create a conflicting appointment for staff3
        start_time = self.appointment.start_time
        end_time = self.appointment.end_time
        
        Appointment.objects.create(
            firm=self.firm,
            appointment_type=self.collective_type,
            staff_user=self.staff3,
            start_time=start_time,
            end_time=end_time,
            status="confirmed",
            booked_by=self.user,
        )

        # Try to substitute staff2 with staff3 (who has a conflict)
        with self.assertRaises(ValueError) as context:
            service.substitute_collective_host(
                appointment=self.appointment,
                old_host=self.staff2,
                new_host=self.staff3,
                substituted_by=self.user,
            )

        self.assertIn("conflict", str(context.exception).lower())

    def test_substitute_non_collective_event_fails(self):
        """Test that substitution fails for non-collective events."""
        # Create a regular one-on-one appointment
        one_on_one_type = AppointmentType.objects.create(
            firm=self.firm,
            name="One-on-One",
            event_category="one_on_one",
            duration_minutes=30,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )

        start_time = timezone.make_aware(
            datetime(2025, 12, 16, 10, 0, 0),
            pytz.timezone("America/New_York")
        )
        
        appointment = Appointment.objects.create(
            firm=self.firm,
            appointment_type=one_on_one_type,
            staff_user=self.staff1,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
            status="confirmed",
            booked_by=self.user,
        )

        service = BookingService()
        
        with self.assertRaises(ValueError) as context:
            service.substitute_collective_host(
                appointment=appointment,
                old_host=self.staff1,
                new_host=self.staff2,
                substituted_by=self.user,
            )

        self.assertIn("collective", str(context.exception).lower())
