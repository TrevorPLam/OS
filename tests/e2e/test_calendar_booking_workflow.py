"""
End-to-end integration tests for calendar booking workflow.

Tests complete booking flow from link creation to appointment confirmation.
"""
import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.calendar.models import (
    AppointmentType,
    BookingLink,
    Appointment,
    AvailabilityProfile,
)
from modules.clients.models import Client, Organization
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Consulting Firm", slug="consulting-firm", status="active")


@pytest.fixture
def consultant(db):
    return User.objects.create_user(username="consultant", email="consultant@firm.com", password="pass1234")


@pytest.fixture
def organization(db, firm, consultant):
    return Organization.objects.create(firm=firm, name="Client Organization", created_by=consultant)


@pytest.fixture
def client(db, firm, consultant, organization):
    return Client.objects.create(
        firm=firm,
        organization=organization,
        company_name="Client Company",
        primary_contact_name="Jane Smith",
        primary_contact_email="jane@client.com",
        status="active",
        account_manager=consultant,
    )


@pytest.mark.e2e
@pytest.mark.django_db
class TestCalendarBookingWorkflow:
    """Test complete calendar booking workflow"""

    def test_complete_booking_workflow(self, firm, consultant):
        """Test complete flow: create appointment type → booking link → schedule appointment"""

        # Step 1: Create appointment type
        apt_type = AppointmentType.objects.create(
            firm=firm,
            name="Strategy Session",
            description="60-minute strategy consultation",
            duration_minutes=60,
            location_mode="video",
            status="active",
            event_category="one_on_one",
        )

        assert apt_type.status == "active"

        # Step 2: Create availability profile
        availability = AvailabilityProfile.objects.create(
            firm=firm, name="Business Hours", owner=consultant, is_default=True
        )

        assert availability.is_default is True

        # Step 3: Create booking link
        booking_link = BookingLink.objects.create(
            firm=firm, appointment_type=apt_type, slug="strategy-session", owner=consultant, is_active=True
        )

        assert booking_link.is_active is True
        assert booking_link.slug == "strategy-session"

        # Step 4: Book appointment
        start_time = timezone.now() + timedelta(days=2)
        end_time = start_time + timedelta(minutes=60)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=apt_type,
            host=consultant,
            start_time=start_time,
            end_time=end_time,
            status="scheduled",
            attendee_name="Prospective Client",
            attendee_email="prospect@example.com",
            location_details="https://zoom.us/j/987654321",
        )

        assert appointment.status == "scheduled"
        assert appointment.host == consultant
        assert appointment.attendee_email == "prospect@example.com"

        # Step 5: Confirm appointment
        appointment.status = "confirmed"
        appointment.save()

        assert appointment.status == "confirmed"

        # Verify complete workflow
        assert Appointment.objects.filter(firm=firm, status="confirmed").count() == 1

    def test_group_event_booking_workflow(self, firm, consultant):
        """Test group event booking with multiple attendees"""

        # Create group event type
        apt_type = AppointmentType.objects.create(
            firm=firm,
            name="Group Workshop",
            description="Team workshop session",
            duration_minutes=90,
            location_mode="video",
            status="active",
            event_category="group",
            max_attendees=20,
            enable_waitlist=True,
        )

        # Create booking link
        booking_link = BookingLink.objects.create(
            firm=firm, appointment_type=apt_type, slug="workshop", owner=consultant, is_active=True
        )

        # Book group appointment
        start_time = timezone.now() + timedelta(days=3)
        end_time = start_time + timedelta(minutes=90)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=apt_type,
            host=consultant,
            start_time=start_time,
            end_time=end_time,
            status="scheduled",
            attendee_name="Group Event",
            attendee_email="group@example.com",
        )

        # Verify group settings
        assert appointment.appointment_type.event_category == "group"
        assert appointment.appointment_type.max_attendees == 20
        assert appointment.appointment_type.enable_waitlist is True

    def test_appointment_cancellation_workflow(self, firm, consultant):
        """Test appointment cancellation flow"""

        # Create appointment type and booking
        apt_type = AppointmentType.objects.create(
            firm=firm,
            name="Consultation",
            duration_minutes=30,
            location_mode="video",
            status="active",
        )

        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=apt_type,
            host=consultant,
            start_time=start_time,
            end_time=end_time,
            status="scheduled",
            attendee_name="Test User",
            attendee_email="test@example.com",
        )

        # Cancel appointment
        appointment.status = "cancelled"
        appointment.save()

        assert appointment.status == "cancelled"

        # Verify cancellation
        cancelled_appointments = Appointment.objects.filter(firm=firm, status="cancelled")
        assert cancelled_appointments.count() == 1

    def test_appointment_rescheduling_workflow(self, firm, consultant):
        """Test appointment rescheduling flow"""

        # Create appointment
        apt_type = AppointmentType.objects.create(
            firm=firm,
            name="Follow-up Call",
            duration_minutes=30,
            location_mode="phone",
            status="active",
        )

        original_start = timezone.now() + timedelta(days=1)
        original_end = original_start + timedelta(minutes=30)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=apt_type,
            host=consultant,
            start_time=original_start,
            end_time=original_end,
            status="scheduled",
            attendee_name="Client Name",
            attendee_email="client@example.com",
        )

        # Reschedule to new time
        new_start = timezone.now() + timedelta(days=2)
        new_end = new_start + timedelta(minutes=30)

        appointment.start_time = new_start
        appointment.end_time = new_end
        appointment.save()

        assert appointment.start_time == new_start
        assert appointment.end_time == new_end

    def test_multi_host_round_robin_workflow(self, firm, consultant, db):
        """Test round-robin appointment distribution"""

        # Create additional consultants
        consultant2 = User.objects.create_user(username="consultant2", email="c2@firm.com", password="pass")
        consultant3 = User.objects.create_user(username="consultant3", email="c3@firm.com", password="pass")

        # Create round-robin appointment type
        apt_type = AppointmentType.objects.create(
            firm=firm,
            name="Sales Call",
            duration_minutes=30,
            location_mode="video",
            status="active",
            event_category="round_robin",
        )

        # Book appointments with different hosts (simulating round-robin distribution)
        appointments = []
        hosts = [consultant, consultant2, consultant3]

        for i, host in enumerate(hosts):
            start_time = timezone.now() + timedelta(days=i + 1)
            end_time = start_time + timedelta(minutes=30)

            appointment = Appointment.objects.create(
                firm=firm,
                appointment_type=apt_type,
                host=host,
                start_time=start_time,
                end_time=end_time,
                status="scheduled",
                attendee_name=f"Client {i+1}",
                attendee_email=f"client{i+1}@example.com",
            )
            appointments.append(appointment)

        # Verify distribution
        assert len(appointments) == 3
        assert len(set(a.host for a in appointments)) == 3  # All different hosts
