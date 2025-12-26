"""
Core middleware for telemetry and observability.
"""
from __future__ import annotations

import time

from modules.core.telemetry import log_metric


class TelemetryRequestMiddleware:
    """
    Emit non-content HTTP request telemetry for operational observability.

    Logs duration, HTTP status, and resolved operation names without request content.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        operation = None

        if hasattr(request, "resolver_match") and request.resolver_match:
            operation = (
                request.resolver_match.view_name
                or request.resolver_match.url_name
                or request.resolver_match.route
            )

        try:
            response = self.get_response(request)
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            log_metric(
                "http_request",
                operation=operation or "unknown",
                http_status=500,
                duration_ms=duration_ms,
                error_class=exc.__class__.__name__,
                result="error",
            )
            raise

        duration_ms = int((time.monotonic() - start) * 1000)
        log_metric(
            "http_request",
            operation=operation or "unknown",
            http_status=response.status_code,
            duration_ms=duration_ms,
            result="success" if response.status_code < 500 else "error",
        )
        return response
