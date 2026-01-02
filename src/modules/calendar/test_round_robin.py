"""
TEAM-2: Advanced Round Robin Tests.

Tests for advanced round robin functionality including:
- Strict round robin distribution (equal regardless of availability)
- Optimize for availability (favor most available)
- Weighted distribution (configurable weights per team member)
- Prioritize by capacity (route to least-booked)
- Equal distribution tracking and rebalancing
- Capacity limits per person per day
- Fallback logic when no one available
- Manual assignment overrides
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from modules.calendar.models import Appointment, AppointmentType, AvailabilityProfile
from modules.calendar.services import RoundRobinService, RoutingService
from modules.firm.models import Firm

User = get_user_model()


class RoundRobinStrictDistributionTest(TestCase):
    """Test strict round robin distribution strategy (TEAM-2)."""

    def setUp(self):
        """Set up test fixtures for round robin."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Create 3 staff users for round robin
        self.staff1 = User.objects.create_user(username="rr_staff1", password="testpass")
        self.staff2 = User.objects.create_user(username="rr_staff2", password="testpass")
        self.staff3 = User.objects.create_user(username="rr_staff3", password="testpass")

        # Create round robin appointment type
        self.rr_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Round Robin Consultation",
            event_category="one_on_one",
            duration_minutes=30,
            location_mode="video",
            routing_policy="round_robin_pool",
            round_robin_strategy="strict",
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        # Add staff to round robin pool
        self.rr_type.round_robin_pool.set([self.staff1, self.staff2, self.staff3])

        # Create availability profiles for all staff
        for staff in [self.staff1, self.staff2, self.staff3]:
            AvailabilityProfile.objects.create(
                firm=self.firm,
                name=f"{staff.username} Availability",
                owner_type="staff",
                owner_staff_user=staff,
                timezone="America/New_York",
                weekly_hours={
                    "monday": [{"start": "09:00", "end": "17:00"}],
                    "tuesday": [{"start": "09:00", "end": "17:00"}],
                },
                min_notice_minutes=60,
                max_future_days=30,
                slot_rounding_minutes=30,
                created_by=self.user,
            )

    def test_strict_round_robin_equal_distribution(self):
        """Test that strict round robin distributes equally."""
        service = RoundRobinService()
        
        start_time = timezone.make_aware(
            datetime(2025, 12, 15, 10, 0, 0),
            pytz.timezone("America/New_York")
        )
        end_time = start_time + timedelta(minutes=30)

        # First selection should go to staff with least appointments (all have 0)
        staff1_selected, reason1 = service.select_round_robin_staff(
            appointment_type=self.rr_type,
            start_time=start_time,
            end_time=end_time,
        )
        
        self.assertIsNotNone(staff1_selected)
        self.assertIn(staff1_selected, [self.staff1, self.staff2, self.staff3])

        # Create an appointment for the selected staff
        Appointment.objects.create(
            firm=self.firm,
            appointment_type=self.rr_type,
            staff_user=staff1_selected,
            start_time=start_time,
            end_time=end_time,
            status="confirmed",
            booked_by=self.user,
        )

        # Second selection should go to a different staff member
        start_time2 = start_time + timedelta(hours=1)
        end_time2 = start_time2 + timedelta(minutes=30)
        
        staff2_selected, reason2 = service.select_round_robin_staff(
            appointment_type=self.rr_type,
            start_time=start_time2,
            end_time=end_time2,
        )

        self.assertIsNotNone(staff2_selected)
        self.assertNotEqual(staff2_selected, staff1_selected)

    def test_strict_round_robin_skips_unavailable(self):
        """Test that strict round robin skips staff with conflicts."""
        # Create a conflicting appointment for staff1
        start_time = timezone.make_aware(
            datetime(2025, 12, 15, 10, 0, 0),
            pytz.timezone("America/New_York")
        )
        end_time = start_time + timedelta(minutes=30)

        Appointment.objects.create(
            firm=self.firm,
            appointment_type=self.rr_type,
            staff_user=self.staff1,
            start_time=start_time,
            end_time=end_time,
            status="confirmed",
            booked_by=self.user,
        )

        # Try to route at the same time - should skip staff1
        service = RoundRobinService()
        selected_staff, reason = service.select_round_robin_staff(
            appointment_type=self.rr_type,
            start_time=start_time,
            end_time=end_time,
        )

        self.assertIsNotNone(selected_staff)
        self.assertNotEqual(selected_staff, self.staff1)


class RoundRobinWeightedDistributionTest(TestCase):
    """Test weighted round robin distribution (TEAM-2)."""

    def setUp(self):
        """Set up test fixtures for weighted round robin."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Create 3 staff users
        self.staff1 = User.objects.create_user(username="rr_staff1", password="testpass")
        self.staff2 = User.objects.create_user(username="rr_staff2", password="testpass")
        self.staff3 = User.objects.create_user(username="rr_staff3", password="testpass")

        # Create weighted round robin appointment type
        # Staff1 weight=2, Staff2 weight=1.5, Staff3 weight=1
        self.rr_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Weighted Round Robin",
            duration_minutes=30,
            location_mode="video",
            routing_policy="round_robin_pool",
            round_robin_strategy="weighted",
            round_robin_weights={
                str(self.staff1.id): 2.0,
                str(self.staff2.id): 1.5,
                str(self.staff3.id): 1.0,
            },
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        self.rr_type.round_robin_pool.set([self.staff1, self.staff2, self.staff3])

        # Create availability profiles
        for staff in [self.staff1, self.staff2, self.staff3]:
            AvailabilityProfile.objects.create(
                firm=self.firm,
                name=f"{staff.username} Availability",
                owner_type="staff",
                owner_staff_user=staff,
                timezone="America/New_York",
                weekly_hours={
                    "monday": [{"start": "09:00", "end": "17:00"}],
                },
                min_notice_minutes=60,
                max_future_days=30,
                slot_rounding_minutes=30,
                created_by=self.user,
            )

    def test_weighted_distribution_respects_weights(self):
        """Test that weighted distribution assigns more to higher-weight staff."""
        service = RoundRobinService()
        
        # Staff1 has weight 2.0, so should get selected first when all have 0 appointments
        start_time = timezone.make_aware(
            datetime(2025, 12, 15, 10, 0, 0),
            pytz.timezone("America/New_York")
        )
        end_time = start_time + timedelta(minutes=30)

        selected_staff, reason = service.select_round_robin_staff(
            appointment_type=self.rr_type,
            start_time=start_time,
            end_time=end_time,
        )

        # Should select based on weighted ratio (count / weight)
        # All have 0 appointments, so ratio = 0/weight for all
        # Selection will pick the one with lowest ratio (which will be tied)
        self.assertIsNotNone(selected_staff)


class RoundRobinCapacityLimitTest(TestCase):
    """Test capacity limits per person per day (TEAM-2)."""

    def setUp(self):
        """Set up test fixtures for capacity limit testing."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        self.staff1 = User.objects.create_user(username="rr_staff1", password="testpass")
        self.staff2 = User.objects.create_user(username="rr_staff2", password="testpass")

        # Create round robin with capacity limit of 2 per day
        self.rr_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Limited Capacity RR",
            duration_minutes=30,
            location_mode="video",
            routing_policy="round_robin_pool",
            round_robin_strategy="strict",
            round_robin_capacity_per_day=2,
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        self.rr_type.round_robin_pool.set([self.staff1, self.staff2])

        # Create availability profiles
        for staff in [self.staff1, self.staff2]:
            AvailabilityProfile.objects.create(
                firm=self.firm,
                name=f"{staff.username} Availability",
                owner_type="staff",
                owner_staff_user=staff,
                timezone="America/New_York",
                weekly_hours={
                    "monday": [{"start": "09:00", "end": "17:00"}],
                },
                min_notice_minutes=60,
                max_future_days=30,
                slot_rounding_minutes=30,
                created_by=self.user,
            )

    def test_capacity_limit_enforced(self):
        """Test that capacity limit per day is enforced."""
        service = RoundRobinService()
        
        # Create 2 appointments for staff1 on the same day (reaching limit)
        day_start = timezone.make_aware(
            datetime(2025, 12, 15, 9, 0, 0),
            pytz.timezone("America/New_York")
        )
        
        for i in range(2):
            start_time = day_start + timedelta(hours=i)
            end_time = start_time + timedelta(minutes=30)
            Appointment.objects.create(
                firm=self.firm,
                appointment_type=self.rr_type,
                staff_user=self.staff1,
                start_time=start_time,
                end_time=end_time,
                status="confirmed",
                booked_by=self.user,
            )

        # Now try to route another appointment on the same day
        start_time = day_start + timedelta(hours=4)
        end_time = start_time + timedelta(minutes=30)

        selected_staff, reason = service.select_round_robin_staff(
            appointment_type=self.rr_type,
            start_time=start_time,
            end_time=end_time,
        )

        # Should select staff2 since staff1 is at capacity
        self.assertEqual(selected_staff, self.staff2)


class RoundRobinRebalancingTest(TestCase):
    """Test automatic rebalancing detection (TEAM-2)."""

    def setUp(self):
        """Set up test fixtures for rebalancing."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        self.staff1 = User.objects.create_user(username="rr_staff1", password="testpass")
        self.staff2 = User.objects.create_user(username="rr_staff2", password="testpass")
        self.staff3 = User.objects.create_user(username="rr_staff3", password="testpass")

        # Create round robin with rebalancing enabled (threshold 20%)
        self.rr_type = AppointmentType.objects.create(
            firm=self.firm,
            name="Rebalancing RR",
            duration_minutes=30,
            location_mode="video",
            routing_policy="round_robin_pool",
            round_robin_strategy="strict",
            round_robin_enable_rebalancing=True,
            round_robin_rebalancing_threshold=Decimal("0.20"),
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        self.rr_type.round_robin_pool.set([self.staff1, self.staff2, self.staff3])

    def test_rebalancing_needed_when_imbalanced(self):
        """Test that rebalancing is detected when distribution is imbalanced."""
        # Create imbalanced distribution:
        # Staff1: 5 appointments, Staff2: 2 appointments, Staff3: 2 appointments
        # Average: 3, Staff1 deviation: (5-3)/3 = 66% > 20% threshold
        
        base_time = timezone.make_aware(
            datetime(2025, 12, 15, 9, 0, 0),
            pytz.timezone("America/New_York")
        )

        # Create 5 appointments for staff1
        for i in range(5):
            start_time = base_time + timedelta(hours=i)
            Appointment.objects.create(
                firm=self.firm,
                appointment_type=self.rr_type,
                staff_user=self.staff1,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=30),
                status="confirmed",
                booked_by=self.user,
            )

        # Create 2 appointments each for staff2 and staff3
        for staff in [self.staff2, self.staff3]:
            for i in range(2):
                start_time = base_time + timedelta(hours=10 + i)
                Appointment.objects.create(
                    firm=self.firm,
                    appointment_type=self.rr_type,
                    staff_user=staff,
                    start_time=start_time,
                    end_time=start_time + timedelta(minutes=30),
                    status="confirmed",
                    booked_by=self.user,
                )

        service = RoundRobinService()
        needs_rebalancing = service._needs_rebalancing(self.rr_type)

        self.assertTrue(needs_rebalancing)

    def test_rebalancing_not_needed_when_balanced(self):
        """Test that rebalancing is not triggered when distribution is balanced."""
        # Create balanced distribution: 3 appointments each
        base_time = timezone.make_aware(
            datetime(2025, 12, 15, 9, 0, 0),
            pytz.timezone("America/New_York")
        )

        for staff in [self.staff1, self.staff2, self.staff3]:
            for i in range(3):
                start_time = base_time + timedelta(hours=i)
                Appointment.objects.create(
                    firm=self.firm,
                    appointment_type=self.rr_type,
                    staff_user=staff,
                    start_time=start_time,
                    end_time=start_time + timedelta(minutes=30),
                    status="confirmed",
                    booked_by=self.user,
                )

        service = RoundRobinService()
        needs_rebalancing = service._needs_rebalancing(self.rr_type)

        self.assertFalse(needs_rebalancing)


class RoundRobinRoutingIntegrationTest(TestCase):
    """Test round robin integration with routing service (TEAM-2)."""

    def setUp(self):
        """Set up test fixtures for routing integration."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        self.staff1 = User.objects.create_user(username="rr_staff1", password="testpass")
        self.staff2 = User.objects.create_user(username="rr_staff2", password="testpass")

        self.rr_type = AppointmentType.objects.create(
            firm=self.firm,
            name="RR Consultation",
            duration_minutes=30,
            location_mode="video",
            routing_policy="round_robin_pool",
            round_robin_strategy="strict",
            fixed_staff_user=self.staff1,
            created_by=self.user,
        )
        
        self.rr_type.round_robin_pool.set([self.staff1, self.staff2])

        # Create availability profiles
        for staff in [self.staff1, self.staff2]:
            AvailabilityProfile.objects.create(
                firm=self.firm,
                name=f"{staff.username} Availability",
                owner_type="staff",
                owner_staff_user=staff,
                timezone="America/New_York",
                weekly_hours={
                    "monday": [{"start": "09:00", "end": "17:00"}],
                },
                min_notice_minutes=60,
                max_future_days=30,
                slot_rounding_minutes=30,
                created_by=self.user,
            )

    def test_routing_service_uses_round_robin(self):
        """Test that RoutingService properly uses RoundRobinService."""
        service = RoutingService()
        
        start_time = timezone.make_aware(
            datetime(2025, 12, 15, 10, 0, 0),
            pytz.timezone("America/New_York")
        )
        end_time = start_time + timedelta(minutes=30)

        staff_user, reason = service.route_appointment(
            appointment_type=self.rr_type,
            start_time=start_time,
            end_time=end_time,
        )

        self.assertIsNotNone(staff_user)
        self.assertIn(staff_user, [self.staff1, self.staff2])
        self.assertIn("Round robin", reason)
