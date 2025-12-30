"""
Recurrence Generator Engine (DOC-10.1 per docs/10 section 6).

Implements deterministic period generation with:
- Timezone-aware period calculations
- DST correctness
- Idempotency and uniqueness guarantees
- Concurrent-safe operations

DOC-10.1: Generator MUST be safe under retries and concurrency.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.firm.audit import AuditEvent
from modules.recurrence.models import RecurrenceGeneration, RecurrenceRule


class Period:
    """
    Period representation per docs/10 section 2.2.

    A computed interval representing a single recurrence instance.
    """

    def __init__(
        self,
        period_key: str,
        starts_at: datetime,
        ends_at: datetime,
        label: str = "",
    ):
        """
        Initialize a Period.

        Args:
            period_key: Stable string identifier (e.g., '2026-01')
            starts_at: Period start (UTC)
            ends_at: Period end (UTC)
            label: Human-friendly label
        """
        self.period_key = period_key
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.label = label or period_key

    def __repr__(self) -> str:
        return f"Period({self.period_key}, {self.starts_at} to {self.ends_at})"


class RecurrenceGenerator:
    """
    Recurrence generation engine per docs/10 section 6.

    Generates recurring instances deterministically without duplicates.
    """

    def __init__(self, firm, user=None):
        """
        Initialize generator.

        Args:
            firm: Firm context
            user: User context (for audit)
        """
        self.firm = firm
        self.user = user
        self.correlation_id = str(uuid.uuid4())

    def generate_for_window(
        self,
        as_of: datetime,
        lookahead_days: int = 90,
        lookback_days: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate recurrence instances for a time window per docs/10 section 6.2.

        Args:
            as_of: Deterministic clock time (timezone-aware)
            lookahead_days: Days to look ahead for generation
            lookback_days: Days to look back for recovery

        Returns:
            Dict with generation stats

        DOC-10.1: All recurrence calculations MUST be based on explicit as_of time.
        """
        stats = {
            "rules_processed": 0,
            "periods_planned": 0,
            "periods_already_exists": 0,
            "periods_failed": 0,
        }

        # Get active recurrence rules for this firm
        rules = RecurrenceRule.objects.filter(
            firm=self.firm,
            status="active",
        )

        window_start = as_of - timedelta(days=lookback_days)
        window_end = as_of + timedelta(days=lookahead_days)

        for rule in rules:
            try:
                rule_stats = self._generate_for_rule(
                    rule, as_of, window_start, window_end
                )
                stats["rules_processed"] += 1
                stats["periods_planned"] += rule_stats["planned"]
                stats["periods_already_exists"] += rule_stats["exists"]
            except Exception as e:
                stats["periods_failed"] += 1
                # Log error but continue processing other rules
                print(f"Error generating for rule {rule.id}: {e}")

        return stats

    def _generate_for_rule(
        self,
        rule: RecurrenceRule,
        as_of: datetime,
        window_start: datetime,
        window_end: datetime,
    ) -> Dict[str, int]:
        """
        Generate periods for a single rule per docs/10 section 6.2.

        Args:
            rule: RecurrenceRule to generate for
            as_of: Current time
            window_start: Start of generation window
            window_end: End of generation window

        Returns:
            Dict with stats (planned, exists)
        """
        stats = {"planned": 0, "exists": 0}

        # Compute candidate periods
        periods = self._compute_periods(rule, window_start, window_end)

        for period in periods:
            # Attempt to create RecurrenceGeneration record
            created = self._try_create_generation(rule, period, as_of)
            if created:
                stats["planned"] += 1
            else:
                stats["exists"] += 1

        return stats

    def _compute_periods(
        self,
        rule: RecurrenceRule,
        window_start: datetime,
        window_end: datetime,
    ) -> List[Period]:
        """
        Compute candidate periods for a rule per docs/10 section 4.

        DOC-10.1: Period boundary calculations MUST be timezone-aware.

        Args:
            rule: RecurrenceRule to compute periods for
            window_start: Start of generation window
            window_end: End of generation window

        Returns:
            List of Period objects
        """
        periods = []

        # Get rule timezone
        tz = ZoneInfo(rule.timezone)

        # Start from rule.start_at in rule's timezone
        current = rule.start_at.astimezone(tz)

        # If current is before window_start, advance it
        if current < window_start.astimezone(tz):
            current = window_start.astimezone(tz)

        # Generate periods until window_end or rule.end_at
        max_end = window_end
        if rule.end_at:
            max_end = min(max_end, rule.end_at)

        iteration_limit = 1000  # Safety limit
        iterations = 0

        while current < max_end.astimezone(tz) and iterations < iteration_limit:
            iterations += 1

            # Compute period boundaries based on frequency
            if rule.frequency == "monthly":
                period = self._compute_monthly_period(current, tz, rule.interval)
            elif rule.frequency == "quarterly":
                period = self._compute_quarterly_period(current, tz, rule.interval)
            elif rule.frequency == "weekly":
                period = self._compute_weekly_period(current, tz, rule.interval)
            elif rule.frequency == "daily":
                period = self._compute_daily_period(current, tz, rule.interval)
            elif rule.frequency == "yearly":
                period = self._compute_yearly_period(current, tz, rule.interval)
            else:
                raise ValueError(f"Unsupported frequency: {rule.frequency}")

            # Add period if it overlaps with window
            if period.ends_at > window_start and period.starts_at < window_end:
                periods.append(period)

            # Advance current to next period
            current = period.ends_at

        return periods

    def _compute_monthly_period(
        self, current: datetime, tz: ZoneInfo, interval: int
    ) -> Period:
        """
        Compute monthly period per docs/10 section 4.2.

        Period boundaries:
        - starts_at = first day of month at 00:00:00 local
        - ends_at = first day of next month at 00:00:00 local
        """
        # Start at first day of current month
        start_local = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate end date (first day of next month)
        month = start_local.month + interval
        year = start_local.year
        while month > 12:
            month -= 12
            year += 1

        end_local = start_local.replace(year=year, month=month)

        # Convert to UTC
        starts_at = start_local.astimezone(timezone.utc)
        ends_at = end_local.astimezone(timezone.utc)

        # Generate period key
        period_key = start_local.strftime("%Y-%m")
        label = start_local.strftime("%B %Y")

        return Period(period_key, starts_at, ends_at, label)

    def _compute_quarterly_period(
        self, current: datetime, tz: ZoneInfo, interval: int
    ) -> Period:
        """
        Compute quarterly period per docs/10 section 4.3.

        Quarter boundaries:
        - Q1 = Jan–Mar, Q2 = Apr–Jun, Q3 = Jul–Sep, Q4 = Oct–Dec
        """
        # Determine current quarter
        quarter = ((current.month - 1) // 3) + 1

        # Start at first day of quarter
        quarter_start_month = ((quarter - 1) * 3) + 1
        start_local = current.replace(
            month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Calculate end (first day of next quarter)
        next_quarter = quarter + interval
        year = start_local.year
        while next_quarter > 4:
            next_quarter -= 4
            year += 1

        end_month = ((next_quarter - 1) * 3) + 1
        end_local = start_local.replace(year=year, month=end_month)

        # Convert to UTC
        starts_at = start_local.astimezone(timezone.utc)
        ends_at = end_local.astimezone(timezone.utc)

        # Generate period key
        period_key = f"{start_local.year}-Q{quarter}"
        label = f"Q{quarter} {start_local.year}"

        return Period(period_key, starts_at, ends_at, label)

    def _compute_weekly_period(
        self, current: datetime, tz: ZoneInfo, interval: int
    ) -> Period:
        """
        Compute weekly period per docs/10 section 4.4.

        Using ISO week definition (Monday start).
        """
        # Find Monday of current week
        days_since_monday = current.weekday()
        start_local = (current - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # End is Monday of next week
        end_local = start_local + timedelta(weeks=interval)

        # Convert to UTC
        starts_at = start_local.astimezone(timezone.utc)
        ends_at = end_local.astimezone(timezone.utc)

        # Generate period key (ISO week)
        iso_year, iso_week, _ = start_local.isocalendar()
        period_key = f"{iso_year}-W{iso_week:02d}"
        label = f"Week {iso_week}, {iso_year}"

        return Period(period_key, starts_at, ends_at, label)

    def _compute_daily_period(
        self, current: datetime, tz: ZoneInfo, interval: int
    ) -> Period:
        """Compute daily period per docs/10 section 4.1."""
        # Start at beginning of day
        start_local = current.replace(hour=0, minute=0, second=0, microsecond=0)

        # End at beginning of next day
        end_local = start_local + timedelta(days=interval)

        # Convert to UTC
        starts_at = start_local.astimezone(timezone.utc)
        ends_at = end_local.astimezone(timezone.utc)

        # Generate period key
        period_key = start_local.strftime("%Y-%m-%d")
        label = start_local.strftime("%B %d, %Y")

        return Period(period_key, starts_at, ends_at, label)

    def _compute_yearly_period(
        self, current: datetime, tz: ZoneInfo, interval: int
    ) -> Period:
        """Compute yearly period."""
        # Start at beginning of year
        start_local = current.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # End at beginning of next year
        end_local = start_local.replace(year=start_local.year + interval)

        # Convert to UTC
        starts_at = start_local.astimezone(timezone.utc)
        ends_at = end_local.astimezone(timezone.utc)

        # Generate period key
        period_key = str(start_local.year)
        label = str(start_local.year)

        return Period(period_key, starts_at, ends_at, label)

    @transaction.atomic
    def _try_create_generation(
        self, rule: RecurrenceRule, period: Period, as_of: datetime
    ) -> bool:
        """
        Attempt to create RecurrenceGeneration record per docs/10 section 6.2.

        DOC-10.1: Uses unique constraint for dedupe.

        Args:
            rule: RecurrenceRule
            period: Period to generate for
            as_of: Current time

        Returns:
            True if created, False if already exists
        """
        try:
            RecurrenceGeneration.objects.create(
                firm=rule.firm,
                recurrence_rule=rule,
                period_key=period.period_key,
                period_starts_at=period.starts_at,
                period_ends_at=period.ends_at,
                period_label=period.label,
                target_object_type="task",  # Default; can be configured
                status="planned",
                correlation_id=self.correlation_id,
            )
            return True
        except IntegrityError:
            # Already exists (unique constraint violation)
            return False

    def backfill_periods(
        self,
        rule: RecurrenceRule,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, int]:
        """
        Backfill missed periods per docs/10 section 7.2.

        This operation:
        - Is permission-gated (caller must verify)
        - Is auditable
        - Is bounded by specified time range

        Args:
            rule: RecurrenceRule to backfill
            start_date: Start of backfill range
            end_date: End of backfill range

        Returns:
            Dict with backfill stats
        """
        stats = {"planned": 0, "exists": 0}

        # Compute periods in backfill range
        periods = self._compute_periods(rule, start_date, end_date)

        for period in periods:
            created = self._try_create_generation(rule, period, timezone.now())
            if created:
                stats["planned"] += 1
            else:
                stats["exists"] += 1

        # Audit the backfill
        AuditEvent.objects.create(
            firm=self.firm,
            category=AuditEvent.CATEGORY_DATA_ACCESS,
            action="recurrence_backfill",
            severity=AuditEvent.SEVERITY_INFO,
            actor_user=self.user,
            resource_type="RecurrenceRule",
            resource_id=str(rule.id),
            metadata={
                "rule_name": rule.name,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "periods_planned": stats["planned"],
                "periods_exists": stats["exists"],
            },
        )

        return stats
