"""Calendar invitation (ICS) generation services."""

import logging
from typing import List, Tuple

from django.utils import timezone

from .models import Appointment

logger = logging.getLogger(__name__)


class CalendarInvitationService:
    """
    Service for generating calendar invitation (ICS) files.

    FLOW-1: Implements calendar invitation generation for appointment reminders.
    Generates iCalendar (.ics) files that can be attached to reminder emails.
    """

    def generate_ics(
        self,
        appointment: Appointment,
        method: str = "REQUEST",
    ) -> str:
        """
        Generate an iCalendar (.ics) file for an appointment.

        FLOW-1: Creates ICS calendar invitation for email reminders.

        Args:
            appointment: Appointment to create invitation for
            method: iCalendar method (REQUEST, CANCEL, PUBLISH)

        Returns:
            ICS file content as string

        Example usage:
            service = CalendarInvitationService()
            ics_content = service.generate_ics(appointment)
            # Attach ics_content to email
        """
        try:
            from icalendar import Calendar, Event
            from icalendar import vCalAddress, vText
        except ImportError:
            logger.error("icalendar library not installed. Install with: pip install icalendar")
            raise ImportError("icalendar library required for ICS generation")

        # Create calendar
        cal = Calendar()
        cal.add('prodid', '-//UBOS//Calendar Invitation//EN')
        cal.add('version', '2.0')
        cal.add('method', method)

        # Create event
        event = Event()

        # Add basic event details
        event.add('uid', f'appointment-{appointment.appointment_id}@ubos.app')
        event.add('summary', f"Meeting: {appointment.appointment_type.name}")

        # Add description
        description_parts = []
        if appointment.appointment_type.description:
            description_parts.append(appointment.appointment_type.description)
        if appointment.notes:
            description_parts.append(f"Notes: {appointment.notes}")
        if description_parts:
            event.add('description', '\n\n'.join(description_parts))

        # Add times
        event.add('dtstart', appointment.start_time)
        event.add('dtend', appointment.end_time)
        event.add('dtstamp', timezone.now())

        # Add location
        location = self._format_location(appointment)
        if location:
            event.add('location', location)

        # Add organizer (staff user)
        if appointment.staff_user and appointment.staff_user.email:
            organizer = vCalAddress(f'MAILTO:{appointment.staff_user.email}')
            organizer.params['cn'] = vText(appointment.staff_user.get_full_name() or appointment.staff_user.email)
            organizer.params['role'] = vText('CHAIR')
            event['organizer'] = organizer

        # Add attendees
        attendees = self._get_attendees(appointment)
        for attendee_email, attendee_name in attendees:
            attendee = vCalAddress(f'MAILTO:{attendee_email}')
            attendee.params['cn'] = vText(attendee_name)
            attendee.params['role'] = vText('REQ-PARTICIPANT')
            attendee.params['rsvp'] = vText('TRUE')
            event.add('attendee', attendee, encode=0)

        # Add status
        status_map = {
            'requested': 'TENTATIVE',
            'confirmed': 'CONFIRMED',
            'cancelled': 'CANCELLED',
            'completed': 'CONFIRMED',
        }
        event.add('status', status_map.get(appointment.status, 'CONFIRMED'))

        # Add sequence for updates
        event.add('sequence', 0)

        # Add event to calendar
        cal.add_component(event)

        # Generate ICS content
        ics_content = cal.to_ical().decode('utf-8')

        logger.info(f"Generated ICS invitation for appointment {appointment.appointment_id}")

        return ics_content

    def _format_location(self, appointment: Appointment) -> str:
        """
        Format appointment location for ICS file.

        Returns location string based on location_mode.
        """
        location_mode = appointment.appointment_type.location_mode
        location_details = appointment.appointment_type.location_details

        if location_mode == "video":
            if location_details:
                return f"Video Call: {location_details}"
            return "Video Call"
        if location_mode == "phone":
            if location_details:
                return f"Phone: {location_details}"
            return "Phone Call"
        if location_mode == "in_person":
            if location_details:
                return location_details
            return "In Person"
        if location_mode == "custom":
            return location_details or "See details"

        return ""

    def _get_attendees(self, appointment: Appointment) -> List[Tuple[str, str]]:
        """
        Get list of attendees for the appointment.

        Returns:
            List of (email, name) tuples
        """
        attendees = []

        # Add contact if available
        if appointment.contact and hasattr(appointment.contact, 'email'):
            contact_email = getattr(appointment.contact, 'email', None)
            if contact_email:
                attendees.append((
                    contact_email,
                    appointment.contact.name
                ))

        # Add collective hosts if it's a collective event
        if appointment.appointment_type.event_category == "collective":
            for host in appointment.collective_hosts.all():
                if host.email and host != appointment.staff_user:
                    attendees.append((
                        host.email,
                        host.get_full_name() or host.email
                    ))

        return attendees

    def generate_cancellation_ics(self, appointment: Appointment) -> str:
        """
        Generate a cancellation ICS file for an appointment.

        FLOW-1: Creates ICS cancellation notice for cancelled appointments.

        Args:
            appointment: Cancelled appointment

        Returns:
            ICS cancellation file content as string
        """
        return self.generate_ics(appointment, method="CANCEL")
