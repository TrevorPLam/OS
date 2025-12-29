"""
Sentry Error Tracking Configuration.

Provides centralized error tracking and performance monitoring for production.
Sentry captures exceptions, performance data, and provides alerting.
"""

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry error tracking.

    Configuration via environment variables:
    - SENTRY_DSN: Sentry Data Source Name (required for Sentry to work)
    - SENTRY_ENVIRONMENT: Environment name (production, staging, development)
    - SENTRY_TRACES_SAMPLE_RATE: Performance monitoring sample rate (0.0-1.0)
    - SENTRY_PROFILES_SAMPLE_RATE: Profiling sample rate (0.0-1.0)

    This should be called early in Django startup (settings.py).
    """
    sentry_dsn = os.environ.get("SENTRY_DSN")
    sentry_environment = os.environ.get("SENTRY_ENVIRONMENT", "production")
    traces_sample_rate = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    profiles_sample_rate = float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))

    if not sentry_dsn:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return

    # Configure Sentry logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors and above as events
    )

    # Initialize Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=sentry_environment,
        integrations=[
            DjangoIntegration(
                transaction_style="url",  # Use URL pattern for transaction names
                middleware_spans=True,  # Track middleware performance
                signals_spans=True,  # Track Django signals
                cache_spans=True,  # Track cache operations
            ),
            sentry_logging,
        ],
        # Performance Monitoring
        traces_sample_rate=traces_sample_rate,  # Sample 10% of transactions
        profiles_sample_rate=profiles_sample_rate,  # Profile 10% of sampled transactions
        # Error Tracking
        send_default_pii=False,  # Don't send personally identifiable information
        attach_stacktrace=True,  # Attach stack traces to messages
        # Release Tracking
        release=os.environ.get("GIT_COMMIT_SHA"),  # Track releases by git commit
        # Advanced Options
        max_breadcrumbs=50,  # Keep last 50 breadcrumbs
        debug=os.environ.get("SENTRY_DEBUG", "False").lower() == "true",
        # Filtering
        before_send=before_send_filter,
        before_send_transaction=before_send_transaction_filter,
    )

    logger.info(
        f"Sentry initialized: environment={sentry_environment}, "
        f"traces_sample_rate={traces_sample_rate}, "
        f"profiles_sample_rate={profiles_sample_rate}"
    )


def before_send_filter(event: dict, hint: dict) -> dict | None:
    """
    Filter events before sending to Sentry.

    Can be used to:
    - Remove sensitive data
    - Filter out specific errors
    - Add custom context

    Args:
        event: Sentry event dictionary
        hint: Additional context about the event

    Returns:
        Modified event dictionary, or None to drop the event
    """
    # Example: Filter out specific errors
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        # Don't send common HTTP errors that are expected
        if isinstance(exc_value, PermissionError):
            # These are expected in normal operation (portal users trying to access admin endpoints)
            return None

    # Example: Remove sensitive data from request
    if "request" in event:
        # Remove authorization headers
        if "headers" in event["request"]:
            headers = event["request"]["headers"]
            if "Authorization" in headers:
                headers["Authorization"] = "[Filtered]"
            if "Cookie" in headers:
                headers["Cookie"] = "[Filtered]"

        # Remove sensitive query parameters
        if "query_string" in event["request"]:
            # Filter out tokens, passwords, etc.
            # event["request"]["query_string"] = filter_sensitive_params(event["request"]["query_string"])
            pass

    # Add custom tags
    if "tags" not in event:
        event["tags"] = {}

    # Add firm context if available (multi-tenant context)
    if "user" in event and event["user"]:
        # This would be populated by Django integration
        pass

    return event


def before_send_transaction_filter(event: dict, hint: dict) -> dict | None:
    """
    Filter performance transactions before sending to Sentry.

    Can be used to:
    - Sample specific endpoints differently
    - Filter out health check endpoints
    - Add custom tags

    Args:
        event: Sentry transaction event
        hint: Additional context

    Returns:
        Modified event, or None to drop the transaction
    """
    # Filter out health check and monitoring endpoints
    if "transaction" in event:
        transaction_name = event["transaction"]
        if transaction_name in ["/health/", "/api/health/", "/metrics/"]:
            return None  # Don't track health checks

    return event


def capture_exception_with_context(
    exception: Exception, context: dict | None = None, level: str = "error", **extra_tags
) -> str | None:
    """
    Capture an exception with additional context.

    Usage:
        try:
            risky_operation()
        except Exception as e:
            capture_exception_with_context(
                e,
                context={"operation": "risky_operation", "params": {...}},
                level="error",
                module="finance",
                action="invoice_creation"
            )

    Args:
        exception: The exception to capture
        context: Additional context dictionary
        level: Severity level (error, warning, info)
        **extra_tags: Additional tags for filtering in Sentry

    Returns:
        Event ID if sent, None otherwise
    """
    with sentry_sdk.push_scope() as scope:
        # Set level
        scope.level = level

        # Add context
        if context:
            scope.set_context("custom_context", context)

        # Add extra tags
        for key, value in extra_tags.items():
            scope.set_tag(key, value)

        # Capture exception
        return sentry_sdk.capture_exception(exception)


def capture_message_with_context(
    message: str, level: str = "info", context: dict | None = None, **extra_tags
) -> str | None:
    """
    Capture a message with additional context.

    Useful for capturing non-exception events that should be monitored.

    Args:
        message: The message to capture
        level: Severity level (error, warning, info)
        context: Additional context dictionary
        **extra_tags: Additional tags

    Returns:
        Event ID if sent, None otherwise
    """
    with sentry_sdk.push_scope() as scope:
        scope.level = level

        if context:
            scope.set_context("custom_context", context)

        for key, value in extra_tags.items():
            scope.set_tag(key, value)

        return sentry_sdk.capture_message(message)


def set_user_context(user_id: int | str, email: str | None = None, **extra_data) -> None:
    """
    Set user context for error tracking.

    This associates errors with specific users for better debugging.

    Args:
        user_id: User identifier
        email: User email (optional)
        **extra_data: Additional user data
    """
    sentry_sdk.set_user(
        {
            "id": str(user_id),
            "email": email,
            **extra_data,
        }
    )


def set_firm_context(firm_id: int | str, firm_name: str | None = None) -> None:
    """
    Set firm (tenant) context for multi-tenant error tracking.

    Critical for debugging issues specific to a firm.

    Args:
        firm_id: Firm identifier
        firm_name: Firm name (optional)
    """
    sentry_sdk.set_tag("firm_id", str(firm_id))
    if firm_name:
        sentry_sdk.set_tag("firm_name", firm_name)

    sentry_sdk.set_context(
        "firm",
        {
            "id": str(firm_id),
            "name": firm_name or "Unknown",
        },
    )


def clear_context() -> None:
    """Clear all Sentry context (user, tags, etc.)."""
    sentry_sdk.set_user(None)
    sentry_sdk.clear_breadcrumbs()
