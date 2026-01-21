# AGENTS.md — Pricing Module (Pricing Engine)

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/pricing/`

## Purpose

Versioned pricing rulesets for quote generation with immutability guarantees and audit trails.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | RuleSet, Quote, QuoteVersion, QuoteLineItem, EvaluationTrace (~620 LOC) |
| `evaluator.py` | Rule evaluation engine |
| `schema_compatibility.py` | Schema version migration |
| `views.py` | Pricing API |
| `serializers.py` | Pricing serializers |

## Domain Model

```
RuleSet (pricing rules template)
    └── Version history (immutable)

Quote (mutable working draft)
    └── QuoteVersion (immutable snapshot)
            └── QuoteLineItem (individual items)
            └── EvaluationTrace (audit trail)
```

## Key Models

### RuleSet

Versioned pricing rules:

```python
class RuleSet(models.Model):
    firm: FK[Firm]
    
    name: str
    code: str                         # Stable identifier
    version: int                      # Increments on publish
    schema_version: str               # e.g., "1.0.0"
    
    status: str                       # draft, published, deprecated
    
    # Rules
    rules_json: JSONField             # Pricing rules
    checksum: str                     # SHA-256 for integrity
    
    # IMMUTABILITY: Published RuleSets cannot be modified
```

### Quote

Mutable working document:

```python
class Quote(models.Model):
    firm: FK[Firm]
    prospect: FK[Prospect]            # CRM link
    
    name: str
    status: str                       # draft, sent, accepted, rejected
    
    # Current version reference
    current_version: FK[QuoteVersion]
    
    valid_until: Date
```

### QuoteVersion

Immutable pricing snapshot:

```python
class QuoteVersion(models.Model):
    quote: FK[Quote]
    version_number: int
    
    # RuleSet reference (exact version)
    ruleset: FK[RuleSet]
    ruleset_version: int
    ruleset_checksum: str             # Must match at evaluation time
    
    # Pricing
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    
    # Snapshot
    pricing_snapshot: JSONField       # Full pricing state at creation
    
    created_at: DateTime
    created_by: FK[User]
    
    # IMMUTABLE after creation
```

### EvaluationTrace

Audit trail for pricing decisions:

```python
class EvaluationTrace(models.Model):
    quote_version: FK[QuoteVersion]
    
    step_number: int
    rule_id: str
    rule_name: str
    
    input_values: JSONField
    output_value: JSONField
    
    # Explains why this price was calculated
    explanation: str
```

## RuleSet Schema

```json
{
  "schema_version": "1.0.0",
  "rules": [
    {
      "id": "base_hourly",
      "name": "Base Hourly Rate",
      "type": "lookup",
      "table": {
        "junior": 150,
        "senior": 250,
        "principal": 400
      },
      "input": "staff_level"
    },
    {
      "id": "volume_discount",
      "name": "Volume Discount",
      "type": "tiered",
      "tiers": [
        { "min": 0, "max": 100, "value": 0 },
        { "min": 100, "max": 500, "value": 0.05 },
        { "min": 500, "max": null, "value": 0.10 }
      ],
      "input": "total_hours"
    }
  ]
}
```

## Evaluation Engine

```python
from modules.pricing.evaluator import PricingEvaluator

evaluator = PricingEvaluator(ruleset)

result = evaluator.evaluate(
    line_items=[
        {"service": "consulting", "staff_level": "senior", "hours": 40},
        {"service": "consulting", "staff_level": "junior", "hours": 80},
    ],
    context={"client_tier": "premium"}
)

# result includes:
# - line_item_totals
# - subtotal
# - discounts applied
# - evaluation_trace (for audit)
```

## Immutability Rules

1. **Published RuleSets**: Cannot modify rules_json after publish
2. **QuoteVersions**: Cannot modify after creation
3. **Checksum Validation**: QuoteVersion must validate ruleset checksum at evaluation

```python
# Creating new version (bumps version number)
new_ruleset = ruleset.publish_new_version(new_rules_json)

# Deprecating old version
old_ruleset.deprecate()
```

## Dependencies

- **Depends on**: `firm/`, `crm/`
- **Used by**: Proposals, Invoicing
- **Related**: CRM Proposal generation

## URLs

All routes under `/api/v1/pricing/`:

```
# RuleSets
GET/POST   /rulesets/
GET        /rulesets/{id}/
POST       /rulesets/{id}/publish/
POST       /rulesets/{id}/deprecate/
GET        /rulesets/{id}/versions/

# Quotes
GET/POST   /quotes/
GET/PUT    /quotes/{id}/
POST       /quotes/{id}/create-version/
GET        /quotes/{id}/versions/
GET        /quotes/{id}/versions/{version}/

# Evaluation
POST       /evaluate/                      # Evaluate pricing without saving
GET        /quotes/{id}/evaluation-trace/  # Get audit trail
```
