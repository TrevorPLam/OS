"""
Orchestration Engine Module Configuration (DOC-11.1).
"""

from django.apps import AppConfig


class OrchestrationConfig(AppConfig):
    """App configuration for orchestration engine module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.orchestration"
    verbose_name = "Orchestration Engine"
