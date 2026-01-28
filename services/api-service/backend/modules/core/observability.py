"""
Observability utilities and metrics collectors.

Implements docs/03-reference/requirements/DOC-21.md OBSERVABILITY_AND_SRE requirements:
- Correlation IDs
- Required metrics for API, Workers, Integrations, Documents, Billing
- Alert thresholds
- Tenant-safe logging
"""

import uuid
from typing import Optional, Dict, Any
from django.utils import timezone
from .telemetry import log_metric, log_event


# Correlation ID utilities (per docs/03-reference/requirements/DOC-21.md section 1)
def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def get_correlation_id_from_request(request) -> str:
    """Get or generate correlation ID for a request."""
    return getattr(request, "correlation_id", None) or request.META.get("HTTP_X_CORRELATION_ID") or generate_correlation_id()


# Alias for backwards compatibility
get_correlation_id = get_correlation_id_from_request


# API metrics (per docs/03-reference/requirements/DOC-21.md section 2)
def track_api_request(route: str, status_code: int, duration_ms: int, correlation_id: Optional[str] = None, tenant_id: Optional[int] = None):
    """Track API request metrics."""
    log_metric(
        "api_request",
        route_group=route,
        http_status=status_code,
        duration_ms=duration_ms,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
        result="success" if status_code < 500 else "error",
    )


# Worker metrics (per docs/03-reference/requirements/DOC-21.md section 2)
def track_job_execution(job_type: str, status: str, duration_ms: int, retry_count: int = 0, correlation_id: Optional[str] = None, tenant_id: Optional[int] = None):
    """Track worker job execution metrics."""
    log_metric(
        "job_execution",
        job_type=job_type,
        status=status,
        duration_ms=duration_ms,
        retry_count=retry_count,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


def track_dlq_depth(job_type: str, depth: int, tenant_id: Optional[int] = None):
    """Track DLQ depth metrics."""
    log_metric(
        "dlq_depth",
        job_type=job_type,
        depth=depth,
        tenant_id=tenant_id,
    )


# Integration metrics (per docs/03-reference/requirements/DOC-21.md section 2)
def track_email_ingest(status: str, lag_seconds: int = 0, correlation_id: Optional[str] = None, tenant_id: Optional[int] = None):
    """Track email ingestion metrics."""
    log_metric(
        "email_ingest",
        status=status,
        lag_seconds=lag_seconds,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


def track_calendar_sync(provider: str, status: str, lag_seconds: int = 0, correlation_id: Optional[str] = None, tenant_id: Optional[int] = None):
    """Track calendar sync metrics."""
    log_metric(
        "calendar_sync",
        provider=provider,
        status=status,
        lag_seconds=lag_seconds,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


# Document metrics (per docs/03-reference/requirements/DOC-21.md section 2)
def track_document_upload(status: str, file_size_bytes: int, correlation_id: Optional[str] = None, tenant_id: Optional[int] = None):
    """Track document upload metrics."""
    log_metric(
        "document_upload",
        status=status,
        file_size_bytes=file_size_bytes,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


def track_document_download(status: str, correlation_id: Optional[str] = None, tenant_id: Optional[int] = None):
    """Track document download metrics."""
    log_metric(
        "document_download",
        status=status,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


def track_scan_pending_count(count: int, tenant_id: Optional[int] = None):
    """Track document scan pending count."""
    log_metric(
        "scan_pending_count",
        count=count,
        tenant_id=tenant_id,
    )


# Billing metrics (per docs/03-reference/requirements/DOC-21.md section 2)
def track_billing_posting(status: str, correlation_id: Optional[str] = None, tenant_id: Optional[int] = None):
    """Track billing ledger posting metrics."""
    log_metric(
        "billing_posting",
        status=status,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


def track_idempotency_collision(operation: str, correlation_id: Optional[str] = None, tenant_id: Optional[int] = None):
    """Track idempotency key collision (indicates retry)."""
    log_event(
        "idempotency_collision",
        operation=operation,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


# Alert utilities (per docs/03-reference/requirements/DOC-21.md section 3)
def check_alert_threshold(metric_name: str, current_value: float, threshold: float, window_seconds: int = 300) -> bool:
    """
    Check if metric exceeds alert threshold.

    Args:
        metric_name: Name of the metric
        current_value: Current metric value
        threshold: Alert threshold
        window_seconds: Time window for sustained check (default 5 minutes)

    Returns:
        True if alert should fire
    """
    # STUB: In production, implement proper threshold checking with time windows
    return current_value > threshold


# Alert thresholds (per docs/03-reference/requirements/DOC-21.md section 3)
DEFAULT_ALERT_THRESHOLDS = {
    "job_failure_rate": 0.1,  # 10% failure rate
    "dlq_depth": 100,  # 100 items in DLQ
    "integration_lag_seconds": 900,  # 15 minutes lag
    "permission_denial_rate": 0.05,  # 5% denial rate
    "api_error_rate": 0.05,  # 5% error rate
    "document_scan_pending": 50,  # 50 pending scans
}


def get_alert_threshold(metric_name: str, tenant_id: Optional[int] = None) -> float:
    """
    Get alert threshold for a metric.

    Per docs/03-reference/requirements/DOC-21.md section 3: Allows tenant-specific configuration.
    """
    # STUB: In production, load tenant-specific thresholds from configuration
    return DEFAULT_ALERT_THRESHOLDS.get(metric_name, 0)


# Structured logging with correlation (per docs/03-reference/requirements/DOC-21.md section 4)
def log_with_context(
    level: str,
    message: str,
    correlation_id: Optional[str] = None,
    tenant_id: Optional[int] = None,
    actor_id: Optional[int] = None,
    object_type: Optional[str] = None,
    object_id: Optional[str] = None,
    **kwargs
):
    """
    Log with full observability context.

    Per docs/03-reference/requirements/DOC-21.md section 4: Logs MUST include tenant_id, correlation_id, actor, primary object ids.
    """
    import logging
    logger = logging.getLogger("observability")

    context = {
        "correlation_id": correlation_id,
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "object_type": object_type,
        "object_id": object_id,
    }
    context.update(kwargs)

    # Filter None values
    context = {k: v for k, v in context.items() if v is not None}

    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(message, extra={"context": context})
