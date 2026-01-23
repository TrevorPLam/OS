"""
Django app configuration for webhooks module.
"""

from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.webhooks'
    verbose_name = 'Webhooks'
    
    def ready(self):
        """Import signals when app is ready."""
        # Import signals here when needed
        pass
