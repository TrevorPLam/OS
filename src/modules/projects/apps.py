from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.projects'
    verbose_name = 'Projects & Time Tracking'

    def ready(self):
        """Import signals when app is ready."""
        import modules.projects.signals  # noqa
