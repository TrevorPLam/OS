"""
Django AppConfig for events module.

Registers event handlers during application startup.
"""

from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.events'
    verbose_name = 'Domain Events'
    
    def ready(self):
        """
        Import event handlers to register them with the event bus.
        
        Handlers are registered via @subscribe_to decorator when modules are imported.
        """
        # Import event handlers from other modules
        # This ensures handlers are registered at startup
        try:
            from modules.clients import event_handlers  # noqa: F401
        except ImportError:
            pass  # Module may not have event handlers yet
