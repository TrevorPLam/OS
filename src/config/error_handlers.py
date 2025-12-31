"""
Enhanced Error Handling Utilities (ASSESS-I5.4).

Provides consistent error responses with structured error codes and automatic Sentry integration.
Maps known errors (Stripe, validation, etc.) to standardized error codes.
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

# ASSESS-I5.4: Structured error codes for known error scenarios
ERROR_CODES = {
    # Authentication & Authorization
    "authentication_required": "AUTH_001",
    "invalid_token": "AUTH_002",
    "token_expired": "AUTH_003",
    "permission_denied": "AUTH_004",
    "insufficient_permissions": "AUTH_005",
    
    # Validation Errors
    "validation_error": "VAL_001",
    "invalid_input": "VAL_002",
    "missing_required_field": "VAL_003",
    "invalid_format": "VAL_004",
    
    # Resource Errors
    "not_found": "RES_001",
    "resource_not_found": "RES_002",
    "already_exists": "RES_003",
    "conflict": "RES_004",
    
    # Payment/Stripe Errors
    "payment_failed": "PAY_001",
    "card_declined": "PAY_002",
    "insufficient_funds": "PAY_003",
    "invalid_card": "PAY_004",
    "expired_card": "PAY_005",
    "processing_error": "PAY_006",
    "payment_method_required": "PAY_007",
    
    # Business Logic Errors
    "business_rule_violation": "BIZ_001",
    "invalid_state_transition": "BIZ_002",
    "quota_exceeded": "BIZ_003",
    
    # System Errors
    "internal_server_error": "SYS_001",
    "service_unavailable": "SYS_002",
    "timeout": "SYS_003",
    "rate_limit_exceeded": "SYS_004",
    
    # Multi-tenancy Errors
    "firm_not_found": "TEN_001",
    "cross_firm_access": "TEN_002",
    "tenant_isolation_violation": "TEN_003",
}


def map_stripe_error(stripe_error: Exception) -> tuple[str, str]:
    """
    Map Stripe errors to standardized error codes (ASSESS-I5.4).
    
    Args:
        stripe_error: Stripe exception
        
    Returns:
        Tuple of (error_code, error_message)
    """
    error_str = str(stripe_error).lower()
    
    # Map common Stripe error types
    if "card_declined" in error_str or "card was declined" in error_str:
        return ERROR_CODES["card_declined"], "Your card was declined. Please try a different payment method."
    elif "insufficient_funds" in error_str or "insufficient funds" in error_str:
        return ERROR_CODES["insufficient_funds"], "Insufficient funds. Please use a different payment method."
    elif "invalid_card" in error_str or "invalid card number" in error_str:
        return ERROR_CODES["invalid_card"], "Invalid card number. Please check your card details."
    elif "expired_card" in error_str or "card expired" in error_str:
        return ERROR_CODES["expired_card"], "Your card has expired. Please use a different payment method."
    elif "processing_error" in error_str or "processing error" in error_str:
        return ERROR_CODES["processing_error"], "Payment processing error. Please try again later."
    else:
        return ERROR_CODES["payment_failed"], f"Payment failed: {str(stripe_error)}"


def get_error_code(error_type: str, default: str = "SYS_001") -> str:
    """
    Get error code for error type.
    
    Args:
        error_type: Error type key
        default: Default error code if not found
        
    Returns:
        Error code string
    """
    return ERROR_CODES.get(error_type, default)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom exception handler with structured error responses (ASSESS-I5.4).

    Handles Django and DRF exceptions consistently with error codes and reports to Sentry.

    Args:
        exc: The exception that was raised
        context: Context dictionary with view and request information

    Returns:
        Response object with structured error details, or None if exception can't be handled
    """
    # Check for Stripe errors first (ASSESS-I5.4)
    if "stripe" in exc.__class__.__module__.lower() or "stripe" in str(type(exc)).lower():
        error_code, error_message = map_stripe_error(exc)
        response = Response(
            {
                "detail": error_message,
                "error_code": error_code,
                "error_type": "payment_error",
            },
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )
    else:
        # Get the standard DRF error response
        response = drf_exception_handler(exc, context)

        # If DRF couldn't handle it, try Django exceptions
        if response is None:
            if isinstance(exc, Http404):
                response = Response(
                    {
                        "detail": "The requested resource was not found.",
                        "error_code": get_error_code("not_found"),
                        "error_type": "not_found",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            elif isinstance(exc, PermissionDenied):
                response = Response(
                    {
                        "detail": str(exc) or "You do not have permission to access this resource.",
                        "error_code": get_error_code("permission_denied"),
                        "error_type": "permission_denied",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            elif isinstance(exc, ValidationError):
                response = Response(
                    {
                        "detail": str(exc),
                        "error_code": get_error_code("validation_error"),
                        "error_type": "validation_error",
                    },
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

    # Add structured error details (ASSESS-I5.4)
    if response is not None:
        # Ensure response.data is a dict
        if not isinstance(response.data, dict):
            response.data = {"detail": str(response.data)}
        
        # Add error_code if not present
        if "error_code" not in response.data:
            # Try to infer from status code
            if response.status_code == 404:
                response.data["error_code"] = get_error_code("not_found")
            elif response.status_code == 403:
                response.data["error_code"] = get_error_code("permission_denied")
            elif response.status_code == 400:
                response.data["error_code"] = get_error_code("validation_error")
            else:
                response.data["error_code"] = get_error_code("internal_server_error")
        
        # Add error_type if not present
        if "error_type" not in response.data:
            if response.status_code >= 500:
                response.data["error_type"] = "server_error"
            elif response.status_code == 404:
                response.data["error_type"] = "not_found"
            elif response.status_code == 403:
                response.data["error_type"] = "permission_denied"
            else:
                response.data["error_type"] = "client_error"
        
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
    Custom 404 error handler (ASSESS-I5.4).

    Args:
        request: HTTP request
        exception: Optional exception that caused 404

    Returns:
        JSON response with structured 404 error
    """
    return JsonResponse(
        {
            "detail": "The requested resource was not found.",
            "error_code": get_error_code("not_found"),
            "error_type": "not_found",
            "path": request.path,
        },
        status=404,
    )


def handle_500(request) -> JsonResponse:
    """
    Custom 500 error handler (ASSESS-I5.4).

    Args:
        request: HTTP request

    Returns:
        JSON response with structured 500 error
    """
    logger.error(f"Internal server error on path: {request.path}")

    return JsonResponse(
        {
            "detail": "An internal server error occurred. Our team has been notified.",
            "error_code": get_error_code("internal_server_error"),
            "error_type": "server_error",
        },
        status=500,
    )


def handle_403(request, exception=None) -> JsonResponse:
    """
    Custom 403 error handler (ASSESS-I5.4).

    Args:
        request: HTTP request
        exception: Optional exception that caused 403

    Returns:
        JSON response with structured 403 error
    """
    return JsonResponse(
        {
            "detail": "You do not have permission to access this resource.",
            "error_code": get_error_code("permission_denied"),
            "error_type": "permission_denied",
            "path": request.path,
        },
        status=403,
    )


def handle_400(request, exception=None) -> JsonResponse:
    """
    Custom 400 error handler (ASSESS-I5.4).

    Args:
        request: HTTP request
        exception: Optional exception that caused 400

    Returns:
        JSON response with structured 400 error
    """
    return JsonResponse(
        {
            "detail": "Bad request. Please check your request parameters.",
            "error_code": get_error_code("validation_error"),
            "error_type": "validation_error",
            "path": request.path,
        },
        status=400,
    )
