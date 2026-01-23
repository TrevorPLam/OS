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
        import logging
        logger = logging.getLogger(__name__)
        
        # Import event handlers from other modules
        # This ensures handlers are registered at startup
        try:
            from modules.clients import event_handlers  # noqa: F401
            logger.info("Registered event handlers from modules.clients")
        except ImportError as e:
            # Only log if the module exists but has import errors
            # (ignore if event_handlers.py doesn't exist yet)
            if 'event_handlers' not in str(e):
                logger.warning(f"Failed to import clients.event_handlers: {e}")
        
        # TODO: Add imports for other modules' event handlers as they are created
        # Example:
        # try:
        #     from modules.projects import event_handlers  # noqa: F401
        # except ImportError as e:
        #     if 'event_handlers' not in str(e):
        #         logger.warning(f"Failed to import projects.event_handlers: {e}")
