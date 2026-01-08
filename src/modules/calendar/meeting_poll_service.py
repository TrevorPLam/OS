"""Meeting poll services for calendar scheduling."""

import logging
from datetime import datetime

import pytz
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class MeetingPollService:
    """
    Service for managing meeting polls.

    TEAM-4: Implements polling event functionality:
    - Create polls with multiple time slot options
    - Voting interface for invitees
    - Auto-schedule when consensus reached
    - Manual override option
    - Poll expiration
    """

    def create_poll(
        self,
        firm,
        title: str,
        duration_minutes: int,
        proposed_slots: list,
        created_by,
        description: str = "",
        location_mode: str = "video",
        location_details: str = "",
        invitees: list = None,
        voting_deadline: datetime = None,
        allow_maybe_votes: bool = True,
        require_all_invitees: bool = False,
    ):
        """
        Create a new meeting poll.

        TEAM-4: Creates a poll with multiple proposed time slots for invitees to vote on.

        Args:
            firm: Firm this poll belongs to
            title: Poll title
            duration_minutes: Meeting duration
            proposed_slots: List of time slot dicts with start_time, end_time, timezone
            created_by: User creating the poll
            description: Optional meeting description
            location_mode: Meeting location mode
            location_details: Additional location info
            invitees: List of invitee emails or user IDs
            voting_deadline: Optional deadline for voting
            allow_maybe_votes: Allow "maybe" votes
            require_all_invitees: Require all invitees to respond before scheduling

        Returns:
            Created MeetingPoll instance

        Raises:
            ValueError: If invalid input
        """
        from .models import MeetingPoll

        if not proposed_slots or len(proposed_slots) < 2:
            raise ValueError("Must propose at least 2 time slots")

        if not title:
            raise ValueError("Poll title is required")

        poll = MeetingPoll.objects.create(
            firm=firm,
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            location_mode=location_mode,
            location_details=location_details,
            created_by=created_by,
            invitees=invitees or [],
            proposed_slots=proposed_slots,
            status="open",
            voting_deadline=voting_deadline,
            allow_maybe_votes=allow_maybe_votes,
            require_all_invitees=require_all_invitees,
        )

        logger.info(
            f"Created meeting poll {poll.id}: '{title}' with {len(proposed_slots)} proposed slots"
        )

        return poll

    @transaction.atomic
    def vote_on_poll(
        self,
        poll,
        voter_email: str,
        voter_name: str,
        responses: list,
        voter_user=None,
        notes: str = "",
    ):
        """
        Submit a vote on a meeting poll.

        TEAM-4: Records invitee's availability for each proposed time slot.

        Args:
            poll: MeetingPoll instance
            voter_email: Email of voter
            voter_name: Name of voter
            responses: List of responses for each slot ("yes", "no", "maybe")
            voter_user: Optional authenticated user
            notes: Optional notes from voter

        Returns:
            Created or updated MeetingPollVote instance

        Raises:
            ValueError: If poll is closed or invalid input
        """
        from .models import MeetingPollVote

        if poll.status not in ["open"]:
            raise ValueError("Cannot vote on a closed or scheduled poll")

        if len(responses) != len(poll.proposed_slots):
            raise ValueError(
                f"Must provide responses for all {len(poll.proposed_slots)} proposed slots"
            )

        # Validate response values
        valid_responses = ["yes", "no"]
        if poll.allow_maybe_votes:
            valid_responses.append("maybe")

        for response in responses:
            if response not in valid_responses:
                raise ValueError(
                    f"Invalid response '{response}'. Must be one of: {', '.join(valid_responses)}"
                )

        # Check if voter has already voted (update if so)
        vote, created = MeetingPollVote.objects.update_or_create(
            poll=poll,
            voter_email=voter_email,
            defaults={
                "voter_user": voter_user,
                "voter_name": voter_name,
                "responses": responses,
                "notes": notes,
            }
        )

        action = "Created" if created else "Updated"
        logger.info(
            f"{action} vote for poll {poll.id} from {voter_name} ({voter_email})"
        )

        # Check if we should auto-schedule
        if self._should_auto_schedule(poll):
            self._auto_schedule_poll(poll)

        return vote

    def _should_auto_schedule(self, poll) -> bool:
        """
        Check if poll should be auto-scheduled.

        Returns True if:
        - Poll is still open
        - Voting deadline has passed (if set), OR
        - All invitees have responded (if require_all_invitees is True)
        - There's a clear winner slot
        """
        if poll.status != "open":
            return False

        # Check if voting deadline has passed
        if poll.voting_deadline and timezone.now() >= poll.voting_deadline:
            return True

        # Check if all invitees have responded
        if poll.require_all_invitees:
            from .models import MeetingPollVote

            invitee_count = len(poll.invitees)
            vote_count = MeetingPollVote.objects.filter(poll=poll).count()

            if invitee_count > 0 and vote_count >= invitee_count:
                return True

        return False

    @transaction.atomic
    def _auto_schedule_poll(self, poll):
        """
        Auto-schedule a poll by selecting the best time slot.

        Selects the slot with the most "yes" votes.
        """
        best_slot_index = poll.find_best_slot()

        if best_slot_index is None:
            logger.warning(f"Cannot auto-schedule poll {poll.id}: no votes recorded")
            return None

        # Schedule the meeting
        return self.schedule_poll(
            poll=poll,
            slot_index=best_slot_index,
            scheduled_by=poll.created_by,
        )

    @transaction.atomic
    def schedule_poll(
        self,
        poll,
        slot_index: int,
        scheduled_by,
        appointment_type=None,
    ):
        """
        Schedule a meeting from a poll by selecting a time slot.

        TEAM-4: Creates an appointment from the selected poll slot.

        Args:
            poll: MeetingPoll instance
            slot_index: Index of selected slot in poll.proposed_slots
            scheduled_by: User scheduling the meeting
            appointment_type: Optional appointment type to use

        Returns:
            Created Appointment instance

        Raises:
            ValueError: If invalid slot index or poll already scheduled
        """
        from .models import Appointment

        if poll.status == "scheduled":
            raise ValueError("Poll is already scheduled")

        if poll.status == "cancelled":
            raise ValueError("Cannot schedule a cancelled poll")

        if slot_index < 0 or slot_index >= len(poll.proposed_slots):
            raise ValueError(f"Invalid slot index {slot_index}")

        # Get the selected slot
        selected_slot = poll.proposed_slots[slot_index]

        # Parse the slot datetime
        start_time_str = selected_slot.get("start_time")
        end_time_str = selected_slot.get("end_time")
        slot_timezone = selected_slot.get("timezone", "UTC")

        # Parse ISO format datetime strings
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))

        # Ensure timezone aware
        if timezone.is_naive(start_time):
            tz = pytz.timezone(slot_timezone)
            start_time = timezone.make_aware(start_time, tz)
            end_time = timezone.make_aware(end_time, tz)

        # Create appointment
        appointment = Appointment.objects.create(
            firm=poll.firm,
            appointment_type=appointment_type,
            start_time=start_time,
            end_time=end_time,
            timezone=slot_timezone,
            location_mode=poll.location_mode,
            location_details=poll.location_details,
            status="confirmed",
            booked_by=scheduled_by,
            notes=f"Scheduled from poll: {poll.title}",
        )

        # Update poll status
        poll.status = "scheduled"
        poll.selected_slot_index = slot_index
        poll.scheduled_appointment = appointment
        poll.closed_at = timezone.now()
        poll.save()

        logger.info(
            f"Scheduled appointment {appointment.appointment_id} from poll {poll.id} "
            f"(slot {slot_index})"
        )

        return appointment

    @transaction.atomic
    def cancel_poll(
        self,
        poll,
        cancelled_by,
        reason: str = "",
    ):
        """
        Cancel a meeting poll.

        Args:
            poll: MeetingPoll instance
            cancelled_by: User cancelling the poll
            reason: Optional reason for cancellation

        Returns:
            Updated poll instance
        """
        if poll.status in ["scheduled", "cancelled"]:
            raise ValueError(f"Cannot cancel a poll that is already {poll.status}")

        poll.status = "cancelled"
        poll.closed_at = timezone.now()
        poll.save()

        logger.info(
            f"Cancelled poll {poll.id}: '{poll.title}' by {cancelled_by.username}"
            + (f" - Reason: {reason}" if reason else "")
        )

        return poll

    def get_vote_results(self, poll):
        """
        Get detailed voting results for a poll.

        Args:
            poll: MeetingPoll instance

        Returns:
            Dict with vote summary and recommended slot
        """
        vote_summary = poll.get_vote_summary()
        best_slot = poll.find_best_slot()

        # Calculate response rate
        from .models import MeetingPollVote

        total_invitees = len(poll.invitees)
        total_votes = MeetingPollVote.objects.filter(poll=poll).count()
        response_rate = (total_votes / total_invitees * 100) if total_invitees > 0 else 0

        return {
            "poll_id": poll.id,
            "title": poll.title,
            "status": poll.status,
            "total_invitees": total_invitees,
            "total_votes": total_votes,
            "response_rate": round(response_rate, 1),
            "vote_summary": vote_summary,
            "recommended_slot_index": best_slot,
            "selected_slot_index": poll.selected_slot_index,
            "voting_deadline": poll.voting_deadline,
            "closed_at": poll.closed_at,
        }
