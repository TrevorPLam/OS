"""App configuration for calendar module."""

from django.apps import AppConfig
from django.conf import settings


class CalendarConfig(AppConfig):
    """Calendar app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.calendar"
    verbose_name = "Calendar & Scheduling"
    
    def ready(self):
        """Import signals when app is ready."""
        if getattr(settings, "CALENDAR_ENABLE_SIGNALS", True):
            import modules.calendar.signals  # noqa: F401
