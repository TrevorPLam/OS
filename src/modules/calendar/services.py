"""
Calendar Services.

Provides availability computation, routing, and booking logic.
Implements docs/34 sections 2.4, 3, and 4.
Enhanced with AVAIL-1: Multiple calendar support and external calendar conflict checking.
Enhanced with AVAIL-2: Comprehensive availability rules (recurring unavailability, holidays, meeting gaps).
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
from .holiday_service import HolidayService

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

                    # Check for conflicts (per docs/34 section 4.4)
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
                    # Required host has no profile - cannot find availability
                    logger.warning(
                        f"Required host {host.username} has no availability profile "
                        f"for collective event {appointment_type.name}"
                    )
                    return []

        # Compute slots for each required host
        required_host_slots = {}
        for host in required_hosts:
            profile = host_profiles.get(host.id)
            if not profile:
                return []  # Already logged warning above

            slots = self.compute_available_slots(
                profile=profile,
                appointment_type=appointment_type,
                start_date=start_date,
                end_date=end_date,
                staff_user=host,
            )
            required_host_slots[host.id] = set(slots)

        if not required_host_slots:
            return []

        # Find overlapping slots (Venn diagram intersection) for all required hosts
        # Start with first host's slots
        first_host_id = list(required_host_slots.keys())[0]
        overlapping_slots = required_host_slots[first_host_id].copy()

        # Intersect with each other required host's slots
        for host_id, host_slots in required_host_slots.items():
            if host_id == first_host_id:
                continue
            overlapping_slots = overlapping_slots.intersection(host_slots)

        if not overlapping_slots:
            logger.debug(f"No overlapping slots found for collective event {appointment_type.name}")
            return []

        # For each overlapping slot, determine which optional hosts are also available
        result = []
        for slot_start, slot_end in sorted(overlapping_slots):
            available_hosts = required_hosts.copy()

            # Check optional hosts
            for opt_host in optional_hosts:
                profile = host_profiles.get(opt_host.id)
                if not profile:
                    continue

                # Check if optional host is available for this slot
                if not self._has_conflict(
                    opt_host, slot_start, slot_end, appointment_type, profile
                ):
                    available_hosts.append(opt_host)

            result.append((slot_start, slot_end, available_hosts))

        logger.info(
            f"Found {len(result)} overlapping slots for collective event {appointment_type.name} "
            f"with {len(required_hosts)} required hosts"
        )

        return result

    def _is_exception_date(self, date: datetime.date, exceptions: list) -> bool:
        """Check if date is in exception list."""
        date_str = date.strftime("%Y-%m-%d")
        return any(exc.get("date") == date_str for exc in exceptions)

    def _is_holiday(self, check_date: datetime.date, profile: AvailabilityProfile) -> bool:
        """
        Check if date is a holiday.

        AVAIL-2: Checks both auto-detected holidays and custom holidays.

        Args:
            check_date: Date to check
            profile: Availability profile with holiday settings

        Returns:
            True if date is a holiday, False otherwise
        """
        if not profile.auto_detect_holidays and not profile.custom_holidays:
            return False

        holiday_service = HolidayService()

        if profile.auto_detect_holidays:
            # Check auto-detected holidays
            is_holiday = holiday_service.is_holiday(
                check_date=check_date,
                timezone_name=profile.timezone,
                custom_holidays=profile.custom_holidays if profile.custom_holidays else None,
            )
            return is_holiday

        # Check only custom holidays
        if profile.custom_holidays:
            date_str = check_date.strftime("%Y-%m-%d")
            return any(h.get("date") == date_str for h in profile.custom_holidays)

        return False

    def _apply_recurring_unavailability(
        self,
        day_hours: List[dict],
        day_name: str,
        recurring_unavailability: list,
    ) -> List[dict]:
        """
        Apply recurring unavailability blocks to day hours.

        AVAIL-2: Removes time blocks that overlap with recurring unavailability.

        Args:
            day_hours: Available hours for the day [{start: '09:00', end: '17:00'}]
            day_name: Day of week (e.g., 'monday')
            recurring_unavailability: List of recurring blocks [{day_of_week: 'monday', start: '12:00', end: '13:00'}]

        Returns:
            Modified day hours with unavailability blocks removed
        """
        if not recurring_unavailability:
            return day_hours

        # Filter recurring blocks for this day
        day_blocks = [
            block for block in recurring_unavailability
            if block.get('day_of_week') == day_name
        ]

        if not day_blocks:
            return day_hours

        # For each unavailability block, subtract it from available hours
        result_hours = []
        for hour_slot in day_hours:
            start_str = hour_slot.get('start')
            end_str = hour_slot.get('end')

            if not start_str or not end_str:
                continue

            # Convert to minutes for easier calculation
            slot_start = self._time_to_minutes(start_str)
            slot_end = self._time_to_minutes(end_str)

            # Split the slot around each unavailability block
            segments = [(slot_start, slot_end)]

            for block in day_blocks:
                block_start = self._time_to_minutes(block.get('start'))
                block_end = self._time_to_minutes(block.get('end'))

                new_segments = []
                for seg_start, seg_end in segments:
                    # If block doesn't overlap, keep segment as-is
                    if block_end <= seg_start or block_start >= seg_end:
                        new_segments.append((seg_start, seg_end))
                    else:
                        # Block overlaps - split the segment
                        if seg_start < block_start:
                            # Keep part before block
                            new_segments.append((seg_start, block_start))
                        if block_end < seg_end:
                            # Keep part after block
                            new_segments.append((block_end, seg_end))

                segments = new_segments

            # Convert segments back to time strings
            for seg_start, seg_end in segments:
                if seg_end > seg_start:  # Only add non-empty segments
                    result_hours.append({
                        'start': self._minutes_to_time(seg_start),
                        'end': self._minutes_to_time(seg_end),
                    })

        return result_hours

    def _time_to_minutes(self, time_str: str) -> int:
        """Convert time string (HH:MM) to minutes since midnight."""
        hour, minute = map(int, time_str.split(':'))
        return hour * 60 + minute

    def _minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to time string (HH:MM)."""
        hour = minutes // 60
        minute = minutes % 60
        return f"{hour:02d}:{minute:02d}"

    def _has_conflict(
        self,
        staff_user,
        start_time: datetime,
        end_time: datetime,
        appointment_type: AppointmentType,
        profile: Optional[AvailabilityProfile] = None,
    ) -> bool:
        """
        Check if there's a conflict with existing appointments.

        Per docs/34 section 4.4: considers existing appointments and buffers.
        AVAIL-1: Enhanced to check conflicts across multiple external calendars.
        AVAIL-2: Enhanced to check min/max meeting gaps.
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

        # AVAIL-2: Check meeting gaps if profile provided
        if profile:
            if not self._meets_gap_requirements(
                staff_user, start_time, end_time, profile
            ):
                return True

        # AVAIL-1: Check for conflicts across all connected external calendars
        return self._has_external_calendar_conflict(staff_user, buffered_start, buffered_end)

    def _meets_gap_requirements(
        self,
        staff_user,
        start_time: datetime,
        end_time: datetime,
        profile: AvailabilityProfile,
    ) -> bool:
        """
        Check if proposed time slot meets min/max meeting gap requirements.

        AVAIL-2: Ensures meetings have appropriate spacing.

        Args:
            staff_user: Staff user to check
            start_time: Proposed start time
            end_time: Proposed end time
            profile: Availability profile with gap settings

        Returns:
            True if gap requirements are met, False otherwise
        """
        if profile.min_gap_between_meetings_minutes == 0 and not profile.max_gap_between_meetings_minutes:
            # No gap requirements
            return True

        # Find adjacent appointments
        # Before this slot
        before_appts = Appointment.objects.filter(
            staff_user=staff_user,
            status__in=["requested", "confirmed"],
            end_time__lte=start_time,
        ).order_by('-end_time')[:1]

        if before_appts:
            gap_before = (start_time - before_appts[0].end_time).total_seconds() / 60

            # Check minimum gap
            if gap_before < profile.min_gap_between_meetings_minutes:
                logger.debug(
                    f"Gap before ({gap_before} min) less than minimum "
                    f"({profile.min_gap_between_meetings_minutes} min)"
                )
                return False

            # Check maximum gap
            if profile.max_gap_between_meetings_minutes:
                if gap_before > profile.max_gap_between_meetings_minutes:
                    logger.debug(
                        f"Gap before ({gap_before} min) greater than maximum "
                        f"({profile.max_gap_between_meetings_minutes} min)"
                    )
                    return False

        # After this slot
        after_appts = Appointment.objects.filter(
            staff_user=staff_user,
            status__in=["requested", "confirmed"],
            start_time__gte=end_time,
        ).order_by('start_time')[:1]

        if after_appts:
            gap_after = (after_appts[0].start_time - end_time).total_seconds() / 60

            # Check minimum gap
            if gap_after < profile.min_gap_between_meetings_minutes:
                logger.debug(
                    f"Gap after ({gap_after} min) less than minimum "
                    f"({profile.min_gap_between_meetings_minutes} min)"
                )
                return False

            # Check maximum gap
            if profile.max_gap_between_meetings_minutes:
                if gap_after > profile.max_gap_between_meetings_minutes:
                    logger.debug(
                        f"Gap after ({gap_after} min) greater than maximum "
                        f"({profile.max_gap_between_meetings_minutes} min)"
                    )
                    return False

        return True

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


class RoundRobinService:
    """
    Service for advanced round robin distribution.

    TEAM-2: Implements multiple round robin strategies:
    - Strict round robin (equal distribution)
    - Optimize for availability (favor most available)
    - Weighted distribution (configurable weights)
    - Prioritize by capacity (route to least-booked)
    """

    def select_round_robin_staff(
        self,
        appointment_type: AppointmentType,
        start_time: datetime,
        end_time: datetime,
    ) -> Tuple[Optional[any], str]:
        """
        Select a staff member from the round robin pool based on the configured strategy.

        Args:
            appointment_type: AppointmentType with round_robin_pool
            start_time: Proposed appointment start time
            end_time: Proposed appointment end time

        Returns:
            Tuple of (selected_staff, reason_string)
        """
        pool = list(appointment_type.round_robin_pool.all())
        
        if not pool:
            logger.warning(f"Round robin pool is empty for appointment type {appointment_type.name}")
            return None, "No staff in round robin pool"

        strategy = appointment_type.round_robin_strategy or "strict"

        # Filter out staff who have conflicts
        available_staff = self._filter_available_staff(
            pool, start_time, end_time, appointment_type
        )

        if not available_staff:
            # Fallback: if no one is available, return None or implement fallback logic
            logger.warning(
                f"No staff available in round robin pool for {appointment_type.name} "
                f"at {start_time}"
            )
            return None, "No available staff in round robin pool"

        # Check capacity limits per day
        if appointment_type.round_robin_capacity_per_day:
            available_staff = self._filter_by_daily_capacity(
                available_staff,
                start_time,
                appointment_type,
            )

        if not available_staff:
            return None, "All staff have reached daily capacity limit"

        # Apply selection strategy
        if strategy == "strict":
            selected_staff, reason = self._strict_round_robin(
                available_staff, appointment_type
            )
        elif strategy == "optimize_availability":
            selected_staff, reason = self._optimize_for_availability(
                available_staff, start_time, end_time, appointment_type
            )
        elif strategy == "weighted":
            selected_staff, reason = self._weighted_distribution(
                available_staff, appointment_type
            )
        elif strategy == "prioritize_capacity":
            selected_staff, reason = self._prioritize_capacity(
                available_staff, start_time, appointment_type
            )
        else:
            # Default to strict
            selected_staff, reason = self._strict_round_robin(
                available_staff, appointment_type
            )

        # Check if rebalancing is needed
        if (
            appointment_type.round_robin_enable_rebalancing
            and self._needs_rebalancing(appointment_type)
        ):
            logger.info(
                f"Round robin pool for {appointment_type.name} needs rebalancing"
            )
            # Optionally trigger rebalancing logic or just log

        return selected_staff, f"Round robin ({strategy}): {reason}"

    def _filter_available_staff(
        self,
        staff_list: List[any],
        start_time: datetime,
        end_time: datetime,
        appointment_type: AppointmentType,
    ) -> List[any]:
        """Filter staff to only those available at the requested time."""
        available = []
        availability_service = AvailabilityService()

        for staff in staff_list:
            # Get availability profile
            try:
                profile = AvailabilityProfile.objects.get(
                    firm=appointment_type.firm,
                    owner_type="staff",
                    owner_staff_user=staff,
                )
            except AvailabilityProfile.DoesNotExist:
                logger.debug(f"No availability profile for {staff.username}, skipping")
                continue

            # Check for conflicts
            if not availability_service._has_conflict(
                staff, start_time, end_time, appointment_type, profile
            ):
                available.append(staff)

        return available

    def _filter_by_daily_capacity(
        self,
        staff_list: List[any],
        start_time: datetime,
        appointment_type: AppointmentType,
    ) -> List[any]:
        """Filter out staff who have reached daily capacity limit."""
        capacity_limit = appointment_type.round_robin_capacity_per_day
        if not capacity_limit:
            return staff_list

        # Get start of day for counting
        day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        available = []
        for staff in staff_list:
            # Count appointments for this staff on this day
            count = Appointment.objects.filter(
                appointment_type=appointment_type,
                staff_user=staff,
                start_time__gte=day_start,
                start_time__lt=day_end,
                status__in=["requested", "confirmed"],
            ).count()

            if count < capacity_limit:
                available.append(staff)
            else:
                logger.debug(
                    f"Staff {staff.username} has reached daily capacity "
                    f"({count}/{capacity_limit})"
                )

        return available

    def _strict_round_robin(
        self,
        staff_list: List[any],
        appointment_type: AppointmentType,
    ) -> Tuple[any, str]:
        """
        Strict round robin: distribute equally regardless of current load.
        
        Selects the staff member with the fewest total appointments for this type.
        """
        # Count appointments for each staff member
        staff_counts = []
        for staff in staff_list:
            count = Appointment.objects.filter(
                appointment_type=appointment_type,
                staff_user=staff,
                status__in=["requested", "confirmed"],
            ).count()
            staff_counts.append((staff, count))

        # Sort by count (ascending) to find least-assigned
        staff_counts.sort(key=lambda x: x[1])
        selected_staff, count = staff_counts[0]

        return selected_staff, f"{selected_staff.username} (fewest assignments: {count})"

    def _optimize_for_availability(
        self,
        staff_list: List[any],
        start_time: datetime,
        end_time: datetime,
        appointment_type: AppointmentType,
    ) -> Tuple[any, str]:
        """
        Optimize for availability: favor staff with more open slots.
        
        Calculates available slots for each staff member and selects the one with most availability.
        """
        availability_service = AvailabilityService()
        staff_availability = []

        # Look ahead 7 days to assess availability
        search_end = start_time.date() + timedelta(days=7)

        for staff in staff_list:
            try:
                profile = AvailabilityProfile.objects.get(
                    firm=appointment_type.firm,
                    owner_type="staff",
                    owner_staff_user=staff,
                )
                
                slots = availability_service.compute_available_slots(
                    profile=profile,
                    appointment_type=appointment_type,
                    start_date=start_time.date(),
                    end_date=search_end,
                    staff_user=staff,
                )
                
                staff_availability.append((staff, len(slots)))
            except AvailabilityProfile.DoesNotExist:
                staff_availability.append((staff, 0))

        # Sort by availability (descending) to find most available
        staff_availability.sort(key=lambda x: x[1], reverse=True)
        selected_staff, slot_count = staff_availability[0]

        return selected_staff, f"{selected_staff.username} (most available: {slot_count} slots)"

    def _weighted_distribution(
        self,
        staff_list: List[any],
        appointment_type: AppointmentType,
    ) -> Tuple[any, str]:
        """
        Weighted distribution: use configurable weights to favor certain staff.
        
        Higher weight = more appointments should be routed to that staff member.
        """
        weights = appointment_type.round_robin_weights or {}
        
        # Count appointments and calculate weighted ratios
        staff_ratios = []
        for staff in staff_list:
            weight = weights.get(str(staff.id), 1.0)  # Default weight 1.0
            
            count = Appointment.objects.filter(
                appointment_type=appointment_type,
                staff_user=staff,
                status__in=["requested", "confirmed"],
            ).count()
            
            # Ratio = actual count / expected count (based on weight)
            # Lower ratio = under-assigned relative to weight
            ratio = count / weight if weight > 0 else float('inf')
            staff_ratios.append((staff, ratio, weight, count))

        # Sort by ratio (ascending) to find most under-assigned relative to weight
        staff_ratios.sort(key=lambda x: x[1])
        selected_staff, ratio, weight, count = staff_ratios[0]

        return selected_staff, f"{selected_staff.username} (weight: {weight}, count: {count})"

    def _prioritize_capacity(
        self,
        staff_list: List[any],
        start_time: datetime,
        appointment_type: AppointmentType,
    ) -> Tuple[any, str]:
        """
        Prioritize by capacity: route to the person with the fewest bookings recently.
        
        Looks at bookings in the last 30 days to determine who is least busy.
        """
        lookback_start = start_time - timedelta(days=30)

        staff_recent_counts = []
        for staff in staff_list:
            count = Appointment.objects.filter(
                appointment_type=appointment_type,
                staff_user=staff,
                start_time__gte=lookback_start,
                status__in=["requested", "confirmed", "completed"],
            ).count()
            staff_recent_counts.append((staff, count))

        # Sort by recent count (ascending) to find least busy
        staff_recent_counts.sort(key=lambda x: x[1])
        selected_staff, count = staff_recent_counts[0]

        return selected_staff, f"{selected_staff.username} (least busy: {count} in last 30 days)"

    def _needs_rebalancing(self, appointment_type: AppointmentType) -> bool:
        """
        Check if round robin pool needs rebalancing.
        
        Returns True if any staff member is more than threshold% off the average.
        """
        pool = list(appointment_type.round_robin_pool.all())
        if len(pool) < 2:
            return False

        threshold = float(appointment_type.round_robin_rebalancing_threshold or 0.20)

        # Count appointments for each pool member
        counts = []
        for staff in pool:
            count = Appointment.objects.filter(
                appointment_type=appointment_type,
                staff_user=staff,
                status__in=["requested", "confirmed"],
            ).count()
            counts.append(count)

        if not counts:
            return False

        avg = sum(counts) / len(counts)
        
        # Check if any count deviates more than threshold from average
        for count in counts:
            if avg > 0:
                deviation = abs(count - avg) / avg
                if deviation > threshold:
                    return True

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
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Tuple[Optional[any], str]:
        """
        Route an appointment to a staff user based on routing policy.

        Returns: (staff_user, reason)

        Per docs/34 section 2.4: supports multiple routing policies.
        TEAM-2: Enhanced with advanced round robin support.
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
            # TEAM-2: Implement advanced round-robin logic with multiple strategies
            if not start_time or not end_time:
                logger.warning("Round robin routing requires start_time and end_time")
                return appointment_type.fixed_staff_user, f"{reason} - Missing time info, using fixed staff"
            
            round_robin_service = RoundRobinService()
            staff_user, rr_reason = round_robin_service.select_round_robin_staff(
                appointment_type=appointment_type,
                start_time=start_time,
                end_time=end_time,
            )
            
            if staff_user:
                return staff_user, f"{reason} - {rr_reason}"
            else:
                # Fallback if no one is available
                logger.warning(f"Round robin failed: {rr_reason}, falling back to fixed staff")
                return appointment_type.fixed_staff_user, f"{reason} - Round robin fallback: {rr_reason}"


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
    def book_collective_appointment(
        self,
        appointment_type: AppointmentType,
        start_time: datetime,
        end_time: datetime,
        collective_hosts: List[any],
        booked_by,
        account=None,
        contact=None,
        engagement=None,
        intake_responses=None,
        booking_link=None,
    ) -> Appointment:
        """
        Book a collective event appointment with multiple hosts.

        TEAM-1: Implements collective event booking with Venn diagram availability.
        Ensures all required hosts are available and books with all hosts atomically.

        Args:
            appointment_type: AppointmentType with event_category="collective"
            start_time: Start time for appointment
            end_time: End time for appointment
            collective_hosts: List of host users (required + available optional)
            booked_by: User who is booking the appointment
            account: Optional client account
            contact: Optional contact
            engagement: Optional engagement
            intake_responses: Optional intake question responses
            booking_link: Optional booking link used

        Returns:
            Created Appointment instance

        Raises:
            ValueError: If conflicts detected for any host
        """
        if appointment_type.event_category != "collective":
            raise ValueError("book_collective_appointment only works with collective event types")

        if not collective_hosts:
            raise ValueError("Collective events require at least one host")

        # Check for conflicts for ALL hosts within transaction (race condition protection)
        for host in collective_hosts:
            conflicts = Appointment.objects.select_for_update().filter(
                staff_user=host,
                status__in=["requested", "confirmed"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            ).exists()

            # Also check if host is in collective_hosts of other appointments
            collective_conflicts = Appointment.objects.select_for_update().filter(
                collective_hosts=host,
                status__in=["requested", "confirmed"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            ).exists()

            if conflicts or collective_conflicts:
                raise ValueError(
                    f"Time slot is no longer available for host {host.username} (conflict detected)"
                )

        # Determine initial status
        initial_status = "requested" if appointment_type.requires_approval else "confirmed"

        # Use the first required host as the primary staff_user for backward compatibility
        required_hosts = list(appointment_type.required_hosts.all())
        primary_staff_user = required_hosts[0] if required_hosts else collective_hosts[0]

        # Create appointment
        appointment = Appointment.objects.create(
            firm=appointment_type.firm,
            appointment_type=appointment_type,
            booking_link=booking_link,
            staff_user=primary_staff_user,
            account=account,
            contact=contact,
            start_time=start_time,
            end_time=end_time,
            timezone=appointment_type.firm.timezone if hasattr(appointment_type.firm, 'timezone') else 'UTC',
            intake_responses=intake_responses or {},
            status=initial_status,
            booked_by=booked_by,
        )

        # Add all collective hosts
        appointment.collective_hosts.set(collective_hosts)

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status="",
            to_status=initial_status,
            reason=f"Initial collective event booking with {len(collective_hosts)} hosts",
            changed_by=booked_by,
        )

        logger.info(
            f"Booked collective appointment {appointment.appointment_id} "
            f"with {len(collective_hosts)} hosts: {[h.username for h in collective_hosts]}"
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

    @transaction.atomic
    def mark_no_show(
        self,
        appointment: Appointment,
        marked_by,
        party: str = "client",
        reason: str = "",
    ) -> Appointment:
        """
        Mark an appointment as no-show.

        FLOW-2: Enables no-show follow-up workflows.

        Args:
            appointment: Appointment to mark as no-show
            marked_by: User marking the no-show
            party: Who didn't show up ("client" or "staff")
            reason: Optional reason for no-show

        Returns:
            Updated Appointment instance
        """
        if appointment.status not in ["confirmed", "requested"]:
            raise ValueError("Only confirmed or requested appointments can be marked as no-show")

        old_status = appointment.status
        appointment.status = "no_show"
        appointment.status_reason = reason
        appointment.no_show_at = timezone.now()
        appointment.no_show_party = party
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="no_show",
            reason=f"No-show by {party}" + (f": {reason}" if reason else ""),
            changed_by=marked_by,
        )

        logger.info(
            f"Marked appointment {appointment.appointment_id} as no-show ({party})"
        )

        # Trigger no-show workflows
        from .workflow_services import WorkflowExecutionEngine
        engine = WorkflowExecutionEngine()
        engine.trigger_workflows(
            appointment=appointment,
            trigger_event="appointment_no_show",
            actor=marked_by,
        )

        return appointment

    @transaction.atomic
    def complete_appointment(
        self,
        appointment: Appointment,
        completed_by,
        notes: str = "",
    ) -> Appointment:
        """
        Mark an appointment as completed.

        FLOW-2: Triggers post-meeting follow-up workflows.

        Args:
            appointment: Appointment to complete
            completed_by: User marking as complete
            notes: Optional completion notes

        Returns:
            Updated Appointment instance
        """
        if appointment.status not in ["confirmed"]:
            raise ValueError("Only confirmed appointments can be marked as completed")

        old_status = appointment.status
        appointment.status = "completed"
        if notes:
            appointment.notes = (appointment.notes or "") + "\n\n" + notes
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="completed",
            reason="Marked as completed" + (f": {notes}" if notes else ""),
            changed_by=completed_by,
        )

        logger.info(f"Completed appointment {appointment.appointment_id}")

        # Trigger completion workflows (thank you emails, surveys, etc.)
        from .workflow_services import WorkflowExecutionEngine
        engine = WorkflowExecutionEngine()
        engine.trigger_workflows(
            appointment=appointment,
            trigger_event="appointment_completed",
            actor=completed_by,
        )

        return appointment

    @transaction.atomic
    def substitute_collective_host(
        self,
        appointment: Appointment,
        old_host,
        new_host,
        substituted_by,
        reason: str = "",
    ) -> Appointment:
        """
        Substitute a host in a collective event appointment.

        TEAM-1: Implements host substitution workflow for collective events.
        Validates that the new host is available and atomically updates the appointment.

        Args:
            appointment: Appointment to modify
            old_host: Host to remove
            new_host: Host to add as replacement
            substituted_by: User performing the substitution
            reason: Optional reason for substitution

        Returns:
            Updated Appointment instance

        Raises:
            ValueError: If not a collective event, host not found, or new host has conflict
        """
        if appointment.appointment_type.event_category != "collective":
            raise ValueError("Host substitution only applies to collective events")

        # Check that old_host is actually in the appointment
        if old_host not in appointment.collective_hosts.all():
            raise ValueError(f"Host {old_host.username} is not assigned to this appointment")

        # Check that new_host doesn't have a conflict
        conflicts = Appointment.objects.select_for_update().filter(
            staff_user=new_host,
            status__in=["requested", "confirmed"],
            start_time__lt=appointment.end_time,
            end_time__gt=appointment.start_time,
        ).exists()

        collective_conflicts = Appointment.objects.select_for_update().filter(
            collective_hosts=new_host,
            status__in=["requested", "confirmed"],
            start_time__lt=appointment.end_time,
            end_time__gt=appointment.start_time,
        ).exists()

        if conflicts or collective_conflicts:
            raise ValueError(
                f"Cannot substitute: new host {new_host.username} has a conflicting appointment"
            )

        # Remove old host and add new host
        appointment.collective_hosts.remove(old_host)
        appointment.collective_hosts.add(new_host)

        # Update primary staff_user if the old host was primary
        if appointment.staff_user == old_host:
            appointment.staff_user = new_host
            appointment.save()

        # Create audit trail in status history
        substitution_reason = reason or f"Host substitution: {old_host.username} → {new_host.username}"
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=appointment.status,
            to_status=appointment.status,
            reason=substitution_reason,
            changed_by=substituted_by,
        )

        logger.info(
            f"Substituted host in appointment {appointment.appointment_id}: "
            f"{old_host.username} → {new_host.username}"
        )

        return appointment


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

        else:
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
        cal.add('prodid', '-//ConsultantPro//Calendar Invitation//EN')
        cal.add('version', '2.0')
        cal.add('method', method)

        # Create event
        event = Event()
        
        # Add basic event details
        event.add('uid', f'appointment-{appointment.appointment_id}@consultantpro.app')
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
        elif location_mode == "phone":
            if location_details:
                return f"Phone: {location_details}"
            return "Phone Call"
        elif location_mode == "in_person":
            if location_details:
                return location_details
            return "In Person"
        elif location_mode == "custom":
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

