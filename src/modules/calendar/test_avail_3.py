"""
Tests for AVAIL-3: Advanced availability features.

Tests secret events, password protection, email restrictions, and location-based availability.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from modules.calendar.booking_validation_service import BookingValidationService
from modules.calendar.models import AppointmentType, AvailabilityProfile, BookingLink
from modules.firm.models import Firm

User = get_user_model()


class SecretEventsTest(TestCase):
    """Test secret events (direct link only, hidden from public)."""

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
            weekly_hours={},
            exceptions=[],
            created_by=self.user,
        )

        self.service = BookingValidationService()

    def test_secret_event_requires_direct_link(self):
        """Test that secret events can only be accessed via direct link."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="secret-meeting",
            is_secret=True,
            created_by=self.user,
        )

        # Should fail without direct link
        is_valid, error = self.service.validate_booking_link_access(
            booking_link=booking_link,
            is_direct_link=False,
        )
        self.assertFalse(is_valid)
        self.assertIn("private", error.lower())

        # Should succeed with direct link
        is_valid, error = self.service.validate_booking_link_access(
            booking_link=booking_link,
            is_direct_link=True,
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_public_event_accessible_without_direct_link(self):
        """Test that public events can be accessed without direct link."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="public-meeting",
            is_secret=False,
            created_by=self.user,
        )

        # Should succeed even without direct link
        is_valid, error = self.service.validate_booking_link_access(
            booking_link=booking_link,
            is_direct_link=False,
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)


class PasswordProtectionTest(TestCase):
    """Test password-protected booking links."""

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
            weekly_hours={},
            exceptions=[],
            created_by=self.user,
        )

        self.service = BookingValidationService()

    def test_password_protection(self):
        """Test password-protected booking links."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="protected-meeting",
            created_by=self.user,
        )

        # Set password
        self.service.set_booking_link_password(booking_link, "secret123")

        booking_link.refresh_from_db()
        self.assertTrue(booking_link.password_protected)
        self.assertTrue(len(booking_link.password_hash) > 0)

        # Should fail without password
        is_valid, error = self.service.validate_booking_link_access(
            booking_link=booking_link,
            provided_password=None,
        )
        self.assertFalse(is_valid)
        self.assertIn("password", error.lower())

        # Should fail with wrong password
        is_valid, error = self.service.validate_booking_link_access(
            booking_link=booking_link,
            provided_password="wrong",
        )
        self.assertFalse(is_valid)
        self.assertIn("incorrect", error.lower())

        # Should succeed with correct password
        is_valid, error = self.service.validate_booking_link_access(
            booking_link=booking_link,
            provided_password="secret123",
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_remove_password(self):
        """Test removing password protection."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="temp-protected",
            created_by=self.user,
        )

        # Set password
        self.service.set_booking_link_password(booking_link, "temp123")
        booking_link.refresh_from_db()
        self.assertTrue(booking_link.password_protected)

        # Remove password
        self.service.remove_booking_link_password(booking_link)
        booking_link.refresh_from_db()
        self.assertFalse(booking_link.password_protected)
        self.assertEqual(booking_link.password_hash, '')

        # Should now work without password
        is_valid, error = self.service.validate_booking_link_access(
            booking_link=booking_link,
            provided_password=None,
        )
        self.assertTrue(is_valid)


class EmailRestrictionsTest(TestCase):
    """Test email domain whitelist/blacklist."""

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
            weekly_hours={},
            exceptions=[],
            created_by=self.user,
        )

        self.service = BookingValidationService()

    def test_whitelist_enforcement(self):
        """Test that whitelist restricts to specific domains."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="partner-meeting",
            allowed_email_domains=['partner.com', 'client.com'],
            created_by=self.user,
        )

        # Should allow whitelisted domain
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='user@partner.com',
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Should allow another whitelisted domain
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='user@client.com',
        )
        self.assertTrue(is_valid)

        # Should reject non-whitelisted domain
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='user@random.com',
        )
        self.assertFalse(is_valid)
        self.assertIn("allowed", error.lower())

    def test_blacklist_enforcement(self):
        """Test that blacklist blocks specific domains."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="open-meeting",
            blocked_email_domains=['spam.com', 'blocked.com'],
            created_by=self.user,
        )

        # Should allow non-blacklisted domain
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='user@normal.com',
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Should reject blacklisted domain
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='user@spam.com',
        )
        self.assertFalse(is_valid)
        self.assertIn("not allowed", error.lower())

        # Should reject another blacklisted domain
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='user@blocked.com',
        )
        self.assertFalse(is_valid)

    def test_combined_restrictions(self):
        """Test combined whitelist and blacklist."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="restricted-meeting",
            allowed_email_domains=['company.com'],
            blocked_email_domains=['test.company.com'],
            created_by=self.user,
        )

        # Should allow whitelisted domain
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='user@company.com',
        )
        self.assertTrue(is_valid)

        # Blacklist takes precedence (even if subdomain in whitelist)
        # Note: In current implementation, we check exact domain match
        # So 'test.company.com' is different from 'company.com'
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='user@test.company.com',
        )
        # This should fail because test.company.com is not in whitelist
        self.assertFalse(is_valid)

    def test_invalid_email_format(self):
        """Test that invalid email formats are rejected."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="any-meeting",
            created_by=self.user,
        )

        # Should reject invalid email
        is_valid, error = self.service.validate_email_restrictions(
            booking_link=booking_link,
            email='not-an-email',
        )
        self.assertFalse(is_valid)
        self.assertIn("invalid", error.lower())

    def test_can_book_comprehensive(self):
        """Test comprehensive booking validation."""
        booking_link = BookingLink.objects.create(
            firm=self.firm,
            appointment_type=self.appointment_type,
            availability_profile=self.profile,
            slug="comprehensive-test",
            is_secret=True,
            allowed_email_domains=['allowed.com'],
            created_by=self.user,
        )

        # Should fail: not direct link
        can_book, error = self.service.can_book(
            booking_link=booking_link,
            email='user@allowed.com',
            is_direct_link=False,
        )
        self.assertFalse(can_book)

        # Should fail: wrong email domain (even with direct link)
        can_book, error = self.service.can_book(
            booking_link=booking_link,
            email='user@wrong.com',
            is_direct_link=True,
        )
        self.assertFalse(can_book)

        # Should succeed: direct link + correct domain
        can_book, error = self.service.can_book(
            booking_link=booking_link,
            email='user@allowed.com',
            is_direct_link=True,
        )
        self.assertTrue(can_book)
        self.assertIsNone(error)
