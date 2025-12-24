"""
Firm Context Resolution Middleware (TIER 0).

Ensures every request has a firm context attached.
Firm context can be resolved from:
1. Subdomain (e.g., acme.consultantpro.com → Firm slug = "acme")
2. Session (for logged-in users via FirmMembership)
3. JWT Token (for API requests with firm_id claim)

TIER 0 REQUIREMENT: Requests without firm context are REJECTED (403 Forbidden).

Exceptions:
- Public endpoints (health checks, auth endpoints)
- Platform operator endpoints (explicitly marked)
"""
import logging
from typing import Optional

from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from modules.firm.models import Firm, FirmMembership


logger = logging.getLogger(__name__)


class FirmContextMiddleware(MiddlewareMixin):
    """
    TIER 0: Firm Context Resolution Middleware.

    Attaches firm context to every request or rejects it.
    """

    # Public endpoints that don't require firm context
    PUBLIC_PATHS = [
        '/api/auth/login/',
        '/api/auth/register/',
        '/api/auth/token/',
        '/api/auth/token/refresh/',
        '/api/health/',
        '/api/docs/',
        '/api/schema/',
        '/admin/login/',
    ]

    # Platform operator endpoints (require platform role, not firm context)
    PLATFORM_PATHS = [
        '/api/platform/',
    ]

    def process_request(self, request: HttpRequest) -> Optional[JsonResponse]:
        """
        Resolve firm context for the request.

        Returns:
            None if firm context resolved successfully
            JsonResponse with 403 if firm context cannot be resolved
        """
        # Skip firm context for public endpoints
        if self._is_public_path(request.path):
            request.firm = None
            request.firm_context_source = 'public'
            return None

        # Skip firm context for platform endpoints (different auth model)
        if self._is_platform_path(request.path):
            request.firm = None
            request.firm_context_source = 'platform'
            return None

        # Try to resolve firm context from multiple sources
        firm, source = self._resolve_firm_context(request)

        if firm is None:
            # TIER 0: Reject requests without firm context
            logger.warning(
                f"Request rejected: No firm context. "
                f"Path: {request.path}, "
                f"User: {getattr(request.user, 'id', 'anonymous')}"
            )
            return JsonResponse(
                {
                    'error': 'Firm context required',
                    'detail': (
                        'This request requires firm/workspace context. '
                        'Please access via firm subdomain or include firm_id in token.'
                    ),
                    'code': 'FIRM_CONTEXT_REQUIRED'
                },
                status=403
            )

        # Attach firm context to request
        request.firm = firm
        request.firm_context_source = source
        
        # TIER 0.6: Check for active break-glass session and add impersonation indicator
        self._check_break_glass_session(request)

        logger.debug(
            f"Firm context resolved: {firm.slug} "
            f"(source: {source}, path: {request.path})"
        )

        return None
    
    def _check_break_glass_session(self, request: HttpRequest):
        """
        Check if user has an active break-glass session (TIER 0.6).
        
        Adds break-glass context to request for impersonation awareness.
        """
        from modules.firm.models import BreakGlassSession, UserProfile
        
        # Default: no break-glass session
        request.break_glass_session = None
        request.is_impersonating = False
        
        if not request.user or not request.user.is_authenticated:
            return
        
        # Check if user is a break-glass operator
        if not hasattr(request.user, 'platform_profile'):
            return
        
        profile = request.user.platform_profile
        if not profile or not profile.is_break_glass_operator:
            return
        
        # Check for active break-glass session for this firm
        if not request.firm:
            return
        
        # Find active session
        active_sessions = BreakGlassSession.objects.active().for_firm(request.firm).filter(
            operator=request.user
        )
        
        if active_sessions.exists():
            session = active_sessions.first()
            request.break_glass_session = session
            request.is_impersonating = True
            
            logger.info(
                f"Break-glass session active: {session.id} for {request.firm.slug} "
                f"by {request.user.username}"
            )


    def _is_public_path(self, path: str) -> bool:
        """Check if path is a public endpoint."""
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)

    def _is_platform_path(self, path: str) -> bool:
        """Check if path is a platform operator endpoint."""
        return any(path.startswith(platform_path) for platform_path in self.PLATFORM_PATHS)

    def _resolve_firm_context(self, request: HttpRequest) -> tuple[Optional[Firm], str]:
        """
        Resolve firm context from available sources.

        Priority order:
        1. Subdomain (most specific)
        2. JWT token firm_id claim
        3. User session (via FirmMembership)

        Returns:
            (Firm instance, source_name) or (None, 'none')
        """
        # 1. Try subdomain resolution
        firm = self._resolve_from_subdomain(request)
        if firm:
            return (firm, 'subdomain')

        # 2. Try JWT token
        firm = self._resolve_from_token(request)
        if firm:
            return (firm, 'token')

        # 3. Try session (for logged-in users)
        firm = self._resolve_from_session(request)
        if firm:
            return (firm, 'session')

        return (None, 'none')

    def _resolve_from_subdomain(self, request: HttpRequest) -> Optional[Firm]:
        """
        Resolve firm from subdomain.

        Example: acme.consultantpro.com → Firm with slug='acme'
        """
        host = request.get_host().split(':')[0]  # Remove port if present
        parts = host.split('.')

        # Check if this looks like a firm subdomain
        # Example: acme.consultantpro.com has 3+ parts
        if len(parts) < 3:
            return None

        # First part is the potential firm slug
        potential_slug = parts[0]

        # Skip special subdomains
        if potential_slug in ['www', 'api', 'admin', 'platform']:
            return None

        try:
            firm = Firm.objects.get(slug=potential_slug, status__in=['trial', 'active'])
            return firm
        except Firm.DoesNotExist:
            logger.debug(f"No active firm found for subdomain: {potential_slug}")
            return None

    def _resolve_from_token(self, request: HttpRequest) -> Optional[Firm]:
        """
        Resolve firm from JWT token firm_id claim.

        Token must include 'firm_id' in payload.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None

        try:
            # Use DRF's JWT authentication to validate and decode token
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(auth_header.split(' ')[1])

            # Extract firm_id from token payload
            firm_id = validated_token.get('firm_id')
            if not firm_id:
                logger.debug("JWT token missing firm_id claim")
                return None

            firm = Firm.objects.get(id=firm_id, status__in=['trial', 'active'])
            return firm

        except InvalidToken:
            logger.debug("Invalid JWT token")
            return None
        except Firm.DoesNotExist:
            logger.warning(f"Firm {firm_id} from token not found or inactive")
            return None
        except Exception as e:
            logger.error(f"Error resolving firm from token: {e}")
            return None

    def _resolve_from_session(self, request: HttpRequest) -> Optional[Firm]:
        """
        Resolve firm from user session via FirmMembership.

        For users who belong to multiple firms, we use:
        1. session['active_firm_id'] if set
        2. User's primary/default firm (first membership)
        """
        if not request.user or not request.user.is_authenticated:
            return None

        # Check if user has explicitly set an active firm in their session
        active_firm_id = request.session.get('active_firm_id')
        if active_firm_id:
            try:
                # Verify user has access to this firm
                membership = FirmMembership.objects.select_related('firm').get(
                    user=request.user,
                    firm_id=active_firm_id,
                    firm__status__in=['trial', 'active']
                )
                return membership.firm
            except FirmMembership.DoesNotExist:
                logger.warning(
                    f"User {request.user.id} session references inaccessible firm {active_firm_id}"
                )
                # Clear invalid session firm
                del request.session['active_firm_id']

        # Fall back to user's first firm (primary firm)
        try:
            membership = FirmMembership.objects.select_related('firm').filter(
                user=request.user,
                firm__status__in=['trial', 'active']
            ).first()

            if membership:
                return membership.firm
        except Exception as e:
            logger.error(f"Error resolving firm from session: {e}")

        return None
