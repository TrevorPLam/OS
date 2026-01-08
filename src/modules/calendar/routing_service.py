"""Appointment routing services for calendar scheduling."""

import logging
from datetime import datetime
from typing import Any, Optional, Tuple

from .models import AppointmentType
from .round_robin_service import RoundRobinService

logger = logging.getLogger(__name__)


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
            return appointment_type.fixed_staff_user, (
                f"{reason} - {appointment_type.fixed_staff_user.username if appointment_type.fixed_staff_user else 'None'}"
            )

        if policy == "engagement_owner":
            if engagement and engagement.assigned_to:
                return engagement.assigned_to, (
                    f"{reason} - Engagement owner: {engagement.assigned_to.username}"
                )
            # Fallback to fixed staff if no engagement
            return appointment_type.fixed_staff_user, (
                f"{reason} - Fallback to fixed staff (no engagement owner)"
            )

        if policy == "round_robin_pool":
            # TEAM-2: Implement advanced round-robin logic with multiple strategies
            if not start_time or not end_time:
                logger.warning("Round robin routing requires start_time and end_time")
                return appointment_type.fixed_staff_user, (
                    f"{reason} - Missing time info, using fixed staff"
                )

            round_robin_service = RoundRobinService()
            staff_user, rr_reason = round_robin_service.select_round_robin_staff(
                appointment_type=appointment_type,
                start_time=start_time,
                end_time=end_time,
            )

            if staff_user:
                return staff_user, f"{reason} - {rr_reason}"

            # Fallback if no one is available
            logger.warning(
                f"Round robin failed: {rr_reason}, falling back to fixed staff"
            )
            return appointment_type.fixed_staff_user, (
                f"{reason} - Round robin fallback: {rr_reason}"
            )

        if policy == "service_line_owner":
            # FUTURE: Implement service line routing
            return appointment_type.fixed_staff_user, (
                f"{reason} - Service line routing not implemented, using fixed staff"
            )

        # Default fallback
        return appointment_type.fixed_staff_user, (
            f"{reason} - Default fallback to fixed staff"
        )
