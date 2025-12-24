"""
Portal Containment Middleware (TIER 0: Task 0.4).

This middleware implements default-deny portal containment:
- Portal users can ONLY access portal endpoints (allowlist)
- Portal users receive 403 on all other endpoints
- Firm users can access all endpoints

TIER 0 REQUIREMENT: Portal containment must be enforced at middleware level.
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from modules.clients.models import ClientPortalUser


class PortalContainmentMiddleware(MiddlewareMixin):
    """
    TIER 0: Portal Containment Middleware (Default-Deny).

    Enforces that portal users can ONLY access portal-specific endpoints.
    All other endpoints return 403 Forbidden.

    This is a defense-in-depth measure on top of permission classes.
    """

    # Portal-allowed URL prefixes (allowlist)
    PORTAL_ALLOWED_PATHS = [
        '/api/portal/',  # All portal endpoints
        '/api/auth/login/',  # Login endpoint
        '/api/auth/logout/',  # Logout endpoint
        '/api/auth/profile/',  # User profile
        '/api/auth/change-password/',  # Password change
    ]

    # Paths that don't require portal containment check (public)
    PUBLIC_PATHS = [
        '/api/auth/login/',
        '/api/auth/register/',
        '/api/health/',
        '/api/docs/',
        '/api/schema/',
        '/admin/login/',
        '/admin/',
    ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check portal containment before view execution.

        TIER 0: Portal users can only access allowlisted endpoints.
        """
        # Skip unauthenticated requests
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        # Skip public paths
        if self._is_public_path(request.path):
            return None

        # Check if user is a portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
            # User is a portal user - check if path is allowed
            if not self._is_portal_allowed_path(request.path):
                return JsonResponse({
                    'error': 'Access denied',
                    'code': 'PORTAL_ACCESS_DENIED',
                    'message': 'Portal users do not have access to this endpoint.',
                    'detail': f'Portal users can only access endpoints under /api/portal/.'
                }, status=403)
        except ClientPortalUser.DoesNotExist:
            # User is a firm user - allow access to all endpoints
            pass

        return None

    def _is_public_path(self, path):
        """Check if path is public (no containment check needed)."""
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)

    def _is_portal_allowed_path(self, path):
        """Check if path is in portal allowlist."""
        return any(path.startswith(allowed_path) for allowed_path in self.PORTAL_ALLOWED_PATHS)
