"""
Pricing Engine Evaluator (DOC-09.1 per docs/9 PRICING_ENGINE_SPEC)

Implements deterministic pricing evaluation with:
- Context binding
- Rule evaluation
- Trace generation
- Output computation

CRITICAL: Evaluation MUST be deterministic.
Given the same (ruleset_version, context), outputs MUST be identical.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional

from django.utils import timezone


@dataclass
class EvaluationContext:
    """
    Evaluation context per docs/9 section 3.

    Bounded context for pricing evaluation.
    MUST NOT include HR-classified data.
    """

    # Client information
    client_id: int
    client_type: str = "standard"

    # Project scope
    project_type: Optional[str] = None
    engagement_type: Optional[str] = None

    # Pricing inputs
    products: list = field(default_factory=list)
    quantity_overrides: dict = field(default_factory=dict)
    discount_codes: list = field(default_factory=list)

    # Date context
    effective_date: Optional[date] = None
    currency: str = "USD"

    # Custom attributes
    custom_attributes: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "client_id": self.client_id,
            "client_type": self.client_type,
            "project_type": self.project_type,
            "engagement_type": self.engagement_type,
            "products": self.products,
            "quantity_overrides": self.quantity_overrides,
            "discount_codes": self.discount_codes,
            "effective_date": (
                self.effective_date.isoformat() if self.effective_date else None
            ),
            "currency": self.currency,
            "custom_attributes": self.custom_attributes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationContext":
        """Create from dictionary."""
        effective_date = data.get("effective_date")
        if effective_date and isinstance(effective_date, str):
            effective_date = date.fromisoformat(effective_date)

        return cls(
            client_id=data["client_id"],
            client_type=data.get("client_type", "standard"),
            project_type=data.get("project_type"),
            engagement_type=data.get("engagement_type"),
            products=data.get("products", []),
            quantity_overrides=data.get("quantity_overrides", {}),
            discount_codes=data.get("discount_codes", []),
            effective_date=effective_date,
            currency=data.get("currency", "USD"),
            custom_attributes=data.get("custom_attributes", {}),
        )


@dataclass
class TraceStep:
    """Single step in the evaluation trace per docs/9 section 6.3."""

    step_number: int
    rule_id: str
    rule_type: str
    inputs: dict
    outputs: dict
    outcome: str  # "applied", "skipped", "error"
    reason: Optional[str] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "step_number": self.step_number,
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "outcome": self.outcome,
            "reason": self.reason,
            "duration_ms": self.duration_ms,
        }


@dataclass
class EvaluationResult:
    """
    Evaluation result per docs/9 section 6.

    Contains all outputs required for QuoteVersion persistence.
    """

    # Outputs
    line_items: list = field(default_factory=list)
    totals: dict = field(default_factory=dict)
    assumptions: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    # Trace
    trace_steps: list = field(default_factory=list)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Metadata
    evaluated_at: datetime = field(default_factory=timezone.now)
    ruleset_checksum: str = ""
    context_checksum: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "line_items": self.line_items,
            "totals": self.totals,
            "assumptions": self.assumptions,
            "warnings": self.warnings,
            "trace": {
                "correlation_id": self.correlation_id,
                "evaluated_at": self.evaluated_at.isoformat(),
                "ruleset_checksum": self.ruleset_checksum,
                "context_checksum": self.context_checksum,
                "steps": [step.to_dict() for step in self.trace_steps],
            },
        }


class PricingEvaluator:
    """
    Deterministic pricing evaluator per docs/9 sections 4-6.

    Evaluates a ruleset against a context to produce outputs and trace.

    Usage:
        evaluator = PricingEvaluator(ruleset)
        result = evaluator.evaluate(context)
    """

    def __init__(self, ruleset: "RuleSet"):
        """
        Initialize evaluator with a ruleset.

        Args:
            ruleset: The RuleSet model instance to evaluate
        """
        self.ruleset = ruleset
        self.rules = ruleset.rules_json
        self._step_counter = 0

    def evaluate(
        self,
        context: EvaluationContext,
        correlation_id: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Evaluate the ruleset against the context.

        Per docs/9 section 4: Evaluation MUST be deterministic.

        Args:
            context: The evaluation context
            correlation_id: Optional correlation ID for tracing

        Returns:
            EvaluationResult with outputs and trace
        """
        result = EvaluationResult(
            correlation_id=correlation_id or str(uuid.uuid4()),
            ruleset_checksum=self.ruleset.checksum,
            context_checksum=self._compute_context_checksum(context),
        )

        self._step_counter = 0

        # Step 1: Resolve products
        line_items = self._evaluate_products(context, result)

        # Step 2: Apply discounts
        line_items = self._apply_discounts(line_items, context, result)

        # Step 3: Compute totals
        totals = self._compute_totals(line_items, context, result)

        # Step 4: Generate assumptions
        assumptions = self._generate_assumptions(context, result)

        # Populate result
        result.line_items = line_items
        result.totals = totals
        result.assumptions = assumptions

        return result

    def _compute_context_checksum(self, context: EvaluationContext) -> str:
        """Compute checksum of evaluation context."""
        normalized = json.dumps(context.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _add_trace_step(
        self,
        result: EvaluationResult,
        rule_id: str,
        rule_type: str,
        inputs: dict,
        outputs: dict,
        outcome: str,
        reason: Optional[str] = None,
    ) -> None:
        """Add a step to the evaluation trace."""
        self._step_counter += 1
        result.trace_steps.append(
            TraceStep(
                step_number=self._step_counter,
                rule_id=rule_id,
                rule_type=rule_type,
                inputs=inputs,
                outputs=outputs,
                outcome=outcome,
                reason=reason,
            )
        )

    def _evaluate_products(
        self,
        context: EvaluationContext,
        result: EvaluationResult,
    ) -> list:
        """Evaluate product rules to generate line items."""
        line_items = []
        products_config = self.rules.get("products", {})

        for i, product_request in enumerate(context.products):
            product_code = product_request.get("code")
            quantity = product_request.get("quantity", 1)

            # Apply quantity override if present
            if product_code in context.quantity_overrides:
                quantity = context.quantity_overrides[product_code]

            product_def = products_config.get(product_code)

            if not product_def:
                self._add_trace_step(
                    result,
                    rule_id=f"product_lookup_{product_code}",
                    rule_type="product_lookup",
                    inputs={"product_code": product_code},
                    outputs={},
                    outcome="skipped",
                    reason=f"Product {product_code} not found in ruleset",
                )
                result.warnings.append(f"Product '{product_code}' not found in ruleset")
                continue

            # Get price based on client type or default
            price_tiers = product_def.get("prices", {})
            unit_price = price_tiers.get(
                context.client_type,
                price_tiers.get("default", 0),
            )

            # Convert to Decimal for precision
            unit_price = Decimal(str(unit_price))
            quantity = Decimal(str(quantity))
            amount = unit_price * quantity

            line_item = {
                "line_number": len(line_items) + 1,
                "product_code": product_code,
                "name": product_def.get("name", product_code),
                "description": product_def.get("description", ""),
                "quantity": float(quantity),
                "unit_price": float(unit_price),
                "amount": float(amount),
                "billing_model": product_def.get("billing_model", "fixed"),
                "billing_unit": product_def.get("billing_unit", ""),
                "tax_category": product_def.get("tax_category", ""),
            }

            line_items.append(line_item)

            self._add_trace_step(
                result,
                rule_id=f"product_{product_code}",
                rule_type="product_pricing",
                inputs={
                    "product_code": product_code,
                    "client_type": context.client_type,
                    "quantity": float(quantity),
                },
                outputs={
                    "unit_price": float(unit_price),
                    "amount": float(amount),
                },
                outcome="applied",
            )

        return line_items

    def _apply_discounts(
        self,
        line_items: list,
        context: EvaluationContext,
        result: EvaluationResult,
    ) -> list:
        """Apply discount rules to line items."""
        discounts_config = self.rules.get("discounts", {})

        for discount_code in context.discount_codes:
            discount_def = discounts_config.get(discount_code)

            if not discount_def:
                self._add_trace_step(
                    result,
                    rule_id=f"discount_lookup_{discount_code}",
                    rule_type="discount_lookup",
                    inputs={"discount_code": discount_code},
                    outputs={},
                    outcome="skipped",
                    reason=f"Discount {discount_code} not found in ruleset",
                )
                result.warnings.append(
                    f"Discount code '{discount_code}' not found in ruleset"
                )
                continue

            discount_type = discount_def.get("type", "percentage")
            discount_value = Decimal(str(discount_def.get("value", 0)))
            applies_to = discount_def.get("applies_to", "all")

            total_discount = Decimal("0")

            for line_item in line_items:
                # Check if discount applies to this product
                if applies_to != "all" and line_item["product_code"] not in applies_to:
                    continue

                original_amount = Decimal(str(line_item["amount"]))

                if discount_type == "percentage":
                    item_discount = original_amount * (discount_value / 100)
                elif discount_type == "fixed":
                    item_discount = min(discount_value, original_amount)
                else:
                    item_discount = Decimal("0")

                line_item["amount"] = float(original_amount - item_discount)
                line_item["discount_applied"] = float(item_discount)
                total_discount += item_discount

            self._add_trace_step(
                result,
                rule_id=f"discount_{discount_code}",
                rule_type="discount",
                inputs={
                    "discount_code": discount_code,
                    "discount_type": discount_type,
                    "discount_value": float(discount_value),
                },
                outputs={"total_discount": float(total_discount)},
                outcome="applied",
            )

        return line_items

    def _compute_totals(
        self,
        line_items: list,
        context: EvaluationContext,
        result: EvaluationResult,
    ) -> dict:
        """Compute quote totals from line items."""
        subtotal = sum(Decimal(str(item["amount"])) for item in line_items)
        total_discounts = sum(
            Decimal(str(item.get("discount_applied", 0))) for item in line_items
        )

        # Get tax configuration
        tax_config = self.rules.get("tax", {})
        tax_rate = Decimal(str(tax_config.get("default_rate", 0)))

        tax_amount = subtotal * (tax_rate / 100)
        total = subtotal + tax_amount

        totals = {
            "subtotal": float(subtotal + total_discounts),  # Before discounts
            "discounts": float(total_discounts),
            "subtotal_after_discounts": float(subtotal),
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amount),
            "total": float(total),
            "currency": context.currency,
        }

        self._add_trace_step(
            result,
            rule_id="compute_totals",
            rule_type="totals",
            inputs={"line_item_count": len(line_items)},
            outputs=totals,
            outcome="applied",
        )

        return totals

    def _generate_assumptions(
        self,
        context: EvaluationContext,
        result: EvaluationResult,
    ) -> list:
        """Generate assumption statements per docs/9 section 6.2."""
        assumptions = []

        # Standard assumptions
        assumptions.append(f"Prices quoted in {context.currency}")

        if context.effective_date:
            assumptions.append(
                f"Prices effective as of {context.effective_date.isoformat()}"
            )

        # Ruleset-specific assumptions
        ruleset_assumptions = self.rules.get("assumptions", [])
        assumptions.extend(ruleset_assumptions)

        self._add_trace_step(
            result,
            rule_id="generate_assumptions",
            rule_type="assumptions",
            inputs={},
            outputs={"assumption_count": len(assumptions)},
            outcome="applied",
        )

        return assumptions


def evaluate_quote(
    ruleset: "RuleSet",
    context: EvaluationContext,
    correlation_id: Optional[str] = None,
) -> EvaluationResult:
    """
    Convenience function to evaluate a quote.

    Args:
        ruleset: The RuleSet to evaluate
        context: The evaluation context
        correlation_id: Optional correlation ID

    Returns:
        EvaluationResult with outputs and trace
    """
    evaluator = PricingEvaluator(ruleset)
    return evaluator.evaluate(context, correlation_id)
