"""Django app configuration for Accounting Integrations module."""

from django.apps import AppConfig


class AccountingIntegrationsConfig(AppConfig):
    """Configuration for Accounting Integrations app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.accounting_integrations'
    verbose_name = 'Accounting Integrations'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import modules.accounting_integrations.signals  # noqa: F401
        except ImportError:
            pass
