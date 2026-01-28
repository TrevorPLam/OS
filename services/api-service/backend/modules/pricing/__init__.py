"""
Pricing Engine Module (DOC-09.1 per docs/03-reference/requirements/DOC-09.md PRICING_ENGINE_SPEC)

Provides versioned pricing rules evaluation with deterministic outputs and trace.

This module implements:
- RuleSet: Versioned collections of pricing rules
- PricingContext: Typed evaluation input
- Evaluator: Deterministic rule evaluation engine
- Trace: Complete evaluation audit trail
- QuoteVersion: Immutable pricing snapshots

Per docs/03-reference/requirements/DOC-09.md:
- Pricing MUST be reproducible and explainable
- Pricing MUST be auditable at the time of agreement
- Pricing rules MUST be versioned and snapshot-able
"""

default_app_config = "modules.pricing.apps.PricingConfig"
