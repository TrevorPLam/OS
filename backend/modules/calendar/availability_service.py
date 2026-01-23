"""
Calendar availability services.

Provides availability computation, routing, and booking logic.
Implements docs/03-reference/requirements/DOC-34.md sections 2.4, 3, and 4.
Enhanced with AVAIL-1: Multiple calendar support and external calendar conflict checking.
Enhanced with AVAIL-2: Comprehensive availability rules (recurring unavailability, holidays, meeting gaps).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Tuple, Optional

import pytz
from django.utils import timezone

from .holiday_service import HolidayService
from .google_service import GoogleCalendarService
from .ical_service import ICalService
from .microsoft_service import MicrosoftCalendarService
from .models import Appointment, AppointmentType, AvailabilityProfile
from .oauth_models import OAuthConnection

logger = logging.getLogger(__name__)


class AvailabilityService:
    """
    Service for computing available slots.

    Implements docs/03-reference/requirements/DOC-34.md section 4: availability computation with buffers and constraints.

    Meta-commentary:
    - **Current Status:** External conflict checks for Google/Microsoft are placeholders; only iCal and internal overlap checks enforce conflicts today.
    - **Follow-up (T-067):** Add provider event→appointment mapping with sync cursors so stale external mappings and cancelled events stop surfacing as available slots.
    - **Assumption:** OAuth connections supply up-to-date availability; missing backfill means stale tokens or paused sync can yield optimistic availability windows.
    - **Limitation:** Conflict detection is single-staff focused and does not reconcile simultaneous edits across multiple connected calendars.
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

        Per docs/03-reference/requirements/DOC-34.md section 4:
        1. Availability computed in profile timezone
        2. Buffers enforced
        3. Min notice and max future booking enforced
        4. Conflicts with existing appointments considered
        """
        # Get profile timezone
        profile_tz = pytz.timezone(profile.timezone)
        now = timezone.now()

        # Enforce min notice (per docs/03-reference/requirements/DOC-34.md section 4.3)
        earliest_start = now + timedelta(minutes=profile.min_notice_minutes)

        # Enforce max future booking (per docs/03-reference/requirements/DOC-34.md section 4.3)
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

            # AVAIL-2: Check if day is a holiday
            if profile.auto_detect_holidays or profile.custom_holidays:
                if self._is_holiday(current_date, profile):
                    current_date += timedelta(days=1)
                    continue

            # Get weekly hours for this day
            day_name = current_date.strftime("%A").lower()
            day_hours = profile.weekly_hours.get(day_name, [])

            # AVAIL-2: Apply recurring unavailability blocks
            day_hours = self._apply_recurring_unavailability(
                day_hours, day_name, profile.recurring_unavailability
            )

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

                    # Check for conflicts (per docs/03-reference/requirements/DOC-34.md section 4.4)
                    if staff_user and self._has_conflict(
                        staff_user, slot_start_utc, slot_end_utc, appointment_type, profile
                    ):
                        current_slot_start += timedelta(minutes=profile.slot_rounding_minutes)
                        continue

                    slots.append((slot_start_utc, slot_end_utc))
                    current_slot_start += timedelta(minutes=profile.slot_rounding_minutes)

            current_date += timedelta(days=1)

        return slots

    def compute_collective_available_slots(
        self,
        appointment_type: AppointmentType,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> List[Tuple[datetime, datetime, List[any]]]:
        """
        Compute available slots for collective events (multiple hosts, overlapping availability).

        TEAM-1: Implements Venn diagram availability logic where slots are only available
        when ALL required hosts are free. Optional hosts are not required for availability.

        Args:
            appointment_type: AppointmentType with event_category="collective"
            start_date: Start date for availability search
            end_date: End date for availability search

        Returns:
            List of (start_time, end_time, available_hosts) tuples in UTC.
            available_hosts includes all required hosts plus any optional hosts who are available.
        """
        if appointment_type.event_category != "collective":
            raise ValueError("compute_collective_available_slots only works with collective event types")

        # Get required and optional hosts
        required_hosts = list(appointment_type.required_hosts.all())
        optional_hosts = list(appointment_type.optional_hosts.all())

        if not required_hosts:
            logger.warning(f"Collective event {appointment_type.name} has no required hosts")
            return []

        # Get availability profiles for all hosts
        host_profiles = {}
        for host in required_hosts + optional_hosts:
            try:
                profile = AvailabilityProfile.objects.get(
                    firm=appointment_type.firm,
                    owner_type="staff",
                    owner_staff_user=host,
                )
                host_profiles[host.id] = profile
            except AvailabilityProfile.DoesNotExist:
                if host in required_hosts:
                    logger.warning(f"Required host {host.username} has no availability profile, cannot compute collective slots.")
                    return []
                logger.warning(f"No availability profile for optional host {host.username}")
        if not host_profiles:
            return []

        # Get available slots for each host
        host_slots = {}
        for host_id, profile in host_profiles.items():
            try:
                host = next(h for h in required_hosts + optional_hosts if h.id == host_id)
                slots = self.compute_available_slots(
                    profile=profile,
                    appointment_type=appointment_type,
                    start_date=start_date,
                    end_date=end_date,
                    staff_user=host,
                )
                host_slots[host_id] = set(slots)
            except Exception as e:
                logger.warning(f"Error computing slots for host {host_id}: {e}")
                host_slots[host_id] = set()

        # Find overlapping slots for required hosts
        collective_slots = []

        # Create a list of slot sets for each required host
        required_host_slot_sets = [
            host_slots.get(host.id, set()) for host in required_hosts
        ]

        # If any required host has no slots, no collective availability
        if any(not slots for slots in required_host_slot_sets):
            return []

        # Find intersection of all required host slots
        overlapping_slots = required_host_slot_sets[0].copy()
        for other_slots in required_host_slot_sets[1:]:
            overlapping_slots.intersection_update(other_slots)

        if not overlapping_slots:
            return []

        # For each overlapping slot, determine which optional hosts are also available
        for slot_start, slot_end in sorted(list(overlapping_slots)):
            available_hosts = list(required_hosts)

            for optional_host in optional_hosts:
                optional_slots_set = host_slots.get(optional_host.id, set())
                if (slot_start, slot_end) in optional_slots_set:
                    available_hosts.append(optional_host)

            collective_slots.append((slot_start, slot_end, available_hosts))

        return collective_slots

    def _is_exception_date(self, date, exceptions: List[str]) -> bool:
        """Check if a date is in the exception list."""
        if not exceptions:
            return False

        # Convert date to string format for comparison
        date_str = date.isoformat()
        return date_str in exceptions

    def _is_holiday(self, date, profile: AvailabilityProfile) -> bool:
        """Check if a date is a holiday."""
        try:
            holiday_service = HolidayService()

            # Check custom holidays first
            if profile.custom_holidays:
                date_str = date.isoformat()
                if date_str in profile.custom_holidays:
                    return True

            # Check auto-detected holidays
            if profile.auto_detect_holidays:
                return holiday_service.is_holiday(date, profile.country_code)

            return False
        except Exception as e:
            logger.warning(f"Error checking holidays: {e}")
            return False

    def _apply_recurring_unavailability(
        self,
        day_hours: list,
        day_name: str,
        recurring_unavailability: dict,
    ) -> list:
        """
        Apply recurring unavailability blocks to day hours.

        Args:
            day_hours: List of time slots for the day
            day_name: Name of day (monday, tuesday, etc.)
            recurring_unavailability: Dict of recurring unavailability

        Returns:
            Modified day_hours list
        """
        if not recurring_unavailability:
            return day_hours

        day_blocks = recurring_unavailability.get(day_name, [])
        if not day_blocks:
            return day_hours

        # Convert time slots to list of (start, end) tuples for easier manipulation
        result_hours = []
        for slot in day_hours:
            result_hours.append({"start": slot.get("start"), "end": slot.get("end")})

        # Apply each unavailability block
        for block in day_blocks:
            block_start = block.get("start")
            block_end = block.get("end")

            if not block_start or not block_end:
                continue

            # Split any overlapping slots
            new_result_hours = []
            for slot in result_hours:
                slot_start = slot.get("start")
                slot_end = slot.get("end")

                # Skip invalid slots
                if not slot_start or not slot_end:
                    continue

                # Case 1: No overlap - keep slot as is
                if slot_end <= block_start or slot_start >= block_end:
                    new_result_hours.append(slot)
                    continue

                # Case 2: Block fully covers slot - remove slot
                if block_start <= slot_start and block_end >= slot_end:
                    continue

                # Case 3: Block splits slot - create two slots
                if block_start > slot_start and block_end < slot_end:
                    new_result_hours.append({"start": slot_start, "end": block_start})
                    new_result_hours.append({"start": block_end, "end": slot_end})
                    continue

                # Case 4: Block overlaps start of slot - shorten slot
                if block_start <= slot_start and block_end < slot_end:
                    new_result_hours.append({"start": block_end, "end": slot_end})
                    continue

                # Case 5: Block overlaps end of slot - shorten slot
                if block_start > slot_start and block_end >= slot_end:
                    new_result_hours.append({"start": slot_start, "end": block_start})
                    continue

            result_hours = new_result_hours

        return result_hours

    def _has_conflict(
        self,
        staff_user,
        start_time: datetime,
        end_time: datetime,
        appointment_type: AppointmentType,
        profile: Optional[AvailabilityProfile] = None,
    ) -> bool:
        """
        Check for conflicts for a staff user.

        Per docs/03-reference/requirements/DOC-34.md section 4.4: checks internal appointments and external calendars.

        Returns True if any conflict found, False otherwise.
        """
        # Check internal appointments first
        internal_conflict = Appointment.objects.filter(
            staff_user=staff_user,
            status__in=["requested", "confirmed"],
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()

        if internal_conflict:
            return True

        if profile is None:
            try:
                profile = AvailabilityProfile.objects.get(
                    firm=appointment_type.firm,
                    owner_type="staff",
                    owner_staff_user=staff_user,
                )
            except AvailabilityProfile.DoesNotExist:
                return False

        # Check external calendar conflicts if enabled
        if profile.check_external_calendars:
            connections = OAuthConnection.objects.filter(
                user=staff_user,
                is_active=True,
            )

            for connection in connections:
                if connection.provider == "google":
                    if self._check_google_conflict(
                        connection,
                        start_time,
                        end_time,
                        profile.treat_all_day_as_busy,
                        profile.treat_tentative_as_busy,
                    ):
                        return True
                elif connection.provider == "microsoft":
                    if self._check_microsoft_conflict(
                        connection,
                        start_time,
                        end_time,
                        profile.treat_all_day_as_busy,
                        profile.treat_tentative_as_busy,
                    ):
                        return True
                elif connection.provider == "ical":
                    # Check iCal feed
                    if connection.ical_feed_url:
                        if self._check_ical_conflict(
                            connection.ical_feed_url,
                            start_time,
                            end_time,
                            profile.treat_all_day_as_busy,
                            profile.treat_tentative_as_busy,
                        ):
                            return True

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
