"""
Calendar Services.

Aggregator for availability computation, routing, and booking logic.
Implements docs/03-reference/requirements/DOC-34.md sections 2.4, 3, and 4.
Enhanced with AVAIL-1: Multiple calendar support and external calendar conflict checking.
Enhanced with AVAIL-2: Comprehensive availability rules (recurring unavailability, holidays, meeting gaps).
"""

from .availability_service import AvailabilityService
from .booking_service import BookingService
from .group_event_service import GroupEventService
from .invitation_service import CalendarInvitationService
from .meeting_poll_service import MeetingPollService
from .round_robin_service import RoundRobinService
from .routing_service import RoutingService

__all__ = [
    "AvailabilityService",
    "BookingService",
    "GroupEventService",
    "CalendarInvitationService",
    "MeetingPollService",
    "RoundRobinService",
    "RoutingService",
]
