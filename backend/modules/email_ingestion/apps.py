"""App configuration for email ingestion module."""

from django.apps import AppConfig


class EmailIngestionConfig(AppConfig):
    """Email ingestion app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.email_ingestion"
    verbose_name = "Email Ingestion"
