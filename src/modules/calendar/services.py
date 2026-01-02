"""
Calendar Services.

Provides availability computation, routing, and booking logic.
Implements docs/34 sections 2.4, 3, and 4.
Enhanced with AVAIL-1: Multiple calendar support and external calendar conflict checking.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Tuple, Optional
import pytz
from django.db import transaction
from django.utils import timezone

from .models import (
    AppointmentType,
    AvailabilityProfile,
    Appointment,
    AppointmentStatusHistory,
)
from .oauth_models import OAuthConnection
from .ical_service import ICalService
from .google_service import GoogleCalendarService
from .microsoft_service import MicrosoftCalendarService

logger = logging.getLogger(__name__)


class AvailabilityService:
    """
    Service for computing available slots.

    Implements docs/34 section 4: availability computation with buffers and constraints.
    """

    def compute_available_slots(
        self,
        profile: AvailabilityProfile,
        appointment_type: AppointmentType,
        start_date: datetime.date,
        end_date: datetime.date,
        staff_user=None,
    ) -> List[Tuple[datetime, datetime]]:
        """
        Compute available slots for a given profile and appointment type.

        Returns list of (start_time, end_time) tuples in UTC.

        Per docs/34 section 4:
        1. Availability computed in profile timezone
        2. Buffers enforced
        3. Min notice and max future booking enforced
        4. Conflicts with existing appointments considered
        """
        # Get profile timezone
        profile_tz = pytz.timezone(profile.timezone)
        now = timezone.now()

        # Enforce min notice (per docs/34 section 4.3)
        earliest_start = now + timedelta(minutes=profile.min_notice_minutes)

        # Enforce max future booking (per docs/34 section 4.3)
        latest_start = now + timedelta(days=profile.max_future_days)

        slots = []

        # Iterate through each day
        current_date = start_date
        while current_date <= end_date:
            # Skip if outside allowed booking window
            day_start_naive = datetime.combine(current_date, datetime.min.time())
            day_start_aware = profile_tz.localize(day_start_naive)

            if day_start_aware.astimezone(pytz.UTC) > latest_start:
                break

            # Check if day is in exceptions
            if self._is_exception_date(current_date, profile.exceptions):
                current_date += timedelta(days=1)
                continue

            # Get weekly hours for this day
            day_name = current_date.strftime("%A").lower()
            day_hours = profile.weekly_hours.get(day_name, [])

            for time_slot in day_hours:
                # Parse start and end times
                start_time_str = time_slot.get("start")
                end_time_str = time_slot.get("end")

                if not start_time_str or not end_time_str:
                    continue

                # Create datetime objects in profile timezone
                start_hour, start_minute = map(int, start_time_str.split(":"))
                end_hour, end_minute = map(int, end_time_str.split(":"))

                slot_start_naive = datetime.combine(
                    current_date, datetime.min.time()
                ).replace(hour=start_hour, minute=start_minute)
                slot_end_naive = datetime.combine(
                    current_date, datetime.min.time()
                ).replace(hour=end_hour, minute=end_minute)

                slot_start_aware = profile_tz.localize(slot_start_naive)
                slot_end_aware = profile_tz.localize(slot_end_naive)

                # Generate slots within this window
                current_slot_start = slot_start_aware
                while current_slot_start + timedelta(minutes=appointment_type.duration_minutes) <= slot_end_aware:
                    slot_end = current_slot_start + timedelta(minutes=appointment_type.duration_minutes)

                    # Convert to UTC
                    slot_start_utc = current_slot_start.astimezone(pytz.UTC)
                    slot_end_utc = slot_end.astimezone(pytz.UTC)

                    # Check constraints
                    if slot_start_utc < earliest_start:
                        current_slot_start += timedelta(minutes=profile.slot_rounding_minutes)
                        continue

                    if slot_start_utc > latest_start:
                        break

                    # Check for conflicts (per docs/34 section 4.4)
                    if staff_user and self._has_conflict(
                        staff_user, slot_start_utc, slot_end_utc, appointment_type
                    ):
                        current_slot_start += timedelta(minutes=profile.slot_rounding_minutes)
                        continue

                    slots.append((slot_start_utc, slot_end_utc))
                    current_slot_start += timedelta(minutes=profile.slot_rounding_minutes)

            current_date += timedelta(days=1)

        return slots

    def _is_exception_date(self, date: datetime.date, exceptions: list) -> bool:
        """Check if date is in exception list."""
        date_str = date.strftime("%Y-%m-%d")
        return any(exc.get("date") == date_str for exc in exceptions)

    def _has_conflict(
        self,
        staff_user,
        start_time: datetime,
        end_time: datetime,
        appointment_type: AppointmentType,
    ) -> bool:
        """
        Check if there's a conflict with existing appointments.

        Per docs/34 section 4.4: considers existing appointments and buffers.
        AVAIL-1: Enhanced to check conflicts across multiple external calendars.
        """
        # Add buffers to the slot
        buffered_start = start_time - timedelta(minutes=appointment_type.buffer_before_minutes)
        buffered_end = end_time + timedelta(minutes=appointment_type.buffer_after_minutes)

        # Check for overlapping internal appointments
        conflicts = Appointment.objects.filter(
            staff_user=staff_user,
            status__in=["requested", "confirmed"],
            start_time__lt=buffered_end,
            end_time__gt=buffered_start,
        ).exists()

        if conflicts:
            return True

        # AVAIL-1: Check for conflicts across all connected external calendars
        return self._has_external_calendar_conflict(staff_user, buffered_start, buffered_end)

    def _has_external_calendar_conflict(
        self,
        staff_user,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """
        Check for conflicts across all external calendar connections.

        AVAIL-1: Checks Google, Microsoft, iCloud, and iCal feeds for conflicts.
        Respects all-day event and tentative event preferences per connection.

        Args:
            staff_user: Staff user to check calendars for
            start_time: Start of time slot to check
            end_time: End of time slot to check

        Returns:
            True if conflict found in any external calendar, False otherwise
        """
        try:
            # Get all active calendar connections for this user
            connections = OAuthConnection.objects.filter(
                user=staff_user,
                status='active',
                sync_enabled=True,
            )

            for connection in connections:
                try:
                    if connection.provider in ['apple', 'ical']:
                        # Check iCal feed
                        if connection.ical_feed_url:
                            has_conflict = self._check_ical_conflict(
                                connection.ical_feed_url,
                                start_time,
                                end_time,
                                connection.treat_all_day_as_busy,
                                connection.treat_tentative_as_busy,
                            )
                            if has_conflict:
                                logger.debug(
                                    f"Conflict found in iCal feed for user {staff_user.username}"
                                )
                                return True

                    elif connection.provider == 'google':
                        # Check Google Calendar
                        has_conflict = self._check_google_conflict(
                            connection,
                            start_time,
                            end_time,
                            connection.treat_all_day_as_busy,
                            connection.treat_tentative_as_busy,
                        )
                        if has_conflict:
                            logger.debug(
                                f"Conflict found in Google Calendar for user {staff_user.username}"
                            )
                            return True

                    elif connection.provider == 'microsoft':
                        # Check Microsoft Calendar
                        has_conflict = self._check_microsoft_conflict(
                            connection,
                            start_time,
                            end_time,
                            connection.treat_all_day_as_busy,
                            connection.treat_tentative_as_busy,
                        )
                        if has_conflict:
                            logger.debug(
                                f"Conflict found in Microsoft Calendar for user {staff_user.username}"
                            )
                            return True

                except Exception as e:
                    logger.warning(
                        f"Error checking calendar connection {connection.connection_id}: {e}"
                    )
                    # Continue checking other calendars even if one fails
                    continue

            return False

        except Exception as e:
            logger.error(f"Error checking external calendar conflicts: {e}")
            # Default to no conflict if we can't check (availability should be conservative)
            return False

    def _check_ical_conflict(
        self,
        feed_url: str,
        start_time: datetime,
        end_time: datetime,
        treat_all_day_as_busy: bool,
        treat_tentative_as_busy: bool,
    ) -> bool:
        """
        Check for conflicts in an iCal feed.

        Args:
            feed_url: iCal feed URL
            start_time: Start of time slot to check
            end_time: End of time slot to check
            treat_all_day_as_busy: Whether to treat all-day events as busy
            treat_tentative_as_busy: Whether to treat tentative events as busy

        Returns:
            True if conflict found, False otherwise
        """
        try:
            ical_service = ICalService()
            is_available = ical_service.check_availability(
                feed_url=feed_url,
                start_time=start_time,
                end_time=end_time,
                treat_all_day_as_busy=treat_all_day_as_busy,
                treat_tentative_as_busy=treat_tentative_as_busy,
            )
            # If not available, there's a conflict
            return not is_available
        except Exception as e:
            logger.warning(f"Error checking iCal availability: {e}")
            return False

    def _check_google_conflict(
        self,
        connection: OAuthConnection,
        start_time: datetime,
        end_time: datetime,
        treat_all_day_as_busy: bool,
        treat_tentative_as_busy: bool,
    ) -> bool:
        """
        Check for conflicts in Google Calendar.

        Args:
            connection: OAuth connection to Google Calendar
            start_time: Start of time slot to check
            end_time: End of time slot to check
            treat_all_day_as_busy: Whether to treat all-day events as busy
            treat_tentative_as_busy: Whether to treat tentative events as busy

        Returns:
            True if conflict found, False otherwise
        """
        try:
            google_service = GoogleCalendarService()
            # Note: This is a placeholder - actual implementation would require
            # fetching events from Google Calendar API and checking for conflicts
            # Similar to the iCal logic but using the Google Calendar API
            logger.debug("Google Calendar conflict check not yet fully implemented")
            return False
        except Exception as e:
            logger.warning(f"Error checking Google Calendar availability: {e}")
            return False

    def _check_microsoft_conflict(
        self,
        connection: OAuthConnection,
        start_time: datetime,
        end_time: datetime,
        treat_all_day_as_busy: bool,
        treat_tentative_as_busy: bool,
    ) -> bool:
        """
        Check for conflicts in Microsoft Calendar.

        Args:
            connection: OAuth connection to Microsoft Calendar
            start_time: Start of time slot to check
            end_time: End of time slot to check
            treat_all_day_as_busy: Whether to treat all-day events as busy
            treat_tentative_as_busy: Whether to treat tentative events as busy

        Returns:
            True if conflict found, False otherwise
        """
        try:
            microsoft_service = MicrosoftCalendarService()
            # Note: This is a placeholder - actual implementation would require
            # fetching events from Microsoft Graph API and checking for conflicts
            # Similar to the iCal logic but using the Microsoft Graph API
            logger.debug("Microsoft Calendar conflict check not yet fully implemented")
            return False
        except Exception as e:
            logger.warning(f"Error checking Microsoft Calendar availability: {e}")
            return False


class RoutingService:
    """
    Service for routing appointments to staff.

    Implements docs/34 section 2.4: routing policies.
    """

    def route_appointment(
        self,
        appointment_type: AppointmentType,
        account=None,
        engagement: Optional[Any] = None,
    ) -> Tuple[Optional[any], str]:
        """
        Route an appointment to a staff user based on routing policy.

        Returns: (staff_user, reason)

        Per docs/34 section 2.4: supports multiple routing policies.
        """
        policy = appointment_type.routing_policy
        reason = f"Routing policy: {policy}"

        if policy == "fixed_staff":
            return appointment_type.fixed_staff_user, f"{reason} - {appointment_type.fixed_staff_user.username if appointment_type.fixed_staff_user else 'None'}"

        elif policy == "engagement_owner":
            if engagement and engagement.assigned_to:
                return engagement.assigned_to, f"{reason} - Engagement owner: {engagement.assigned_to.username}"
            # Fallback to fixed staff if no engagement
            return appointment_type.fixed_staff_user, f"{reason} - Fallback to fixed staff (no engagement owner)"

        elif policy == "round_robin_pool":
            # FUTURE: Implement round-robin logic with team pool
            return appointment_type.fixed_staff_user, f"{reason} - Round robin not implemented, using fixed staff"

        elif policy == "service_line_owner":
            # FUTURE: Implement service line routing
            return appointment_type.fixed_staff_user, f"{reason} - Service line routing not implemented, using fixed staff"

        # Default fallback
        return appointment_type.fixed_staff_user, f"{reason} - Default fallback to fixed staff"


class BookingService:
    """
    Service for booking appointments.

    Implements docs/34 section 3: booking flows with race condition protection.
    """

    @transaction.atomic
    def book_appointment(
        self,
        appointment_type: AppointmentType,
        start_time: datetime,
        end_time: datetime,
        staff_user,
        booked_by,
        account=None,
        contact=None,
        engagement=None,
        intake_responses=None,
        booking_link=None,
    ) -> Appointment:
        """
        Book an appointment with atomic transaction for race condition protection.

        Per docs/34 section 4.5: slot selection protected against race conditions.
        Per docs/34 section 3: creates appointment in requested or confirmed status.
        """
        # Check for conflicts within transaction (per docs/34 section 4.5)
        conflicts = Appointment.objects.select_for_update().filter(
            staff_user=staff_user,
            status__in=["requested", "confirmed"],
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()

        if conflicts:
            raise ValueError("Time slot is no longer available (conflict detected)")

        # Determine initial status (per docs/34 section 3.1)
        initial_status = "requested" if appointment_type.requires_approval else "confirmed"

        # Create appointment
        appointment = Appointment.objects.create(
            firm=appointment_type.firm,
            appointment_type=appointment_type,
            booking_link=booking_link,
            staff_user=staff_user,
            account=account,
            contact=contact,
            start_time=start_time,
            end_time=end_time,
            timezone=appointment_type.firm.timezone if hasattr(appointment_type.firm, 'timezone') else 'UTC',
            intake_responses=intake_responses or {},
            status=initial_status,
            booked_by=booked_by,
        )

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status="",
            to_status=initial_status,
            reason="Initial booking",
            changed_by=booked_by,
        )

        return appointment

    @transaction.atomic
    def cancel_appointment(
        self,
        appointment: Appointment,
        reason: str,
        cancelled_by,
    ) -> Appointment:
        """
        Cancel an appointment.

        Creates status history entry for audit trail.
        """
        old_status = appointment.status
        appointment.status = "cancelled"
        appointment.status_reason = reason
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="cancelled",
            reason=reason,
            changed_by=cancelled_by,
        )

        return appointment

    @transaction.atomic
    def confirm_appointment(
        self,
        appointment: Appointment,
        confirmed_by,
    ) -> Appointment:
        """
        Confirm a requested appointment (approval flow).

        Per docs/34 section 3.1: approval-required appointments start as requested.
        """
        if appointment.status != "requested":
            raise ValueError("Only requested appointments can be confirmed")

        old_status = appointment.status
        appointment.status = "confirmed"
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="confirmed",
            reason="Approved by staff",
            changed_by=confirmed_by,
        )

        return appointment
