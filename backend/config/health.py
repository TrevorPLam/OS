"""
Health check endpoints for infrastructure monitoring (CONST-2 compliant).

These endpoints are used by load balancers, Kubernetes probes,
and monitoring systems to verify service health.

Per Constitution Section 9.4:
"Liveness and readiness checks must be correct and meaningful.
Readiness must reflect dependency availability where needed."
"""

import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
@never_cache
def health_check(request):
    """
    Liveness probe endpoint.
    
    Returns 200 OK if the application process is running.
    Used by orchestrators (Kubernetes, ECS, Docker) to determine if the
    process should be restarted.
    
    This endpoint should be fast and not check external dependencies.
    It only verifies that the Python process is responsive.

    GET /health/
    """
    return JsonResponse({
        "status": "healthy",
        "service": "consultantpro",
        "timestamp": timezone.now().isoformat(),
    }, status=200)


@require_GET
@never_cache
def readiness_check(request):
    """
    Readiness check endpoint with dependency verification.

    Returns 200 OK if the application can serve requests (database connected, cache available).
    Returns 503 Service Unavailable if any critical dependency is unreachable.
    Used for Kubernetes readiness probes and load balancer health checks.

    Critical dependencies:
    - Database (PostgreSQL)
    
    Non-critical dependencies (degraded mode):
    - Cache (Redis/Memcached)

    GET /health/ready/
    """
    checks = {}
    overall_status = "ready"
    
    # Check database connectivity (critical)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = {"status": "connected", "critical": True}
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}", exc_info=True)
        checks["database"] = {
            "status": "disconnected",
            "critical": True,
            "error": str(e)
        }
        overall_status = "not_ready"
    
    # Check cache connectivity (non-critical - can run in degraded mode)
    try:
        test_key = "_readiness_check_test"
        test_value = timezone.now().isoformat()
        cache.set(test_key, test_value, timeout=10)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            checks["cache"] = {"status": "connected", "critical": False}
            cache.delete(test_key)  # Clean up test key
        else:
            checks["cache"] = {
                "status": "degraded",
                "critical": False,
                "message": "Cache read/write mismatch"
            }
            logger.warning("Cache readiness check: read/write mismatch")
    except Exception as e:
        checks["cache"] = {
            "status": "unavailable",
            "critical": False,
            "error": str(e)
        }
        logger.warning(f"Cache readiness check failed: {e}")
    
    # Return 503 if any critical dependency failed
    status_code = 200 if overall_status == "ready" else 503
    
    return JsonResponse({
        "status": overall_status,
        "service": "consultantpro",
        "checks": checks,
        "timestamp": timezone.now().isoformat(),
    }, status=status_code)

