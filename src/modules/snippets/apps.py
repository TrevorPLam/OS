"""App configuration for snippets module."""

from django.apps import AppConfig


class SnippetsConfig(AppConfig):
    """Configuration for snippets module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.snippets"
    verbose_name = "Snippets"
