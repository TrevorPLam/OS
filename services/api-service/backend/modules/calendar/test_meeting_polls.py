"""
TEAM-4: Meeting Poll Tests.

Tests for meeting poll functionality including:
- Create polls with multiple time slot options
- Voting interface for invitees
- Auto-schedule when consensus reached
- Manual override option
- Poll expiration
"""

from datetime import datetime, timedelta

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from modules.calendar.models import Appointment, AppointmentType, MeetingPoll, MeetingPollVote
from modules.calendar.services import MeetingPollService
from modules.firm.models import Firm

User = get_user_model()


class MeetingPollCreationTest(TestCase):
    """Test meeting poll creation (TEAM-4)."""

    def setUp(self):
        """Set up test fixtures for meeting polls."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.service = MeetingPollService()

    def test_create_poll_with_valid_data(self):
        """Test creating a poll with valid data."""
        proposed_slots = [
            {
                "start_time": "2025-12-15T10:00:00Z",
                "end_time": "2025-12-15T11:00:00Z",
                "timezone": "America/New_York",
            },
            {
                "start_time": "2025-12-15T14:00:00Z",
                "end_time": "2025-12-15T15:00:00Z",
                "timezone": "America/New_York",
            },
            {
                "start_time": "2025-12-16T10:00:00Z",
                "end_time": "2025-12-16T11:00:00Z",
                "timezone": "America/New_York",
            },
        ]

        invitees = ["alice@example.com", "bob@example.com", "charlie@example.com"]

        poll = self.service.create_poll(
            firm=self.firm,
            title="Q4 Strategy Meeting",
            duration_minutes=60,
            proposed_slots=proposed_slots,
            created_by=self.user,
            description="Quarterly strategy review",
            invitees=invitees,
            allow_maybe_votes=True,
        )

        self.assertIsNotNone(poll)
        self.assertEqual(poll.title, "Q4 Strategy Meeting")
        self.assertEqual(poll.duration_minutes, 60)
        self.assertEqual(len(poll.proposed_slots), 3)
        self.assertEqual(len(poll.invitees), 3)
        self.assertEqual(poll.status, "open")
        self.assertTrue(poll.allow_maybe_votes)

    def test_create_poll_with_insufficient_slots(self):
        """Test that creating a poll with less than 2 slots fails."""
        proposed_slots = [
            {
                "start_time": "2025-12-15T10:00:00Z",
                "end_time": "2025-12-15T11:00:00Z",
                "timezone": "America/New_York",
            },
        ]

        with self.assertRaises(ValueError) as context:
            self.service.create_poll(
                firm=self.firm,
                title="Meeting",
                duration_minutes=60,
                proposed_slots=proposed_slots,
                created_by=self.user,
            )

        self.assertIn("at least 2 time slots", str(context.exception))


class MeetingPollVotingTest(TestCase):
    """Test meeting poll voting (TEAM-4)."""

    def setUp(self):
        """Set up test fixtures for voting."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.service = MeetingPollService()

        proposed_slots = [
            {
                "start_time": "2025-12-15T10:00:00Z",
                "end_time": "2025-12-15T11:00:00Z",
                "timezone": "America/New_York",
            },
            {
                "start_time": "2025-12-15T14:00:00Z",
                "end_time": "2025-12-15T15:00:00Z",
                "timezone": "America/New_York",
            },
        ]

        self.poll = self.service.create_poll(
            firm=self.firm,
            title="Team Meeting",
            duration_minutes=60,
            proposed_slots=proposed_slots,
            created_by=self.user,
            invitees=["alice@example.com", "bob@example.com"],
        )

    def test_vote_on_poll_with_valid_responses(self):
        """Test voting on a poll with valid responses."""
        responses = ["yes", "no"]

        vote = self.service.vote_on_poll(
            poll=self.poll,
            voter_email="alice@example.com",
            voter_name="Alice",
            responses=responses,
        )

        self.assertIsNotNone(vote)
        self.assertEqual(vote.voter_email, "alice@example.com")
        self.assertEqual(vote.voter_name, "Alice")
        self.assertEqual(vote.responses, responses)

    def test_vote_with_maybe_option(self):
        """Test voting with 'maybe' option when allowed."""
        responses = ["yes", "maybe"]

        vote = self.service.vote_on_poll(
            poll=self.poll,
            voter_email="bob@example.com",
            voter_name="Bob",
            responses=responses,
        )

        self.assertIsNotNone(vote)
        self.assertIn("maybe", vote.responses)

    def test_vote_with_invalid_response_count(self):
        """Test that voting with wrong number of responses fails."""
        responses = ["yes"]  # Only 1 response, but 2 slots

        with self.assertRaises(ValueError) as context:
            self.service.vote_on_poll(
                poll=self.poll,
                voter_email="alice@example.com",
                voter_name="Alice",
                responses=responses,
            )

        self.assertIn("Must provide responses for all", str(context.exception))

    def test_update_existing_vote(self):
        """Test that voting again updates the existing vote."""
        # First vote
        vote1 = self.service.vote_on_poll(
            poll=self.poll,
            voter_email="alice@example.com",
            voter_name="Alice",
            responses=["yes", "no"],
        )

        # Second vote (update)
        vote2 = self.service.vote_on_poll(
            poll=self.poll,
            voter_email="alice@example.com",
            voter_name="Alice",
            responses=["no", "yes"],
        )

        # Should be the same vote object (updated)
        self.assertEqual(vote1.id, vote2.id)
        self.assertEqual(vote2.responses, ["no", "yes"])

        # Should only have one vote total
        total_votes = MeetingPollVote.objects.filter(poll=self.poll).count()
        self.assertEqual(total_votes, 1)


class MeetingPollSchedulingTest(TestCase):
    """Test meeting poll scheduling (TEAM-4)."""

    def setUp(self):
        """Set up test fixtures for scheduling."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.service = MeetingPollService()

        proposed_slots = [
            {
                "start_time": "2025-12-15T10:00:00Z",
                "end_time": "2025-12-15T11:00:00Z",
                "timezone": "America/New_York",
            },
            {
                "start_time": "2025-12-15T14:00:00Z",
                "end_time": "2025-12-15T15:00:00Z",
                "timezone": "America/New_York",
            },
            {
                "start_time": "2025-12-16T10:00:00Z",
                "end_time": "2025-12-16T11:00:00Z",
                "timezone": "America/New_York",
            },
        ]

        self.poll = self.service.create_poll(
            firm=self.firm,
            title="Team Meeting",
            duration_minutes=60,
            proposed_slots=proposed_slots,
            created_by=self.user,
            invitees=["alice@example.com", "bob@example.com", "charlie@example.com"],
        )

        # Add votes
        self.service.vote_on_poll(
            poll=self.poll,
            voter_email="alice@example.com",
            voter_name="Alice",
            responses=["yes", "no", "yes"],
        )
        self.service.vote_on_poll(
            poll=self.poll,
            voter_email="bob@example.com",
            voter_name="Bob",
            responses=["yes", "yes", "no"],
        )
        self.service.vote_on_poll(
            poll=self.poll,
            voter_email="charlie@example.com",
            voter_name="Charlie",
            responses=["yes", "maybe", "no"],
        )

    def test_manual_schedule_poll(self):
        """Test manually scheduling a poll."""
        # Slot 0 has 3 yes votes (best option)
        appointment = self.service.schedule_poll(
            poll=self.poll,
            slot_index=0,
            scheduled_by=self.user,
        )

        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.status, "confirmed")
        self.assertEqual(appointment.firm, self.firm)

        # Refresh poll
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.status, "scheduled")
        self.assertEqual(self.poll.selected_slot_index, 0)
        self.assertEqual(self.poll.scheduled_appointment, appointment)

    def test_find_best_slot(self):
        """Test that the best slot is correctly identified."""
        best_slot = self.poll.find_best_slot()
        
        # Slot 0: 3 yes, 0 no
        # Slot 1: 1 yes, 1 no, 1 maybe
        # Slot 2: 1 yes, 2 no
        # Best should be slot 0
        self.assertEqual(best_slot, 0)

    def test_get_vote_summary(self):
        """Test getting vote summary."""
        summary = self.poll.get_vote_summary()
        
        # Check slot 0
        self.assertEqual(summary[0]["yes"], 3)
        self.assertEqual(summary[0]["no"], 0)
        
        # Check slot 1
        self.assertEqual(summary[1]["yes"], 1)
        self.assertEqual(summary[1]["no"], 1)
        self.assertEqual(summary[1]["maybe"], 1)

    def test_schedule_with_invalid_slot_index(self):
        """Test that scheduling with invalid slot index fails."""
        with self.assertRaises(ValueError) as context:
            self.service.schedule_poll(
                poll=self.poll,
                slot_index=10,  # Invalid index
                scheduled_by=self.user,
            )

        self.assertIn("Invalid slot index", str(context.exception))

    def test_cannot_schedule_already_scheduled_poll(self):
        """Test that scheduling an already scheduled poll fails."""
        # Schedule once
        self.service.schedule_poll(
            poll=self.poll,
            slot_index=0,
            scheduled_by=self.user,
        )

        # Try to schedule again
        with self.assertRaises(ValueError) as context:
            self.service.schedule_poll(
                poll=self.poll,
                slot_index=1,
                scheduled_by=self.user,
            )

        self.assertIn("already scheduled", str(context.exception))


class MeetingPollAutoScheduleTest(TestCase):
    """Test automatic scheduling when all invitees respond (TEAM-4)."""

    def setUp(self):
        """Set up test fixtures for auto-scheduling."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.service = MeetingPollService()

        proposed_slots = [
            {
                "start_time": "2025-12-15T10:00:00Z",
                "end_time": "2025-12-15T11:00:00Z",
                "timezone": "America/New_York",
            },
            {
                "start_time": "2025-12-15T14:00:00Z",
                "end_time": "2025-12-15T15:00:00Z",
                "timezone": "America/New_York",
            },
        ]

        self.poll = self.service.create_poll(
            firm=self.firm,
            title="Team Meeting",
            duration_minutes=60,
            proposed_slots=proposed_slots,
            created_by=self.user,
            invitees=["alice@example.com", "bob@example.com"],
            require_all_invitees=True,  # Enable auto-schedule when all vote
        )

    def test_auto_schedule_when_all_invitees_respond(self):
        """Test that poll auto-schedules when all invitees have voted."""
        # First vote
        self.service.vote_on_poll(
            poll=self.poll,
            voter_email="alice@example.com",
            voter_name="Alice",
            responses=["yes", "no"],
        )

        # Poll should still be open
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.status, "open")

        # Second vote (all invitees have now responded)
        self.service.vote_on_poll(
            poll=self.poll,
            voter_email="bob@example.com",
            voter_name="Bob",
            responses=["yes", "no"],
        )

        # Poll should now be auto-scheduled
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.status, "scheduled")
        self.assertIsNotNone(self.poll.scheduled_appointment)
        self.assertEqual(self.poll.selected_slot_index, 0)  # Best slot


class MeetingPollCancellationTest(TestCase):
    """Test meeting poll cancellation (TEAM-4)."""

    def setUp(self):
        """Set up test fixtures for cancellation."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.service = MeetingPollService()

        proposed_slots = [
            {
                "start_time": "2025-12-15T10:00:00Z",
                "end_time": "2025-12-15T11:00:00Z",
                "timezone": "America/New_York",
            },
            {
                "start_time": "2025-12-15T14:00:00Z",
                "end_time": "2025-12-15T15:00:00Z",
                "timezone": "America/New_York",
            },
        ]

        self.poll = self.service.create_poll(
            firm=self.firm,
            title="Team Meeting",
            duration_minutes=60,
            proposed_slots=proposed_slots,
            created_by=self.user,
        )

    def test_cancel_open_poll(self):
        """Test cancelling an open poll."""
        cancelled_poll = self.service.cancel_poll(
            poll=self.poll,
            cancelled_by=self.user,
            reason="Meeting no longer needed",
        )

        self.assertEqual(cancelled_poll.status, "cancelled")
        self.assertIsNotNone(cancelled_poll.closed_at)

    def test_cannot_cancel_already_cancelled_poll(self):
        """Test that cancelling an already cancelled poll fails."""
        # Cancel once
        self.service.cancel_poll(
            poll=self.poll,
            cancelled_by=self.user,
        )

        # Try to cancel again
        with self.assertRaises(ValueError) as context:
            self.service.cancel_poll(
                poll=self.poll,
                cancelled_by=self.user,
            )

        self.assertIn("Cannot cancel", str(context.exception))


class MeetingPollResultsTest(TestCase):
    """Test meeting poll results and analytics (TEAM-4)."""

    def setUp(self):
        """Set up test fixtures for results."""
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.service = MeetingPollService()

        proposed_slots = [
            {
                "start_time": "2025-12-15T10:00:00Z",
                "end_time": "2025-12-15T11:00:00Z",
                "timezone": "America/New_York",
            },
            {
                "start_time": "2025-12-15T14:00:00Z",
                "end_time": "2025-12-15T15:00:00Z",
                "timezone": "America/New_York",
            },
        ]

        self.poll = self.service.create_poll(
            firm=self.firm,
            title="Team Meeting",
            duration_minutes=60,
            proposed_slots=proposed_slots,
            created_by=self.user,
            invitees=["alice@example.com", "bob@example.com", "charlie@example.com"],
        )

        # Add some votes
        self.service.vote_on_poll(
            poll=self.poll,
            voter_email="alice@example.com",
            voter_name="Alice",
            responses=["yes", "no"],
        )
        self.service.vote_on_poll(
            poll=self.poll,
            voter_email="bob@example.com",
            voter_name="Bob",
            responses=["yes", "yes"],
        )

    def test_get_vote_results(self):
        """Test getting comprehensive vote results."""
        results = self.service.get_vote_results(self.poll)

        self.assertEqual(results["poll_id"], self.poll.id)
        self.assertEqual(results["title"], "Team Meeting")
        self.assertEqual(results["status"], "open")
        self.assertEqual(results["total_invitees"], 3)
        self.assertEqual(results["total_votes"], 2)
        self.assertAlmostEqual(results["response_rate"], 66.7, places=1)
        self.assertEqual(results["recommended_slot_index"], 0)

        # Check vote summary
        vote_summary = results["vote_summary"]
        self.assertEqual(vote_summary[0]["yes"], 2)
        self.assertEqual(vote_summary[0]["no"], 0)
        self.assertEqual(vote_summary[1]["yes"], 1)
        self.assertEqual(vote_summary[1]["no"], 1)
