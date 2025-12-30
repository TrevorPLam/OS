"""App configuration for SMS module."""

from django.apps import AppConfig


class SMSConfig(AppConfig):
    """Configuration for SMS module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.sms"
    verbose_name = "SMS"
