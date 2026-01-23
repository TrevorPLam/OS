"""
Recurrence Engine Module Configuration (DOC-10.1).
"""

from django.apps import AppConfig


class RecurrenceConfig(AppConfig):
    """App configuration for recurrence engine module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.recurrence"
    verbose_name = "Recurrence Engine"
