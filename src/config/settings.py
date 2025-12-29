"""
Django settings for ConsultantPro (USP Phase 1).

This is the Core Skeleton targeting the management consulting vertical.
Built as a Modular Monolith following the "Fork-and-Ship" strategy.
"""

import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: Secret key MUST be set via environment variable - no fallback
# Application will fail to start if DJANGO_SECRET_KEY is not configured
_secret_key = os.environ.get("DJANGO_SECRET_KEY")
if not _secret_key:
    raise ValueError(
        "DJANGO_SECRET_KEY environment variable is required. "
        "Generate one with: python -c "
        "'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    )
SECRET_KEY = _secret_key

# SECURITY: DEBUG defaults to False for production safety
# Explicitly set DJANGO_DEBUG=True for development
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    # Django Core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # USP Business Modules (Organized by Domain)
    "modules.core",  # TIER 3: Shared infrastructure (purge, audit utilities)
    "modules.firm",  # TIER 0: Multi-tenant foundation (Workspace/Firm)
    "modules.auth",
    "modules.crm",  # Pre-sale: Leads, Prospects, Proposals
    "modules.clients",  # Post-sale: Client management and portal
    "modules.projects",
    "modules.finance",
    "modules.documents",
    "modules.assets",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # TIER 5.5: Operational observability (non-content telemetry)
    "modules.core.middleware.TelemetryRequestMiddleware",
    # TIER 0: Firm context resolution (must come after AuthenticationMiddleware)
    "modules.firm.middleware.FirmContextMiddleware",
    # Sentry context middleware (must come after FirmContextMiddleware to capture firm context)
    "config.sentry_middleware.SentryContextMiddleware",
    # TIER 0: Portal containment (must come after FirmContextMiddleware)
    "modules.clients.middleware.PortalContainmentMiddleware",
    # TIER 0.6: Break-glass awareness for impersonation banners + auditing
    "modules.firm.middleware.BreakGlassImpersonationMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# PostgreSQL 15+ (Strict ACID compliance required)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "consultantpro"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "ATOMIC_REQUESTS": True,  # Enforce transaction safety
        "CONN_MAX_AGE": 600,  # Connection pooling
    }
}

if os.environ.get("USE_SQLITE_FOR_TESTS") == "True":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

# Password validation
# SECURITY: Minimum 12 characters recommended for stronger security
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "frontend" / "build" / "static"]

# Media files (User uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.BoundedPageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "config.throttling.BurstRateThrottle",
        "config.throttling.SustainedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "burst": "100/minute",
        "sustained": "1000/hour",
        "anon": "20/hour",
        "payment": "10/minute",
        "upload": "30/hour",
    },
    "EXCEPTION_HANDLER": "config.error_handlers.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# API guardrails
API_PAGINATION_MAX_PAGE_SIZE = 200
API_SEARCH_MAX_LENGTH = 100
API_QUERY_TIMEOUT_MS = 3000

# Simple JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

# CORS Settings (for React frontend)
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

CORS_ALLOW_CREDENTIALS = True

# S3 Configuration (for Documents module)
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")

# E2EE / KMS Configuration
DEFAULT_FIRM_KMS_KEY_ID = os.environ.get("DEFAULT_FIRM_KMS_KEY_ID", "local-default-key")
KMS_BACKEND = os.environ.get("KMS_BACKEND", "local")

# Stripe Configuration (for Finance module)
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# API Documentation with drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "ConsultantPro API",
    "DESCRIPTION": "Quote-to-Cash Management Platform for Management Consulting Firms",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api",
    "ENUM_NAME_OVERRIDES": {
        "StatusEnum": "modules.crm.models.Client.STATUS_CHOICES",
    },
}

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "errors.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "security.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "security_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "config.exceptions": {
            "handlers": ["console", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "modules": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Security Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# =============================================================================
# Error Tracking & Monitoring (Sentry)
# =============================================================================
# Initialize Sentry for error tracking and performance monitoring
# Only active if SENTRY_DSN environment variable is set
from config.sentry import init_sentry  # noqa

init_sentry()

# =============================================================================
# Environment Validation (runs on startup)
# =============================================================================
# Import at end to validate after all settings are loaded
from config.env_validator import validate_environment  # noqa
