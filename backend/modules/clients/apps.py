from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.clients"
    verbose_name = "Clients (Post-Sale)"

    def ready(self):
        """Import signals when app is ready."""
        import modules.clients.signals  # noqa
