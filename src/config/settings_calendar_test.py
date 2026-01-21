import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("USE_SQLITE_FOR_TESTS", "True")
os.environ.setdefault("DJANGO_DEBUG", "False")

from config.settings import *  # noqa: F401, F403

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "modules.core",
    "modules.firm",
    "modules.auth",
    "tests.stubs.clients.apps.StubClientsConfig",
    "modules.calendar",
]

ROOT_URLCONF = "config.urls_auth_test"

MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if "modules.clients.middleware.PortalContainmentMiddleware" not in middleware
    and "modules.firm.middleware.FirmContextMiddleware" not in middleware
    and "debug_toolbar.middleware.DebugToolbarMiddleware" not in middleware
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CALENDAR_ENABLE_SIGNALS = False
