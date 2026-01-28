"""
Communications App Configuration.
"""

from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    """Configuration for the Communications module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.communications"
    verbose_name = "Communications"
