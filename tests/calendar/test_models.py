import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.calendar.models import (
    AppointmentType,
    AvailabilityProfile,
    BookingLink,
    Appointment,
)
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.fixture
def appointment_type(db, firm):
    return AppointmentType.objects.create(
        firm=firm,
        name="30-Minute Consultation",
        description="Standard consultation call",
        duration_minutes=30,
        location_mode="video",
        status="active",
        event_category="one_on_one",
    )


@pytest.mark.django_db
class TestAppointmentType:
    """Test AppointmentType model functionality"""

    def test_appointment_type_creation(self, firm):
        """Test basic appointment type creation"""
        apt_type = AppointmentType.objects.create(
            firm=firm,
            name="Discovery Call",
            description="Initial discovery call",
            duration_minutes=45,
            location_mode="video",
            status="active",
        )

        assert apt_type.name == "Discovery Call"
        assert apt_type.duration_minutes == 45
        assert apt_type.location_mode == "video"
        assert apt_type.status == "active"
        assert apt_type.event_category == "one_on_one"  # default

    def test_appointment_type_location_modes(self, firm):
        """Test different location modes"""
        location_modes = ["video", "phone", "in_person", "custom"]

        for mode in location_modes:
            apt_type = AppointmentType.objects.create(
                firm=firm, name=f"{mode} Meeting", duration_minutes=30, location_mode=mode, status="active"
            )
            assert apt_type.location_mode == mode

    def test_appointment_type_event_categories(self, firm):
        """Test different event categories"""
        categories = ["one_on_one", "group", "collective", "round_robin"]

        for category in categories:
            apt_type = AppointmentType.objects.create(
                firm=firm, name=f"{category} Event", duration_minutes=30, event_category=category, status="active"
            )
            assert apt_type.event_category == category

    def test_appointment_type_group_settings(self, firm):
        """Test group event settings"""
        apt_type = AppointmentType.objects.create(
            firm=firm,
            name="Group Webinar",
            duration_minutes=60,
            event_category="group",
            max_attendees=50,
            enable_waitlist=True,
            status="active",
        )

        assert apt_type.event_category == "group"
        assert apt_type.max_attendees == 50
        assert apt_type.enable_waitlist is True

    def test_appointment_type_status_choices(self, firm):
        """Test status choices"""
        statuses = ["active", "inactive", "archived"]

        for status in statuses:
            apt_type = AppointmentType.objects.create(
                firm=firm, name=f"Status {status}", duration_minutes=30, status=status
            )
            assert apt_type.status == status

    def test_appointment_type_rich_description(self, firm):
        """Test rich description field"""
        rich_desc = "<h1>Welcome!</h1><p>This is a <strong>formatted</strong> description.</p>"

        apt_type = AppointmentType.objects.create(
            firm=firm,
            name="Rich Event",
            duration_minutes=30,
            rich_description=rich_desc,
            internal_name="Internal Event Name",
            status="active",
        )

        assert apt_type.rich_description == rich_desc
        assert apt_type.internal_name == "Internal Event Name"


@pytest.mark.django_db
class TestAvailabilityProfile:
    """Test AvailabilityProfile model functionality"""

    def test_availability_profile_creation(self, firm, user):
        """Test basic availability profile creation"""
        profile = AvailabilityProfile.objects.create(firm=firm, name="Business Hours", owner=user, is_default=False)

        assert profile.name == "Business Hours"
        assert profile.owner == user
        assert profile.firm == firm
        assert profile.is_default is False

    def test_availability_profile_default_flag(self, firm, user):
        """Test default availability profile"""
        profile = AvailabilityProfile.objects.create(firm=firm, name="Default Schedule", owner=user, is_default=True)

        assert profile.is_default is True


@pytest.mark.django_db
class TestBookingLink:
    """Test BookingLink model functionality"""

    def test_booking_link_creation(self, firm, user, appointment_type):
        """Test basic booking link creation"""
        link = BookingLink.objects.create(
            firm=firm,
            appointment_type=appointment_type,
            slug="consultation-call",
            owner=user,
            is_active=True,
        )

        assert link.slug == "consultation-call"
        assert link.appointment_type == appointment_type
        assert link.owner == user
        assert link.is_active is True

    def test_booking_link_slug_uniqueness(self, firm, user, appointment_type):
        """Test that booking link slugs are unique per firm"""
        BookingLink.objects.create(
            firm=firm, appointment_type=appointment_type, slug="unique-slug", owner=user, is_active=True
        )

        # Creating another link with same slug should fail
        with pytest.raises(Exception):  # IntegrityError
            BookingLink.objects.create(
                firm=firm, appointment_type=appointment_type, slug="unique-slug", owner=user, is_active=True
            )

    def test_booking_link_active_status(self, firm, user, appointment_type):
        """Test booking link active/inactive status"""
        link = BookingLink.objects.create(
            firm=firm, appointment_type=appointment_type, slug="test-link", owner=user, is_active=True
        )

        assert link.is_active is True

        link.is_active = False
        link.save()

        assert link.is_active is False


@pytest.mark.django_db
class TestAppointment:
    """Test Appointment model functionality"""

    def test_appointment_creation(self, firm, user, appointment_type):
        """Test basic appointment creation"""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=appointment_type,
            host=user,
            start_time=start_time,
            end_time=end_time,
            status="scheduled",
            attendee_name="John Doe",
            attendee_email="john@example.com",
        )

        assert appointment.appointment_type == appointment_type
        assert appointment.host == user
        assert appointment.status == "scheduled"
        assert appointment.attendee_name == "John Doe"
        assert appointment.attendee_email == "john@example.com"

    def test_appointment_status_transitions(self, firm, user, appointment_type):
        """Test appointment status transitions"""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=appointment_type,
            host=user,
            start_time=start_time,
            end_time=end_time,
            status="scheduled",
            attendee_name="John Doe",
            attendee_email="john@example.com",
        )

        # Confirm appointment
        appointment.status = "confirmed"
        appointment.save()
        assert appointment.status == "confirmed"

        # Cancel appointment
        appointment.status = "cancelled"
        appointment.save()
        assert appointment.status == "cancelled"

    def test_appointment_duration(self, firm, user, appointment_type):
        """Test appointment duration calculation"""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=45)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=appointment_type,
            host=user,
            start_time=start_time,
            end_time=end_time,
            status="scheduled",
            attendee_name="John Doe",
            attendee_email="john@example.com",
        )

        duration = (appointment.end_time - appointment.start_time).total_seconds() / 60
        assert duration == 45

    def test_appointment_location_info(self, firm, user, appointment_type):
        """Test appointment location information"""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=appointment_type,
            host=user,
            start_time=start_time,
            end_time=end_time,
            status="scheduled",
            attendee_name="John Doe",
            attendee_email="john@example.com",
            location_details="https://zoom.us/j/123456789",
        )

        assert appointment.location_details == "https://zoom.us/j/123456789"

    def test_appointment_notes(self, firm, user, appointment_type):
        """Test appointment notes field"""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)

        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=appointment_type,
            host=user,
            start_time=start_time,
            end_time=end_time,
            status="scheduled",
            attendee_name="John Doe",
            attendee_email="john@example.com",
            notes="Discussed project requirements",
        )

        assert appointment.notes == "Discussed project requirements"
