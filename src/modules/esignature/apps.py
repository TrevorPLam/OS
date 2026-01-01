"""Django app configuration for e-signature integrations."""

from django.apps import AppConfig


class EsignatureConfig(AppConfig):
    """Configuration for the esignature app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.esignature"
    verbose_name = "E-Signature Integrations"

    def ready(self):
        """Import signals when app is ready."""
        import modules.esignature.signals  # noqa: F401
