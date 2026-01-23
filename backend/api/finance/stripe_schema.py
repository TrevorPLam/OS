"""
Stripe webhook schema validation helpers.

Provides deterministic payload validation for Stripe events before processing.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class StripeEventData(BaseModel):
    """Schema for the nested event data payload."""

    model_config = ConfigDict(extra="allow")
    object: Mapping[str, Any]


class StripeWebhookEventSchema(BaseModel):
    """Schema for Stripe webhook events (minimal required fields)."""

    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    data: StripeEventData


def normalize_stripe_event_payload(event: object) -> Mapping[str, Any]:
    """
    Normalize Stripe event objects to plain mappings for validation.

    Meta-commentary:
    - Reasoning: Stripe SDK returns StripeObject; Pydantic expects a mapping.
    - Constraint: Reject non-mapping inputs early to avoid ambiguous errors.
    """
    if hasattr(event, "to_dict"):
        return event.to_dict()
    if isinstance(event, Mapping):
        return event
    raise ValueError("Stripe event payload must be a mapping")


def validate_stripe_event_payload(event: object) -> StripeWebhookEventSchema:
    """
    Validate a Stripe webhook payload and return the typed schema.

    Raises:
        ValueError: If payload is not a mapping.
        ValidationError: If required fields are missing or invalid.
    """
    normalized = normalize_stripe_event_payload(event)
    return StripeWebhookEventSchema.model_validate(normalized)


__all__ = [
    "StripeWebhookEventSchema",
    "StripeEventData",
    "ValidationError",
    "normalize_stripe_event_payload",
    "validate_stripe_event_payload",
]
