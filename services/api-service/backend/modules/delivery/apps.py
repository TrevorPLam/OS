"""
Delivery Templates Module Configuration (DOC-12.1).
"""

from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    """App configuration for delivery templates module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.delivery"
    verbose_name = "Delivery Templates"
