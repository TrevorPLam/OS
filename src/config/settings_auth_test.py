import os

# Provide defaults so auth tests can run without external configuration
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("USE_SQLITE_FOR_TESTS", "True")
os.environ.setdefault("DJANGO_DEBUG", "True")

from config.settings import *  # noqa: F401, F403

# Narrow the installed apps to the minimum required for auth flows
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.microsoft",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "modules.core",
    "modules.firm",
    "modules.auth",
]

ROOT_URLCONF = "config.urls_auth_test"

# Remove middleware that depends on modules not loaded for focused auth tests
MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if "modules.clients.middleware.PortalContainmentMiddleware" not in middleware
    and "modules.firm.middleware.FirmContextMiddleware" not in middleware
]

# Force SQLite for isolated, fast auth tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
