"""
Recurrence Backfill Service (DOC-10.2)

Implements backfill operations for missed recurrence periods during pause.

Per docs/03-reference/requirements/DOC-10.md section 7.2:
- Backfill operation MUST be permission-gated
- MUST be auditable
- MUST be bounded by specified time range
- Generates RecurrenceGeneration rows for missed periods

This service allows filling gaps when a recurrence was paused
and the user wants to catch up on missed instances.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from modules.recurrence.models import RecurrenceRule, RecurrenceGeneration
from modules.recurrence.generator import RecurrenceGenerator
from modules.firm.audit import audit


@dataclass
class BackfillResult:
    """Result of a backfill operation."""

    recurrence_rule_id: int
    start_date: datetime
    end_date: datetime
    periods_created: int
    periods_skipped: int  # Already existed
    generation_ids: List[int]
    audit_event_id: Optional[int] = None


class BackfillService:
    """
    Service for backfilling missed recurrence periods.

    DOC-10.2: Implements backfill operation with permission gating and audit trail.
    """

    def __init__(self):
        """Initialize backfill service."""
        self.generator = RecurrenceGenerator()

    @transaction.atomic
    def backfill_missed_periods(
        self,
        recurrence_rule: RecurrenceRule,
        start_date: datetime,
        end_date: datetime,
        user,
        reason: str,
    ) -> BackfillResult:
        """
        Backfill missed periods for a recurrence rule.

        Per docs/03-reference/requirements/DOC-10.md section 7.2:
        - Permission-gated (caller must verify permissions)
        - Auditable (creates audit event)
        - Bounded by time range

        Args:
            recurrence_rule: RecurrenceRule to backfill
            start_date: Start of backfill window (timezone-aware)
            end_date: End of backfill window (timezone-aware)
            user: User performing backfill (for audit)
            reason: Reason for backfill (for audit)

        Returns:
            BackfillResult with periods created and audit event ID

        Raises:
            ValueError: If rule is active (shouldn't backfill active rules)
            PermissionError: If user lacks permission (caller should check first)
        """
        # Validate rule status
        if recurrence_rule.status not in ["paused", "canceled"]:
            raise ValueError(
                f"Cannot backfill rule with status '{recurrence_rule.status}'. "
                "Only paused or canceled rules can be backfilled."
            )

        # Validate date range
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        # Validate date range is bounded (max 1 year for safety)
        max_backfill_days = 365
        if (end_date - start_date).days > max_backfill_days:
            raise ValueError(
                f"Backfill window exceeds maximum of {max_backfill_days} days. "
                f"Requested: {(end_date - start_date).days} days."
            )

        # Compute candidate periods in the backfill window
        periods_created = 0
        periods_skipped = 0
        generation_ids = []

        # Generate periods using the generator
        candidate_periods = self.generator.compute_periods(
            recurrence_rule=recurrence_rule,
            as_of=end_date,  # Use end_date as "now" for computation
            start_boundary=start_date,
            end_boundary=end_date,
        )

        for period in candidate_periods:
            # Try to create RecurrenceGeneration for this period
            generation, created = RecurrenceGeneration.objects.get_or_create(
                firm=recurrence_rule.firm,
                recurrence_rule=recurrence_rule,
                period_key=period["period_key"],
                defaults={
                    "target_object_type": "task",  # Default, can be customized
                    "status": "planned",
                    "period_starts_at": period["starts_at"],
                    "period_ends_at": period["ends_at"],
                    "period_label": period["label"],
                    "idempotency_key": self.generator.compute_idempotency_key(
                        recurrence_rule, period["period_key"]
                    ),
                    "backfilled": True,  # Mark as backfilled
                    "backfill_reason": reason,
                },
            )

            if created:
                periods_created += 1
                generation_ids.append(generation.id)
            else:
                periods_skipped += 1

        # Create audit event
        audit_event = audit.log_event(
            firm=recurrence_rule.firm,
            event_type="recurrence_backfill",
            severity="medium",
            actor=user,
            target_model="recurrence.RecurrenceRule",
            target_id=str(recurrence_rule.id),
            description=f"Backfilled {periods_created} periods for recurrence rule",
            metadata={
                "recurrence_rule_id": recurrence_rule.id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "periods_created": periods_created,
                "periods_skipped": periods_skipped,
                "reason": reason,
                "generation_ids": generation_ids,
            },
        )

        return BackfillResult(
            recurrence_rule_id=recurrence_rule.id,
            start_date=start_date,
            end_date=end_date,
            periods_created=periods_created,
            periods_skipped=periods_skipped,
            generation_ids=generation_ids,
            audit_event_id=audit_event.id if audit_event else None,
        )

    def validate_backfill_permission(self, user, recurrence_rule: RecurrenceRule) -> bool:
        """
        Validate that user has permission to backfill.

        DOC-10.2: Backfill MUST be permission-gated.

        Args:
            user: User requesting backfill
            recurrence_rule: RecurrenceRule to backfill

        Returns:
            True if user has permission, False otherwise
        """
        # Check if user has manage_recurrence permission
        from modules.crm.models import Permission

        return user.has_perm("recurrence.can_backfill_recurrence", recurrence_rule.firm)

    def get_missed_periods(
        self,
        recurrence_rule: RecurrenceRule,
        start_date: Optional[datetime] = None,
    ) -> List[dict]:
        """
        Get list of periods that were missed during pause.

        Useful for previewing what would be backfilled.

        Args:
            recurrence_rule: RecurrenceRule to analyze
            start_date: Start of analysis window (defaults to paused_at)

        Returns:
            List of period dicts with period_key, starts_at, ends_at, label, exists
        """
        if not recurrence_rule.paused_at and recurrence_rule.status == "paused":
            return []

        # Use paused_at as start if not provided
        if start_date is None:
            start_date = recurrence_rule.paused_at or timezone.now()

        end_date = timezone.now()

        # Compute periods
        candidate_periods = self.generator.compute_periods(
            recurrence_rule=recurrence_rule,
            as_of=end_date,
            start_boundary=start_date,
            end_boundary=end_date,
        )

        # Check which periods already exist
        result = []
        for period in candidate_periods:
            exists = RecurrenceGeneration.objects.filter(
                recurrence_rule=recurrence_rule,
                period_key=period["period_key"],
            ).exists()

            result.append(
                {
                    "period_key": period["period_key"],
                    "starts_at": period["starts_at"],
                    "ends_at": period["ends_at"],
                    "label": period["label"],
                    "exists": exists,
                    "would_create": not exists,
                }
            )

        return result


# Global service instance
backfill_service = BackfillService()
