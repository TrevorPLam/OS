"""
Rate limiting helpers.

Shared helpers for applying rate limit behavior across webhook endpoints.
"""

import logging

from django.http import HttpResponse

logger = logging.getLogger(__name__)


def enforce_webhook_rate_limit(request, provider: str, endpoint: str) -> HttpResponse | None:
    """
    Return a 429 response when a webhook rate limit is exceeded.

    Uses django-ratelimit's request.limited flag when block=False is configured.
    """
    if not getattr(request, "limited", False):
        return None

    ip_address = request.META.get("REMOTE_ADDR", "unknown")
    logger.warning(
        "Rate limit exceeded for %s webhook endpoint from IP %s", provider, ip_address
    )

    try:
        from modules.core.telemetry import log_event, log_metric

        log_event(
            "webhook_rate_limited",
            provider=provider,
            endpoint=endpoint,
            ip_address=ip_address,
        )
        log_metric("webhook_rate_limited", provider=provider, endpoint=endpoint)
    except Exception:
        logger.debug("Telemetry unavailable for webhook rate limit logging")

    return HttpResponse(status=429)
