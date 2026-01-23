"""Pricing module app configuration."""

from django.apps import AppConfig


class PricingConfig(AppConfig):
    """Configuration for the pricing module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.pricing"
    verbose_name = "Pricing Engine"

    def ready(self) -> None:
        """Initialize pricing module."""
        pass
