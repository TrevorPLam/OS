"""Group event management services for calendar appointments."""

import logging

from django.db import transaction
from django.utils import timezone

from .models import Appointment

logger = logging.getLogger(__name__)


class GroupEventService:
    """
    Service for managing group events.

    TEAM-3: Implements group event functionality:
    - Attendee registration and management
    - Waitlist when full
    - Automatic promotion from waitlist
    - Capacity tracking
    """

    def register_attendee(
        self,
        appointment: Appointment,
        contact=None,
        attendee_name: str = "",
        attendee_email: str = "",
    ) -> tuple:
        """
        Register an attendee for a group event.

        TEAM-3: Handles registration with capacity checking and waitlist management.

        Args:
            appointment: Group event appointment
            contact: Optional contact to register
            attendee_name: Name if not a contact
            attendee_email: Email if not a contact

        Returns:
            Tuple of (attendee_or_waitlist, is_on_waitlist)

        Raises:
            ValueError: If not a group event or invalid input
        """
        from .models import GroupEventAttendee, GroupEventWaitlist

        if appointment.appointment_type.event_category != "group":
            raise ValueError("This endpoint only works with group event types")

        if not contact and not (attendee_name and attendee_email):
            raise ValueError("Must provide either contact or attendee name and email")

        # Check current capacity
        current_attendees = GroupEventAttendee.objects.filter(
            appointment=appointment,
            status__in=["registered", "confirmed"],
        ).count()

        max_attendees = appointment.appointment_type.max_attendees

        if current_attendees < max_attendees:
            # Space available - register directly
            attendee = GroupEventAttendee.objects.create(
                appointment=appointment,
                contact=contact,
                attendee_name=attendee_name,
                attendee_email=attendee_email,
                status="registered",
            )

            logger.info(
                f"Registered attendee for group event {appointment.appointment_id}: "
                f"{contact.name if contact else attendee_name}"
            )

            return attendee, False

        # At capacity - check if waitlist is enabled
        if not appointment.appointment_type.enable_waitlist:
            raise ValueError("Group event is at capacity and waitlist is not enabled")

        # Add to waitlist
        waitlist_entry = GroupEventWaitlist.objects.create(
            appointment=appointment,
            contact=contact,
            waitlist_name=attendee_name,
            waitlist_email=attendee_email,
            status="waiting",
        )

        logger.info(
            f"Added to waitlist for group event {appointment.appointment_id}: "
            f"{contact.name if contact else attendee_name}"
        )

        return waitlist_entry, True

    @transaction.atomic
    def cancel_attendee(
        self,
        appointment: Appointment,
        attendee_id: int,
    ):
        """
        Cancel an attendee and promote from waitlist if available.

        TEAM-3: Handles attendee cancellation with automatic waitlist promotion.

        Args:
            appointment: Group event appointment
            attendee_id: ID of attendee to cancel

        Returns:
            Tuple of (cancelled_attendee, promoted_waitlist_entry)
        """
        from .models import GroupEventAttendee, GroupEventWaitlist

        try:
            attendee = GroupEventAttendee.objects.select_for_update().get(
                attendee_id=attendee_id,
                appointment=appointment,
            )
        except GroupEventAttendee.DoesNotExist:
            raise ValueError("Attendee not found")

        # Cancel the attendee
        attendee.status = "cancelled"
        attendee.save()

        logger.info(
            f"Cancelled attendee {attendee_id} for group event {appointment.appointment_id}"
        )

        # Try to promote from waitlist
        promoted_entry = self._promote_from_waitlist(appointment)

        return attendee, promoted_entry

    def _promote_from_waitlist(self, appointment: Appointment):
        """
        Promote the next person from waitlist to attendee.

        Args:
            appointment: Group event appointment

        Returns:
            Promoted waitlist entry or None if waitlist is empty
        """
        from .models import GroupEventAttendee, GroupEventWaitlist

        # Get next waiting entry (highest priority, then oldest)
        waitlist_entry = GroupEventWaitlist.objects.filter(
            appointment=appointment,
            status="waiting",
        ).order_by("-priority", "joined_at").first()

        if not waitlist_entry:
            return None

        # Create attendee from waitlist entry
        attendee = GroupEventAttendee.objects.create(
            appointment=appointment,
            contact=waitlist_entry.contact,
            attendee_name=waitlist_entry.waitlist_name,
            attendee_email=waitlist_entry.waitlist_email,
            status="registered",
        )

        # Mark waitlist entry as promoted
        waitlist_entry.status = "promoted"
        waitlist_entry.promoted_at = timezone.now()
        waitlist_entry.save()

        logger.info(
            f"Promoted waitlist entry {waitlist_entry.waitlist_id} to attendee "
            f"for group event {appointment.appointment_id}"
        )

        return waitlist_entry

    def get_attendee_list(self, appointment: Appointment):
        """
        Get the list of attendees for a group event.

        Args:
            appointment: Group event appointment

        Returns:
            QuerySet of GroupEventAttendee
        """
        from .models import GroupEventAttendee

        return GroupEventAttendee.objects.filter(
            appointment=appointment,
            status__in=["registered", "confirmed", "attended"],
        ).order_by("registered_at")

    def get_waitlist(self, appointment: Appointment):
        """
        Get the waitlist for a group event.

        Args:
            appointment: Group event appointment

        Returns:
            QuerySet of GroupEventWaitlist
        """
        from .models import GroupEventWaitlist

        return GroupEventWaitlist.objects.filter(
            appointment=appointment,
            status="waiting",
        ).order_by("-priority", "joined_at")

    def get_capacity_info(self, appointment: Appointment):
        """
        Get capacity information for a group event.

        Args:
            appointment: Group event appointment

        Returns:
            Dict with capacity info
        """
        from .models import GroupEventAttendee

        if appointment.appointment_type.event_category != "group":
            return None

        max_attendees = appointment.appointment_type.max_attendees
        current_attendees = GroupEventAttendee.objects.filter(
            appointment=appointment,
            status__in=["registered", "confirmed"],
        ).count()

        waitlist_count = 0
        if appointment.appointment_type.enable_waitlist:
            from .models import GroupEventWaitlist
            waitlist_count = GroupEventWaitlist.objects.filter(
                appointment=appointment,
                status="waiting",
            ).count()

        return {
            "max_attendees": max_attendees,
            "current_attendees": current_attendees,
            "available_spots": max(0, max_attendees - current_attendees),
            "is_full": current_attendees >= max_attendees,
            "waitlist_enabled": appointment.appointment_type.enable_waitlist,
            "waitlist_count": waitlist_count,
        }
