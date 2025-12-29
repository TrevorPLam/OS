"""
Health check endpoints for infrastructure monitoring.

These endpoints are used by load balancers, Kubernetes probes,
and monitoring systems to verify service health.
"""

import logging

from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Basic health check endpoint.

    Returns 200 OK if the application is running.
    Used for simple liveness probes.

    GET /health/
    """
    return JsonResponse({"status": "healthy"}, status=200)


def readiness_check(request):
    """
    Readiness check endpoint with database connectivity verification.

    Returns 200 OK if the application can serve requests (database connected).
    Returns 503 Service Unavailable if database is unreachable.
    Used for Kubernetes readiness probes and load balancer health checks.

    GET /health/ready/
    """
    try:
        # Test database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return JsonResponse(
            {
                "status": "ready",
                "checks": {
                    "database": "connected",
                },
            },
            status=200,
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse(
            {
                "status": "not_ready",
                "checks": {
                    "database": "disconnected",
                },
                "error": str(e),
            },
            status=503,
        )
