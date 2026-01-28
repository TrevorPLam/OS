"""
CSP report endpoint.

Receives CSP violation reports and logs them for monitoring.
"""

import json
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def csp_report(request):
    """Log CSP violation reports."""
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        logger.warning("Invalid CSP report payload received")
        return HttpResponse(status=400)

    report = payload.get("csp-report") or payload.get("report") or payload
    logger.warning("CSP violation reported: %s", report)

    try:
        from modules.core.telemetry import log_event, log_metric

        log_event("csp_violation", report=report)
        log_metric("csp_violation")
    except Exception:
        logger.debug("Telemetry unavailable for CSP reporting")

    return HttpResponse(status=204)
