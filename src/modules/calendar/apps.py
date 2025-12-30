"""App configuration for calendar module."""

from django.apps import AppConfig


class CalendarConfig(AppConfig):
    """Calendar app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.calendar"
    verbose_name = "Calendar & Scheduling"
