"""
Sentry Context Middleware.

Automatically adds firm and user context to all Sentry error reports.
This is critical for multi-tenant debugging.
"""

import logging
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from config.sentry import set_firm_context, set_user_context

logger = logging.getLogger(__name__)


class SentryContextMiddleware:
    """
    Middleware to add multi-tenant context to Sentry error reports.

    For each request, this middleware:
    1. Identifies the authenticated user
    2. Identifies the firm (tenant) from request
    3. Sets Sentry context for better error tracking

    This ensures all errors captured by Sentry include:
    - User ID and email
    - Firm ID and name (multi-tenant context)
    - Request metadata
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """
        Initialize middleware.

        Args:
            get_response: Next middleware or view in the chain
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process request and add Sentry context.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        # Add user context if authenticated
        if hasattr(request, "user") and request.user.is_authenticated:
            set_user_context(
                user_id=request.user.id,
                email=request.user.email,
                username=request.user.username,
                is_staff=request.user.is_staff,
                is_superuser=request.user.is_superuser,
            )

            # Add firm context if available (multi-tenant)
            if hasattr(request, "firm") and request.firm:
                set_firm_context(
                    firm_id=request.firm.id,
                    firm_name=request.firm.name,
                )
            # Fallback: try to get firm from user's profile
            elif hasattr(request.user, "firm") and request.user.firm:
                set_firm_context(
                    firm_id=request.user.firm.id,
                    firm_name=request.user.firm.name,
                )
            # Fallback: try to get firm from user's firm_id
            elif hasattr(request.user, "firm_id") and request.user.firm_id:
                set_firm_context(
                    firm_id=request.user.firm_id,
                    firm_name="Unknown",
                )

        response = self.get_response(request)
        return response
