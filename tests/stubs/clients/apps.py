"""App config for stub clients app used in calendar tests."""

from django.apps import AppConfig


class StubClientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.stubs.clients"
    label = "clients"
