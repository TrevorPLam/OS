# AGENTS.md — Recurrence Module (Recurrence Engine)

Last Updated: 2026-01-06
Applies To: `src/modules/recurrence/`

## Purpose

Deterministic generation of recurring events/work items with DST-correct period boundaries.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | RecurrenceRule, RecurrenceGeneration, PeriodDefinition (~502 LOC) |
| `generator.py` | Period generation engine |
| `backfill.py` | Historical period backfill |

## Domain Model

```
RecurrenceRule (defines "what repeats")
    └── RecurrenceGeneration (dedupe ledger)

PeriodDefinition (computed period boundaries)
```

## Key Models

### RecurrenceRule

Defines what repeats and how:

```python
class RecurrenceRule(models.Model):
    firm: FK[Firm]
    
    # What this applies to
    scope: str                        # work_item_template_node, delivery_template, etc.
    
    # Polymorphic target
    target_delivery_template: FK[DeliveryTemplate]
    target_engagement: FK[ClientEngagement]
    target_engagement_line: FK[EngagementLine]
    
    # Frequency
    frequency: str                    # daily, weekly, monthly, quarterly, yearly
    interval: int                     # Every N periods (e.g., every 2 weeks)
    
    # Anchor
    anchor_type: str                  # calendar, fiscal, custom
    anchor_date: Date                 # Starting point
    
    # Bounds
    start_at: DateTime
    end_at: DateTime                  # Null = open-ended
    
    # Timezone (REQUIRED for DST correctness)
    timezone: str                     # e.g., "America/New_York"
    
    status: str                       # active, paused, canceled
```

### RecurrenceGeneration

Dedupe ledger to prevent duplicates:

```python
class RecurrenceGeneration(models.Model):
    rule: FK[RecurrenceRule]
    
    period_start: DateTime
    period_end: DateTime
    period_label: str                 # e.g., "2026-Q1", "2026-W03"
    
    # What was created
    generated_object_type: str        # work_item, invoice, etc.
    generated_object_id: int
    
    generated_at: DateTime
    
    class Meta:
        unique_together = ["rule", "period_start"]  # Prevents duplicates
```

## Generation Engine

```python
from modules.recurrence.generator import RecurrenceGenerator

generator = RecurrenceGenerator(rule)

# Get upcoming periods
periods = generator.get_periods(
    from_date=datetime.now(),
    count=10,
)

# Generate for a specific period
result = generator.generate_for_period(period)

# Idempotent - safe to call multiple times
# Uses RecurrenceGeneration to prevent duplicates
```

## Period Calculation

### Calendar-Based

```python
# Monthly on 15th
{
    "frequency": "monthly",
    "anchor_type": "calendar",
    "anchor_date": "2026-01-15"
}
# Generates: Jan 15, Feb 15, Mar 15, ...

# Weekly on Monday
{
    "frequency": "weekly",
    "anchor_type": "calendar",
    "anchor_date": "2026-01-06"  # A Monday
}
# Generates: Every Monday
```

### Fiscal-Based

```python
# Quarterly, fiscal year starts April
{
    "frequency": "quarterly",
    "anchor_type": "fiscal",
    "fiscal_year_start_month": 4
}
# Generates: Q1 (Apr-Jun), Q2 (Jul-Sep), Q3 (Oct-Dec), Q4 (Jan-Mar)
```

## DST Handling

**Critical**: All calculations use timezone-aware datetimes:

```python
# Rule specifies timezone
rule.timezone = "America/New_York"

# Generator handles DST transitions
# 2:00 AM on March 8, 2026 skips to 3:00 AM
# 2:00 AM on November 1, 2026 repeats

# Period boundaries always calculated in rule's timezone
# Then stored as UTC in database
```

## Deduplication

Every generation checks ledger:

```python
def generate_for_period(self, period):
    # Check if already generated
    existing = RecurrenceGeneration.objects.filter(
        rule=self.rule,
        period_start=period.start,
    ).exists()
    
    if existing:
        return None  # Already generated
    
    # Create work item / invoice / etc.
    obj = self._create_object(period)
    
    # Record in ledger
    RecurrenceGeneration.objects.create(
        rule=self.rule,
        period_start=period.start,
        period_end=period.end,
        generated_object_type=obj._meta.model_name,
        generated_object_id=obj.id,
    )
    
    return obj
```

## Backfill

For catching up on missed generations:

```python
from modules.recurrence.backfill import backfill_rule

# Generate all missing periods from rule start to now
created = backfill_rule(rule)
```

## Dependencies

- **Depends on**: `firm/`, `delivery/`, `clients/`
- **Used by**: WorkItem generation, invoice scheduling
- **Related**: `jobs/` (background generation job)

## Invariants

1. **Timezone Required**: Every RecurrenceRule MUST have a timezone
2. **Idempotent**: Same period never generates twice
3. **Deterministic**: Given same rule and date, produces same periods
4. **DST-Correct**: Handles daylight saving transitions
