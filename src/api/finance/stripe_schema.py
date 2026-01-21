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
    Convert a Stripe event object into a plain mapping suitable for schema validation.
    
    If the input provides a `to_dict()` method, its result is returned. If the input is already a `Mapping`, it is returned unchanged.
    
    Parameters:
        event (object): A Stripe event object or a mapping. Accepted inputs are objects with a `to_dict()` method or instances of `collections.abc.Mapping`.
    
    Returns:
        Mapping[str, Any]: A plain mapping representation of the event.
    
    Raises:
        ValueError: If `event` is neither a mapping nor provides `to_dict()`.
    """
    if hasattr(event, "to_dict"):
        return event.to_dict()
    if isinstance(event, Mapping):
        return event
    raise ValueError("Stripe event payload must be a mapping")


def validate_stripe_event_payload(event: object) -> StripeWebhookEventSchema:
    """
    Validate and parse a Stripe webhook payload into a StripeWebhookEventSchema.
    
    Parameters:
        event (object): A Stripe event mapping or an object with a `to_dict()` method representing the webhook payload.
    
    Returns:
        stripe_event (StripeWebhookEventSchema): Validated and parsed webhook event.
    
    Raises:
        ValueError: If the payload is not a mapping.
        ValidationError: If required fields are missing or invalid during schema validation.
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