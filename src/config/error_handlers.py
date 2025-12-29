"""
Enhanced Error Handling Utilities.

Provides consistent error responses and automatic Sentry integration.
"""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from config.sentry import capture_exception_with_context

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom exception handler with Sentry integration.

    Handles Django and DRF exceptions consistently and reports to Sentry.

    Args:
        exc: The exception that was raised
        context: Context dictionary with view and request information

    Returns:
        Response object with error details, or None if exception can't be handled
    """
    # Get the standard DRF error response
    response = drf_exception_handler(exc, context)

    # If DRF couldn't handle it, try Django exceptions
    if response is None:
        if isinstance(exc, Http404):
            response = Response(
                {"detail": "Not found.", "error_code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        elif isinstance(exc, PermissionDenied):
            response = Response(
                {"detail": str(exc) or "Permission denied.", "error_code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif isinstance(exc, ValidationError):
            response = Response(
                {"detail": str(exc), "error_code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            # Unhandled exception - this will be caught by Django's error handling
            # Log to Sentry with context
            request = context.get("request")
            view = context.get("view")

            capture_exception_with_context(
                exc,
                context={
                    "view": view.__class__.__name__ if view else "Unknown",
                    "path": request.path if request else "Unknown",
                    "method": request.method if request else "Unknown",
                },
                level="error",
            )
            logger.error(f"Unhandled exception in {view.__class__.__name__ if view else 'unknown view'}: {exc}")
            return None

    # Add custom error details
    if response is not None:
        # Add request ID if available
        request = context.get("request")
        if request and hasattr(request, "id"):
            response.data["request_id"] = request.id

        # Add firm context for multi-tenant debugging
        if request and hasattr(request, "firm") and request.firm:
            response.data["firm_id"] = request.firm.id

        # Log non-500 errors to Sentry as messages (not exceptions)
        if response.status_code >= 400 and response.status_code < 500:
            # Client errors - log as info/warning
            logger.warning(f"Client error {response.status_code}: {exc.__class__.__name__} - {str(exc)}")
        elif response.status_code >= 500:
            # Server errors - capture as exception
            view = context.get("view")
            capture_exception_with_context(
                exc,
                context={
                    "view": view.__class__.__name__ if view else "Unknown",
                    "path": request.path if request else "Unknown",
                    "method": request.method if request else "Unknown",
                    "status_code": response.status_code,
                },
                level="error",
            )

    return response


def handle_404(request, exception=None) -> JsonResponse:
    """
    Custom 404 error handler.

    Args:
        request: HTTP request
        exception: Optional exception that caused 404

    Returns:
        JSON response with 404 error
    """
    return JsonResponse(
        {
            "detail": "The requested resource was not found.",
            "error_code": "not_found",
            "path": request.path,
        },
        status=404,
    )


def handle_500(request) -> JsonResponse:
    """
    Custom 500 error handler.

    Args:
        request: HTTP request

    Returns:
        JSON response with 500 error
    """
    logger.error(f"Internal server error on path: {request.path}")

    return JsonResponse(
        {
            "detail": "An internal server error occurred. Our team has been notified.",
            "error_code": "internal_server_error",
        },
        status=500,
    )


def handle_403(request, exception=None) -> JsonResponse:
    """
    Custom 403 error handler.

    Args:
        request: HTTP request
        exception: Optional exception that caused 403

    Returns:
        JSON response with 403 error
    """
    return JsonResponse(
        {
            "detail": "You do not have permission to access this resource.",
            "error_code": "permission_denied",
            "path": request.path,
        },
        status=403,
    )


def handle_400(request, exception=None) -> JsonResponse:
    """
    Custom 400 error handler.

    Args:
        request: HTTP request
        exception: Optional exception that caused 400

    Returns:
        JSON response with 400 error
    """
    return JsonResponse(
        {
            "detail": "Bad request. Please check your request parameters.",
            "error_code": "bad_request",
            "path": request.path,
        },
        status=400,
    )
