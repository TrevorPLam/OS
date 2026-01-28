"""
Active Directory Synchronization App Configuration
"""

from django.apps import AppConfig


class ADSyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.ad_sync'
    verbose_name = 'Active Directory Synchronization'
