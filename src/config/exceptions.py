"""
Custom exception handlers for structured API error responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.db import IntegrityError
import logging

from modules.core.telemetry import log_event

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides structured error responses.

    Returns:
        Response with format: {
            "error": {
                "type": "ErrorType",
                "message": "Human-readable message",
                "details": {...},  # Optional field-specific errors
                "code": "ERROR_CODE"
            }
        }
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Restructure DRF errors
        error_response = {
            'error': {
                'type': exc.__class__.__name__,
                'message': str(exc),
                'code': get_error_code(exc, response.status_code)
            }
        }

        # Add field-specific errors if they exist
        if isinstance(response.data, dict):
            if 'detail' not in response.data:
                error_response['error']['details'] = response.data
            else:
                error_response['error']['message'] = response.data.get('detail', str(exc))

        response.data = error_response

        # Log error
        log_exception(exc, context, response.status_code)

        return response

    # Handle Django core exceptions
    if isinstance(exc, DjangoValidationError):
        error_response = {
            'error': {
                'type': 'ValidationError',
                'message': 'Validation failed',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else {'non_field_errors': exc.messages},
                'code': 'VALIDATION_ERROR'
            }
        }
        response = Response(error_response, status=status.HTTP_400_BAD_REQUEST)
        log_exception(exc, context, status.HTTP_400_BAD_REQUEST)
        return response

    if isinstance(exc, Http404):
        error_response = {
            'error': {
                'type': 'NotFound',
                'message': 'Resource not found',
                'code': 'NOT_FOUND'
            }
        }
        response = Response(error_response, status=status.HTTP_404_NOT_FOUND)
        log_exception(exc, context, status.HTTP_404_NOT_FOUND)
        return response

    if isinstance(exc, IntegrityError):
        error_response = {
            'error': {
                'type': 'IntegrityError',
                'message': 'Database integrity constraint violated',
                'details': str(exc),
                'code': 'INTEGRITY_ERROR'
            }
        }
        response = Response(error_response, status=status.HTTP_400_BAD_REQUEST)
        log_exception(exc, context, status.HTTP_400_BAD_REQUEST)
        return response

    # Handle all other exceptions
    logger.error("Unhandled exception")
    log_event(
        "api_unhandled_exception",
        operation="drf_exception_handler",
        error_class=exc.__class__.__name__,
    )

    error_response = {
        'error': {
            'type': 'ServerError',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_SERVER_ERROR'
        }
    }

    return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_error_code(exc, status_code):
    """Generate error code from exception and status."""
    error_codes = {
        400: 'BAD_REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        406: 'NOT_ACCEPTABLE',
        409: 'CONFLICT',
        429: 'TOO_MANY_REQUESTS',
        500: 'INTERNAL_SERVER_ERROR',
        503: 'SERVICE_UNAVAILABLE',
    }
    return error_codes.get(status_code, 'UNKNOWN_ERROR')


def log_exception(exc, context, status_code):
    """Log exceptions with appropriate severity."""
    view = context.get('view')
    request = context.get('request')

    log_data = {
        'exception_type': exc.__class__.__name__,
        'status_code': status_code,
        'view': view.__class__.__name__ if view else 'Unknown',
        'method': request.method if request else 'Unknown',
    }

    log_event(
        "api_exception",
        operation="drf_exception_handler",
        http_status=status_code,
        error_class=exc.__class__.__name__,
    )

    if status_code >= 500:
        logger.error("Server error", extra=log_data)
    elif status_code >= 400:
        logger.warning("Client error", extra=log_data)
    else:
        logger.info("Request processed with exception", extra=log_data)
