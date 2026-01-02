"""
Calendar Tests.

Tests slot calculation, DST handling, race conditions, permissions, and routing.
Implements docs/34 section 8 testing requirements.
"""

from datetime import date, datetime, timedelta

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from modules.calendar.models import Appointment, AppointmentType, AvailabilityProfile
from modules.calendar.services import AvailabilityService, BookingService, RoutingService
from modules.firm.models import Firm

User = get_user_model()


class SlotCalculationTest(TestCase):
    """Test slot calculation correctness with buffers and exceptions per docs/34 section 8."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.staff_user = User.objects.create_user(username="staff", password="testpass")

        self.appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="30-min Consultation",
            duration_minutes=30,
            buffer_before_minutes=10,
            buffer_after_minutes=10,
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
            timezone="America/New_York",
            weekly_hours={
                "monday": [{"start": "09:00", "end": "17:00"}],
                "tuesday": [{"start": "09:00", "end": "17:00"}],
                "wednesday": [{"start": "09:00", "end": "17:00"}],
            },
            exceptions=[],
            min_notice_minutes=60,
            max_future_days=30,
            slot_rounding_minutes=15,
            created_by=self.user,
        )

    def test_slot_calculation_with_buffers(self):
        """Test that buffers prevent overlapping appointments."""
        service = AvailabilityService()

        # Create an existing appointment at 10:00-10:30
        existing_start = timezone.make_aware(datetime(2025, 12, 15, 10, 0, 0), pytz.timezone("America/New_York"))
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

        # Get available slots for that day
        start_date = date(2025, 12, 15)
        end_date = date(2025, 12, 15)

        slots = service.compute_available_slots(
            profile=self.profile,
            appointment_type=self.appointment_type,
            start_date=start_date,
            end_date=end_date,
            staff_user=self.staff_user,
        )

        # Verify that slots respect buffers
        # Existing appointment: 10:00-10:30 with 10min before/after buffers = 09:50-10:40 blocked
        # So 09:00, 09:15, 09:30, 09:45 should be blocked (would conflict with buffer)
        # First available should be 11:00 or later

        for start, end in slots:
            # Convert to NY timezone for comparison
            start_ny = start.astimezone(pytz.timezone("America/New_York"))
            end_ny = end.astimezone(pytz.timezone("America/New_York"))

            # Should not overlap with buffered range (09:50-10:40)
            buffered_start = existing_start - timedelta(minutes=10)
            buffered_end = existing_end + timedelta(minutes=10)

            self.assertFalse(
                start < buffered_end and end > buffered_start,
                f"Slot {start_ny}-{end_ny} overlaps with buffered appointment",
            )

    def test_exception_dates_excluded(self):
        """Test that exception dates are excluded from availability."""
        # Add an exception for a specific date
        exception_date = date(2025, 12, 16)
        self.profile.exceptions = [{"date": exception_date.strftime("%Y-%m-%d"), "reason": "Holiday"}]
        self.profile.save()

        service = AvailabilityService()

        # Get slots for the exception date
        slots = service.compute_available_slots(
            profile=self.profile,
            appointment_type=self.appointment_type,
            start_date=exception_date,
            end_date=exception_date,
            staff_user=self.staff_user,
        )

        # Should be no slots on exception date
        self.assertEqual(len(slots), 0)


class DSTBehaviorTest(TestCase):
    """Test DST boundary behavior per docs/34 section 8."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.staff_user = User.objects.create_user(username="staff", password="testpass")

        self.appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="30-min Consultation",
            duration_minutes=30,
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff_user,
            created_by=self.user,
        )

        # Profile in timezone with DST
        self.profile = AvailabilityProfile.objects.create(
            firm=self.firm,
            name="Staff Availability",
            owner_type="staff",
            owner_staff_user=self.staff_user,
            timezone="America/New_York",  # Has DST
            weekly_hours={
                "sunday": [{"start": "09:00", "end": "17:00"}],
                "monday": [{"start": "09:00", "end": "17:00"}],
            },
            min_notice_minutes=0,  # Allow immediate booking for testing
            max_future_days=365,
            slot_rounding_minutes=30,
            created_by=self.user,
        )

    def test_dst_transition(self):
        """Test that slots are correctly computed across DST transitions."""
        service = AvailabilityService()

        # DST begins in spring (March): clocks spring forward
        # DST ends in fall (November): clocks fall back
        # Test around November 2025 DST transition (first Sunday of November)

        # Get slots before and after DST transition
        start_date = date(2025, 11, 1)  # Before DST ends
        end_date = date(2025, 11, 3)  # After DST ends

        slots = service.compute_available_slots(
            profile=self.profile,
            appointment_type=self.appointment_type,
            start_date=start_date,
            end_date=end_date,
            staff_user=self.staff_user,
        )

        # Should have slots on all days (availability defined for Sunday and Monday)
        self.assertGreater(len(slots), 0, "Should have slots across DST boundary")

        # Verify slots are in UTC and correctly converted
        for start, end in slots:
            self.assertEqual(start.tzinfo, pytz.UTC, "Slots should be in UTC")
            self.assertEqual((end - start).total_seconds() / 60, 30, "Slot duration should be 30 minutes")


class RaceConditionTest(TestCase):
    """Test race condition prevention per docs/34 section 8."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user1 = User.objects.create_user(username="user1", password="testpass")
        self.user2 = User.objects.create_user(username="user2", password="testpass")
        self.staff_user = User.objects.create_user(username="staff", password="testpass")

        self.appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="30-min Consultation",
            duration_minutes=30,
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff_user,
            created_by=self.user1,
        )

    def test_double_booking_prevented(self):
        """Test that two users cannot book the same slot."""
        service = BookingService()

        # Both users try to book the same slot
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(minutes=30)

        # First booking should succeed
        appointment1 = service.book_appointment(
            appointment_type=self.appointment_type,
            start_time=start_time,
            end_time=end_time,
            staff_user=self.staff_user,
            booked_by=self.user1,
        )
        self.assertIsNotNone(appointment1)

        # Second booking should fail (conflict)
        with self.assertRaises(ValueError) as context:
            service.book_appointment(
                appointment_type=self.appointment_type,
                start_time=start_time,
                end_time=end_time,
                staff_user=self.staff_user,
                booked_by=self.user2,
            )

        self.assertIn("conflict", str(context.exception).lower())


class RoutingPolicyTest(TestCase):
    """Test routing policy determinism per docs/34 section 8."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.staff_user = User.objects.create_user(username="staff", password="testpass")

        self.appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="30-min Consultation",
            duration_minutes=30,
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff_user,
            created_by=self.user,
        )

    def test_fixed_staff_routing_determinism(self):
        """Test that fixed_staff routing always returns the same user."""
        service = RoutingService()

        # Run routing multiple times
        results = [service.route_appointment(self.appointment_type) for _ in range(5)]

        # All results should be identical
        staff_users = [r[0] for r in results]
        self.assertTrue(all(user == self.staff_user for user in staff_users))


class ApprovalFlowTest(TestCase):
    """Test approval-required flow correctness per docs/34 section 8."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.staff_user = User.objects.create_user(username="staff", password="testpass")

        self.appointment_type_approval = AppointmentType.objects.create(
            firm=self.firm,
            name="Requires Approval",
            duration_minutes=30,
            requires_approval=True,
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff_user,
            created_by=self.user,
        )

        self.appointment_type_auto = AppointmentType.objects.create(
            firm=self.firm,
            name="Auto Confirmed",
            duration_minutes=30,
            requires_approval=False,
            routing_policy="fixed_staff",
            fixed_staff_user=self.staff_user,
            created_by=self.user,
        )

    def test_approval_required_creates_requested_status(self):
        """Test that requires_approval creates appointment in requested status."""
        service = BookingService()

        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(minutes=30)

        appointment = service.book_appointment(
            appointment_type=self.appointment_type_approval,
            start_time=start_time,
            end_time=end_time,
            staff_user=self.staff_user,
            booked_by=self.user,
        )

        self.assertEqual(appointment.status, "requested")

    def test_no_approval_creates_confirmed_status(self):
        """Test that non-approval appointments are auto-confirmed."""
        service = BookingService()

        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(minutes=30)

        appointment = service.book_appointment(
            appointment_type=self.appointment_type_auto,
            start_time=start_time,
            end_time=end_time,
            staff_user=self.staff_user,
            booked_by=self.user,
        )

        self.assertEqual(appointment.status, "confirmed")

    def test_confirm_appointment_flow(self):
        """Test that requested appointments can be confirmed."""
        service = BookingService()

        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(minutes=30)

        # Create requested appointment
        appointment = service.book_appointment(
            appointment_type=self.appointment_type_approval,
            start_time=start_time,
            end_time=end_time,
            staff_user=self.staff_user,
            booked_by=self.user,
        )

        self.assertEqual(appointment.status, "requested")

        # Confirm it
        appointment = service.confirm_appointment(appointment, confirmed_by=self.staff_user)

        self.assertEqual(appointment.status, "confirmed")
        self.assertEqual(appointment.status_history.count(), 2)  # Initial + confirmation


class RichEventDescriptionTest(TestCase):
    """Test rich event descriptions (CAL-3)."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_create_appointment_type_with_rich_description(self):
        """Test creating an appointment type with rich HTML description."""
        rich_html = """
            <h2>What to Expect</h2>
            <p>In this <strong>60-minute session</strong>, we'll:</p>
            <ul>
                <li>Review your current business challenges</li>
                <li>Identify growth opportunities</li>
                <li>Create an actionable roadmap</li>
            </ul>
            <p>Learn more at <a href="https://example.com">our website</a></p>
        """

        appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Strategy Session",
            internal_name="STRAT-01 - Strategy Session (Premium)",
            description="Quick strategy consultation",
            rich_description=rich_html,
            duration_minutes=60,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )

        # Verify fields are saved correctly
        self.assertEqual(appointment_type.name, "Strategy Session")
        self.assertEqual(appointment_type.internal_name, "STRAT-01 - Strategy Session (Premium)")
        self.assertEqual(appointment_type.description, "Quick strategy consultation")
        self.assertIn("<h2>What to Expect</h2>", appointment_type.rich_description)
        self.assertIn("<strong>60-minute session</strong>", appointment_type.rich_description)

    def test_rich_description_fields_optional(self):
        """Test that rich description fields are optional (backward compatibility)."""
        # Create appointment type without rich fields
        appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Basic Consultation",
            description="Simple consultation",
            duration_minutes=30,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )

        # Verify it works without rich fields
        self.assertEqual(appointment_type.name, "Basic Consultation")
        self.assertEqual(appointment_type.internal_name, "")
        self.assertEqual(appointment_type.rich_description, "")
        self.assertIsNone(appointment_type.description_image.name if appointment_type.description_image else None)

    def test_internal_name_separate_from_public_name(self):
        """Test that internal name can differ from public display name."""
        appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Discovery Call",  # Public name
            internal_name="DISCO-STD-2024",  # Internal reference
            description="Initial discovery call",
            duration_minutes=15,
            location_mode="phone",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )

        self.assertEqual(appointment_type.name, "Discovery Call")
        self.assertEqual(appointment_type.internal_name, "DISCO-STD-2024")
        self.assertNotEqual(appointment_type.name, appointment_type.internal_name)


class EventCustomizationTest(TestCase):
    """Test event customization features (CAL-4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_auto_generate_slug_from_name(self):
        """Test that URL slug is auto-generated from event name if not provided."""
        appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Strategy Session",
            description="Initial strategy consultation",
            duration_minutes=60,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )

        # Slug should be auto-generated
        self.assertEqual(appointment_type.url_slug, "strategy-session")

    def test_custom_slug_preserved(self):
        """Test that custom URL slug is preserved if provided."""
        appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Strategy Session",
            url_slug="premium-strategy",
            description="Premium strategy consultation",
            duration_minutes=60,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )

        # Custom slug should be preserved
        self.assertEqual(appointment_type.url_slug, "premium-strategy")

    def test_slug_uniqueness_within_firm(self):
        """Test that URL slugs are unique within a firm."""
        # Create first event
        AppointmentType.objects.create(
            firm=self.firm,
            name="Consultation",
            description="Standard consultation",
            duration_minutes=30,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )

        # Create second event with same name
        appointment_type2 = AppointmentType.objects.create(
            firm=self.firm,
            name="Consultation",
            description="Another consultation",
            duration_minutes=45,
            location_mode="phone",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )

        # Second event should get a unique slug
        self.assertEqual(appointment_type2.url_slug, "consultation-1")

    def test_color_code_validation(self):
        """Test that color code validation works correctly."""
        from django.core.exceptions import ValidationError

        # Valid color code
        appointment_type = AppointmentType(
            firm=self.firm,
            name="Colored Event",
            color_code="#3B82F6",
            description="Event with valid color",
            duration_minutes=30,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )
        appointment_type.clean()  # Should not raise

        # Invalid color code
        appointment_type_invalid = AppointmentType(
            firm=self.firm,
            name="Bad Color Event",
            color_code="blue",
            description="Event with invalid color",
            duration_minutes=30,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            created_by=self.user,
        )

        with self.assertRaises(ValidationError) as context:
            appointment_type_invalid.clean()

        self.assertIn("color_code", context.exception.message_dict)

    def test_archived_status(self):
        """Test that archived status is available (CAL-4)."""
        appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Old Event",
            description="Event to be archived",
            duration_minutes=30,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            status="archived",
            created_by=self.user,
        )

        self.assertEqual(appointment_type.status, "archived")

    def test_availability_overrides(self):
        """Test that availability overrides can be set."""
        overrides = {
            "min_notice_minutes": 120,
            "max_future_days": 60,
            "weekly_hours": {"monday": [{"start": "10:00", "end": "14:00"}]},
        }

        appointment_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Special Event",
            description="Event with custom availability",
            duration_minutes=30,
            location_mode="video",
            routing_policy="fixed_staff",
            fixed_staff_user=self.user,
            availability_overrides=overrides,
            created_by=self.user,
        )

        self.assertEqual(appointment_type.availability_overrides["min_notice_minutes"], 120)
        self.assertEqual(appointment_type.availability_overrides["max_future_days"], 60)
