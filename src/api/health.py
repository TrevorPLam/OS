"""
Health Check Endpoints (CONST-2)

Provides liveness and readiness probes for orchestration and load balancers.

Per Constitution Section 9.4:
"Liveness and readiness checks must be correct and meaningful.
Readiness must reflect dependency availability where needed."

Endpoints:
- /health/ - Liveness probe (always returns 200 if app is running)
- /ready/ - Readiness probe (checks dependencies: DB, cache, etc.)
"""

import logging
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
    This is used by orchestrators (Kubernetes, ECS) to determine if the
    process should be restarted.
    
    Returns:
        JsonResponse with status and timestamp
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'consultantpro',
        'timestamp': timezone.now().isoformat(),
    })


@require_GET
@never_cache
def readiness_check(request):
    """
    Readiness probe endpoint.
    
    Returns 200 OK only if all critical dependencies are available.
    This is used by load balancers to determine if the instance should
    receive traffic.
    
    Checks:
    - Database connectivity
    - Cache availability (if configured)
    
    Returns:
        JsonResponse with status, checks, and timestamp
        Status 200 if all checks pass, 503 if any check fails
    """
    checks = {}
    overall_status = 'ok'
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = {'status': 'ok', 'message': 'Connected'}
    except Exception as e:
        checks['database'] = {'status': 'error', 'message': str(e)}
        overall_status = 'error'
        logger.error(f"Database readiness check failed: {e}", exc_info=True)
    
    # Check cache connectivity (if configured)
    try:
        from django.core.cache import cache
        
        # Test cache read/write
        test_key = 'readiness_check_test'
        test_value = timezone.now().isoformat()
        cache.set(test_key, test_value, timeout=10)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            checks['cache'] = {'status': 'ok', 'message': 'Connected'}
        else:
            checks['cache'] = {'status': 'degraded', 'message': 'Cache read/write mismatch'}
            # Don't mark as error - cache is not critical
            
    except Exception as e:
        checks['cache'] = {'status': 'degraded', 'message': f'Cache unavailable: {str(e)}'}
        # Don't mark as error - cache is not critical
        logger.warning(f"Cache readiness check failed: {e}")
    
    response_data = {
        'status': overall_status,
        'service': 'consultantpro',
        'checks': checks,
        'timestamp': timezone.now().isoformat(),
    }
    
    # Return 503 if any critical dependency failed
    status_code = 200 if overall_status == 'ok' else 503
    
    return JsonResponse(response_data, status=status_code)


@require_GET
@never_cache
def startup_check(request):
    """
    Startup probe endpoint (optional).
    
    Returns 200 OK only after the application has completed initialization.
    This is useful for slow-starting applications.
    
    Currently delegates to readiness check, but can be extended to include
    additional startup-specific checks (e.g., migrations applied, config loaded).
    
    Returns:
        JsonResponse with status and timestamp
    """
    # For now, delegate to readiness check
    return readiness_check(request)
