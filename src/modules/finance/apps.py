from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.finance'
    verbose_name = 'Finance (AR/AP & P&L)'
