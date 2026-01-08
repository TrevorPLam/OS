"""Round robin routing services for calendar appointments."""

import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from .availability_service import AvailabilityService
from .models import Appointment, AppointmentType, AvailabilityProfile

logger = logging.getLogger(__name__)


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
