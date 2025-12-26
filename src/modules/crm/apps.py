from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.crm"
    verbose_name = "CRM (Customer Relationship Management)"

    def ready(self):
        """Import signals when app is ready."""
        import modules.crm.signals  # noqa
