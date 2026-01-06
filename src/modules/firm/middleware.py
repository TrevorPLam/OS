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

import json
import logging

from django.http import HttpRequest, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from modules.auth.authentication import CookieJWTAuthentication
from modules.firm.models import BreakGlassSession, Firm, FirmMembership
from modules.firm.utils import get_active_break_glass_session

logger = logging.getLogger(__name__)


class FirmContextMiddleware(MiddlewareMixin):
    """
    TIER 0: Firm Context Resolution Middleware.

    Attaches firm context to every request or rejects it.
    """

    # Public endpoints that don't require firm context
    # NOTE: Keep exact matches separate from prefixes so we don't accidentally
    # make the entire site public (e.g., treating '/' as a prefix would match everything).
    PUBLIC_EXACT_PATHS = [
        "/",
        "/favicon.ico",
    ]

    PUBLIC_PATH_PREFIXES = [
        "/api/auth/",  # /api/auth/*
        "/api/health/",
        "/health/",
        "/api/docs/",
        "/api/schema/",
        "/api/redoc/",
        "/admin/",
        "/api/v1/tracking/collect",
    ]

    # Platform operator endpoints (require platform role, not firm context)
    PLATFORM_PATHS = [
        "/api/platform/",
    ]

    def process_request(self, request: HttpRequest) -> JsonResponse | None:
        """
        Resolve firm context for the request.

        Returns:
            None if firm context resolved successfully
            JsonResponse with 403 if firm context cannot be resolved
        """
        # Skip firm context for public endpoints
        if self._is_public_path(request.path):
            request.firm = None
            request.firm_context_source = "public"
            return None

        # Skip firm context for platform endpoints (different auth model)
        if self._is_platform_path(request.path):
            request.firm = None
            request.firm_context_source = "platform"
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
                    "error": "Firm context required",
                    "detail": (
                        "This request requires firm/workspace context. "
                        "Please access via firm subdomain or include firm_id in token."
                    ),
                    "code": "FIRM_CONTEXT_REQUIRED",
                },
                status=403,
            )

        # Attach firm context to request
        request.firm = firm
        request.firm_context_source = source

        logger.debug(f"Firm context resolved: {firm.slug} " f"(source: {source}, path: {request.path})")

        return None

    def _is_public_path(self, path: str) -> bool:
        """Check if path is a public endpoint."""
        if path in self.PUBLIC_EXACT_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in self.PUBLIC_PATH_PREFIXES)

    def _is_platform_path(self, path: str) -> bool:
        """Check if path is a platform operator endpoint."""
        return any(path.startswith(platform_path) for platform_path in self.PLATFORM_PATHS)

    def _resolve_firm_context(self, request: HttpRequest) -> tuple[Firm | None, str]:
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
            return (firm, "subdomain")

        # 2. Try JWT token
        firm = self._resolve_from_token(request)
        if firm:
            return (firm, "token")

        # 3. Try session (for logged-in users)
        firm = self._resolve_from_session(request)
        if firm:
            return (firm, "session")

        return (None, "none")

    def _resolve_from_subdomain(self, request: HttpRequest) -> Firm | None:
        """
        Resolve firm from subdomain.

        Example: acme.consultantpro.com → Firm with slug='acme'
        """
        host = request.get_host().split(":")[0]  # Remove port if present
        parts = host.split(".")

        # Check if this looks like a firm subdomain
        # Example: acme.consultantpro.com has 3+ parts
        if len(parts) < 3:
            return None

        # First part is the potential firm slug
        potential_slug = parts[0]

        # Skip special subdomains
        if potential_slug in ["www", "api", "admin", "platform"]:
            return None

        try:
            firm = Firm.objects.get(slug=potential_slug, status__in=["trial", "active"])
            return firm
        except Firm.DoesNotExist:
            logger.debug(f"No active firm found for subdomain: {potential_slug}")
            return None

    def _resolve_from_token(self, request: HttpRequest) -> Firm | None:
        """
        Resolve firm from JWT token firm_id claim.

        Token must include 'firm_id' in payload.
        """
        jwt_auth = CookieJWTAuthentication()
        validated_token = jwt_auth.get_validated_token_from_request(request)
        if validated_token is None:
            return None

        firm_id = validated_token.get("firm_id")
        if not firm_id:
            logger.debug("JWT token missing firm_id claim")
            return None

        try:
            firm = Firm.objects.get(id=firm_id, status__in=["trial", "active"])
            return firm
        except Firm.DoesNotExist:
            logger.warning(f"Firm {firm_id} from token not found or inactive")
            return None
        except Exception as e:
            logger.error(f"Error resolving firm from token: {e}")
            return None

    def _resolve_from_session(self, request: HttpRequest) -> Firm | None:
        """
        Resolve firm from user session via FirmMembership.

        For users who belong to multiple firms, we use:
        1. session['active_firm_id'] if set
        2. User's primary/default firm (first membership)
        """
        if not request.user or not request.user.is_authenticated:
            return None

        # Check if user has explicitly set an active firm in their session
        active_firm_id = request.session.get("active_firm_id")
        if active_firm_id:
            try:
                # Verify user has access to this firm
                membership = FirmMembership.objects.select_related("firm").get(
                    user=request.user, firm_id=active_firm_id, firm__status__in=["trial", "active"]
                )
                return membership.firm
            except FirmMembership.DoesNotExist:
                logger.warning(f"User {request.user.id} session references inaccessible firm {active_firm_id}")
                # Clear invalid session firm
                del request.session["active_firm_id"]

        # Fall back to user's first firm (primary firm)
        try:
            membership = (
                FirmMembership.objects.select_related("firm")
                .filter(user=request.user, firm__status__in=["trial", "active"])
                .first()
            )

            if membership:
                return membership.firm
        except Exception as e:
            logger.error(f"Error resolving firm from session: {e}")

        return None


class BreakGlassImpersonationMiddleware:
    """Expose break-glass impersonation context to downstream layers.

    - Attaches the active break-glass session to the request when present
    - Surfaces impersonation metadata via response headers for UI banners
    - Emits immutable audit events for impersonated requests
    """

    HEADER_NAME = "X-Break-Glass-Impersonation"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request.break_glass_session = self._resolve_break_glass_session(request)
        response = self.get_response(request)

        if request.break_glass_session and request.break_glass_session.impersonated_user:
            payload = self._serialize_session(request.break_glass_session)
            response[self.HEADER_NAME] = json.dumps(payload)
            response["X-Impersonation-Mode"] = "true"
            self._log_impersonated_request(request, response)

        return response

    def _resolve_break_glass_session(self, request: HttpRequest):
        """Lookup the active break-glass session for the current operator."""
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return None

        if not hasattr(request.user, "platform_profile"):
            return None

        if not getattr(request, "firm", None):
            return None

        session = get_active_break_glass_session(request.firm)
        if session and session.operator_id == request.user.id:
            return session

        return None

    def _serialize_session(self, session: BreakGlassSession) -> dict:
        """Serialize impersonation context for UI banners."""
        impersonated = session.impersonated_user
        return {
            "session_id": session.id,
            "impersonated_user": (
                impersonated.get_full_name() or impersonated.email or impersonated.username if impersonated else ""
            ),
            "reason": session.reason,
            "expires_at": session.expires_at.isoformat(),
        }

    def _log_impersonated_request(self, request: HttpRequest, response):
        """Record an immutable audit event for impersonated requests."""
        try:
            from modules.firm.audit import audit
        except Exception:
            return

        session = request.break_glass_session
        audit.log_break_glass_event(
            firm=session.firm,
            action="break_glass_impersonated_request",
            actor=session.operator,
            reason=session.reason,
            target_model=session.__class__.__name__,
            target_id=session.id,
            metadata={
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "impersonated_user_id": session.impersonated_user_id,
                "request_id": request.META.get("HTTP_X_REQUEST_ID", ""),
            },
        )
