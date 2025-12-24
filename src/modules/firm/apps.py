from django.apps import AppConfig


class FirmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.firm'
    label = 'firm'
    verbose_name = 'Firm (Workspace) Management'
    
    def ready(self):
        """Import signals when app is ready."""
        import modules.firm.signals  # noqa: F401

