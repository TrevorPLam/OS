"""
Booking Validation Service.

Provides validation for booking links with advanced access control features.
Implements AVAIL-3: Secret events, password protection, email restrictions.
"""

import hashlib
import logging
from typing import Optional, Tuple

from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import BookingLink

logger = logging.getLogger(__name__)


class BookingValidationService:
    """
    Service for validating booking link access and email restrictions.

    Implements AVAIL-3 features:
    - Secret events (direct link only)
    - Password-protected booking
    - Email domain whitelist/blacklist
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password for storage.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            password: Plain text password to verify
            password_hash: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

    def validate_booking_link_access(
        self,
        booking_link: BookingLink,
        provided_password: Optional[str] = None,
        is_direct_link: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate access to a booking link.

        Args:
            booking_link: BookingLink to validate
            provided_password: Password provided by user (if any)
            is_direct_link: Whether user accessed via direct link (vs. discovery/list)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if link is active
        if booking_link.status != 'active':
            return False, "This booking link is no longer active"

        # Check if secret event and not accessed via direct link
        if booking_link.is_secret and not is_direct_link:
            return False, "This is a private event. Access via direct link only."

        # Check password protection
        if booking_link.password_protected:
            if not provided_password:
                return False, "Password required to access this booking link"

            if not self.verify_password(provided_password, booking_link.password_hash):
                return False, "Incorrect password"

        return True, None

    def validate_email_restrictions(
        self,
        booking_link: BookingLink,
        email: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate email against booking link restrictions.

        Args:
            booking_link: BookingLink with email restrictions
            email: Email address to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # First, validate email format
        try:
            validate_email(email)
        except DjangoValidationError:
            return False, "Invalid email address format"

        # Extract domain from email
        domain = email.split('@')[1].lower() if '@' in email else ''

        if not domain:
            return False, "Invalid email address"

        # Check blacklist first
        if booking_link.blocked_email_domains:
            blocked_domains = [d.lower() for d in booking_link.blocked_email_domains]
            if domain in blocked_domains:
                logger.info(f"Email domain {domain} is blocked for booking link {booking_link.booking_link_id}")
                return False, f"Email addresses from {domain} are not allowed"

        # Check whitelist
        if booking_link.allowed_email_domains:
            allowed_domains = [d.lower() for d in booking_link.allowed_email_domains]
            if domain not in allowed_domains:
                logger.info(f"Email domain {domain} not in whitelist for booking link {booking_link.booking_link_id}")
                allowed_list = ", ".join(allowed_domains)
                return False, f"Only email addresses from these domains are allowed: {allowed_list}"

        return True, None

    def can_book(
        self,
        booking_link: BookingLink,
        email: str,
        provided_password: Optional[str] = None,
        is_direct_link: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a user can book via a booking link.

        Combines all validation checks:
        - Link access (secret, password)
        - Email restrictions (whitelist/blacklist)

        Args:
            booking_link: BookingLink to validate
            email: User's email address
            provided_password: Password provided by user (if any)
            is_direct_link: Whether accessed via direct link

        Returns:
            Tuple of (can_book, error_message)
        """
        # Validate link access
        access_valid, access_error = self.validate_booking_link_access(
            booking_link=booking_link,
            provided_password=provided_password,
            is_direct_link=is_direct_link,
        )

        if not access_valid:
            return False, access_error

        # Validate email restrictions
        email_valid, email_error = self.validate_email_restrictions(
            booking_link=booking_link,
            email=email,
        )

        if not email_valid:
            return False, email_error

        return True, None

    def set_booking_link_password(
        self,
        booking_link: BookingLink,
        password: str,
    ) -> None:
        """
        Set password for a booking link.

        Args:
            booking_link: BookingLink to protect
            password: Plain text password
        """
        booking_link.password_protected = True
        booking_link.password_hash = self.hash_password(password)
        booking_link.save(update_fields=['password_protected', 'password_hash', 'updated_at'])

    def remove_booking_link_password(
        self,
        booking_link: BookingLink,
    ) -> None:
        """
        Remove password protection from a booking link.

        Args:
            booking_link: BookingLink to unprotect
        """
        booking_link.password_protected = False
        booking_link.password_hash = ''
        booking_link.save(update_fields=['password_protected', 'password_hash', 'updated_at'])

    def add_allowed_email_domain(
        self,
        booking_link: BookingLink,
        domain: str,
    ) -> None:
        """
        Add a domain to the whitelist.

        Args:
            booking_link: BookingLink to update
            domain: Domain to allow (e.g., 'example.com')
        """
        if not booking_link.allowed_email_domains:
            booking_link.allowed_email_domains = []

        domain = domain.lower().strip()
        if domain not in booking_link.allowed_email_domains:
            booking_link.allowed_email_domains.append(domain)
            booking_link.save(update_fields=['allowed_email_domains', 'updated_at'])

    def add_blocked_email_domain(
        self,
        booking_link: BookingLink,
        domain: str,
    ) -> None:
        """
        Add a domain to the blacklist.

        Args:
            booking_link: BookingLink to update
            domain: Domain to block (e.g., 'spam.com')
        """
        if not booking_link.blocked_email_domains:
            booking_link.blocked_email_domains = []

        domain = domain.lower().strip()
        if domain not in booking_link.blocked_email_domains:
            booking_link.blocked_email_domains.append(domain)
            booking_link.save(update_fields=['blocked_email_domains', 'updated_at'])
