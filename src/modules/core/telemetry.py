"""
Telemetry helpers for safe, non-content metrics/events logging.
"""
from __future__ import annotations

from contextlib import contextmanager
import logging
import time
from typing import Any, Dict


logger = logging.getLogger("telemetry")

SAFE_FIELDS = {
    "channel",
    "count",
    "duration_ms",
    "error_class",
    "event",
    "http_status",
    "operation",
    "provider",
    "result",
    "status",
    "webhook_type",
}

SENSITIVE_FIELDS = {
    "address",
    "bcc",
    "cc",
    "client",
    "company_name",
    "contract_number",
    "email",
    "html_content",
    "invoice_id",
    "invoice_number",
    "message",
    "name",
    "path",
    "payload",
    "phone",
    "proposal_number",
    "reply_to",
    "subject",
    "text_content",
    "to",
    "user",
    "username",
}

REDACTED_VALUE = "[REDACTED]"


def sanitize_telemetry_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove or redact any potentially sensitive telemetry fields.
    """
    sanitized: Dict[str, Any] = {}
    for key, value in fields.items():
        if key in SENSITIVE_FIELDS:
            sanitized[key] = REDACTED_VALUE
            continue

        if key in SAFE_FIELDS:
            sanitized[key] = value
            continue

        if isinstance(value, (int, float, bool)) or value is None:
            sanitized[key] = value
            continue

        sanitized[key] = REDACTED_VALUE
    return sanitized


def log_event(event: str, **fields: Any) -> None:
    payload = sanitize_telemetry_fields(fields)
    payload["event"] = event
    logger.info("telemetry_event", extra={"telemetry": payload})


def log_metric(metric: str, **fields: Any) -> None:
    payload = sanitize_telemetry_fields(fields)
    payload["event"] = metric
    logger.info("telemetry_metric", extra={"telemetry": payload})


@contextmanager
def track_duration(operation: str, **fields: Any):
    start = time.monotonic()
    error_class = None
    try:
        yield
    except Exception as exc:
        error_class = exc.__class__.__name__
        raise
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        log_metric(
            "duration",
            operation=operation,
            duration_ms=duration_ms,
            error_class=error_class,
            **fields,
        )
