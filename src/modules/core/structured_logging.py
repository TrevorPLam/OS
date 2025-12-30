"""
Structured Logging with No-Content Guarantees (DOC-21.2)

Provides structured logging formatters and utilities that enforce:
1. Required fields: tenant_id, correlation_id, actor, primary object ids
2. No-content logging: Never log email bodies, document content, etc.
3. PII minimization: Minimize R-PII in logs

Per docs/21 section 4: Log requirements.
"""

import logging
import json
import uuid
from typing import Optional, Dict, Any, List
from django.conf import settings


class StructuredLogFormatter(logging.Formatter):
    """
    JSON formatter that ensures required fields are present per docs/21 section 4.

    Required fields:
    - tenant_id (when applicable)
    - correlation_id
    - actor (when applicable)
    - primary object ids

    This formatter also filters out content fields to enforce no-content logging.
    """

    # Content fields that should NEVER appear in logs
    FORBIDDEN_CONTENT_FIELDS = [
        "body",
        "content",
        "email_body",
        "message_body",
        "document_content",
        "file_content",
        "raw_data",
        "payload_content",
        "full_text",
        "html_content",
        "text_content",
        "attachment_data",
    ]

    # PII fields that should be minimized/masked
    PII_FIELDS = [
        "email",
        "phone",
        "address",
        "ssn",
        "tax_id",
        "credit_card",
        "password",
        "secret",
        "token",
        "api_key",
    ]

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON with required fields."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add required fields per docs/21 section 4
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = str(record.correlation_id)
        if hasattr(record, "actor"):
            log_data["actor"] = record.actor
        if hasattr(record, "object_id"):
            log_data["object_id"] = record.object_id
        if hasattr(record, "object_type"):
            log_data["object_type"] = record.object_type

        # Add custom extras (filtered for content)
        if hasattr(record, "extra_data"):
            filtered_extra = self._filter_content(record.extra_data)
            log_data["extra"] = filtered_extra

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

    def _filter_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter content fields and PII from log data.

        Per docs/21 section 4: Logs MUST redact HR and minimize PII.
        """
        filtered = {}
        for key, value in data.items():
            # Check for forbidden content fields
            if any(field in key.lower() for field in self.FORBIDDEN_CONTENT_FIELDS):
                filtered[key] = "[CONTENT_REDACTED]"
                continue

            # Check for PII fields
            if any(field in key.lower() for field in self.PII_FIELDS):
                if isinstance(value, str) and len(value) > 0:
                    # Mask PII: show first 2 chars + length
                    filtered[key] = f"{value[:2]}***({len(value)} chars)"
                else:
                    filtered[key] = "[PII_REDACTED]"
                continue

            # Recursively filter dicts
            if isinstance(value, dict):
                filtered[key] = self._filter_content(value)
            elif isinstance(value, list):
                filtered[key] = [
                    self._filter_content(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered[key] = value

        return filtered


class NoContentLogger:
    """
    Logger that enforces no-content guarantees per DOC-21.2.

    Usage:
        logger = NoContentLogger(__name__)

        # Safe: log with required context
        logger.log_operation(
            tenant_id=firm.id,
            correlation_id=correlation_id,
            actor=user.username,
            operation="document_upload",
            object_type="Document",
            object_id=document.pk,
            status="success",
        )

        # UNSAFE: This will fail
        logger.log_operation(
            tenant_id=firm.id,
            email_body="sensitive content",  # FORBIDDEN
        )
    """

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def log_operation(
        self,
        tenant_id: int,
        correlation_id: uuid.UUID,
        operation: str,
        status: str,
        actor: Optional[str] = None,
        object_type: Optional[str] = None,
        object_id: Optional[Any] = None,
        duration_ms: Optional[int] = None,
        error_class: Optional[str] = None,
        **extra_metadata,
    ):
        """
        Log an operation with required fields per docs/21 section 4.

        Args:
            tenant_id: Firm ID (required per docs/21 section 4)
            correlation_id: Correlation ID (required per docs/21 section 4)
            operation: Operation name (e.g., "document_upload")
            status: Operation status (success, error, etc.)
            actor: Username/actor (when applicable per docs/21 section 4)
            object_type: Type of object (e.g., "Document", "Contact")
            object_id: Primary object ID (required per docs/21 section 4)
            duration_ms: Operation duration in milliseconds
            error_class: Error classification if status=error
            **extra_metadata: Additional metadata (will be filtered for content/PII)

        Raises:
            ValueError: If forbidden content fields are in extra_metadata
        """
        # Validate no forbidden content
        self._validate_no_content(extra_metadata)

        message = f"Operation: {operation} | Status: {status}"
        if object_type and object_id:
            message += f" | Object: {object_type}#{object_id}"

        extra = {
            "tenant_id": tenant_id,
            "correlation_id": str(correlation_id),
            "operation": operation,
            "status": status,
        }

        if actor:
            extra["actor"] = actor
        if object_type:
            extra["object_type"] = object_type
        if object_id:
            extra["object_id"] = str(object_id)
        if duration_ms:
            extra["duration_ms"] = duration_ms
        if error_class:
            extra["error_class"] = error_class

        # Add filtered extra metadata
        if extra_metadata:
            extra["extra_data"] = self._filter_extras(extra_metadata)

        self._logger.info(message, extra=extra)

    def log_security_event(
        self,
        tenant_id: int,
        correlation_id: uuid.UUID,
        event_type: str,
        actor: str,
        resource_type: str,
        resource_id: str,
        action: str,
        result: str,
        **extra_metadata,
    ):
        """
        Log a security event (e.g., permission denial, break-glass).

        Per docs/21 section 3: Repeated permission denials spike should alert.
        """
        self._validate_no_content(extra_metadata)

        message = f"Security Event: {event_type} | Actor: {actor} | Action: {action} | Result: {result}"

        extra = {
            "tenant_id": tenant_id,
            "correlation_id": str(correlation_id),
            "event_type": event_type,
            "actor": actor,
            "object_type": resource_type,
            "object_id": resource_id,
            "action": action,
            "result": result,
        }

        if extra_metadata:
            extra["extra_data"] = self._filter_extras(extra_metadata)

        self._logger.warning(message, extra=extra)

    def log_error(
        self,
        tenant_id: int,
        correlation_id: uuid.UUID,
        error_type: str,
        error_message: str,
        actor: Optional[str] = None,
        object_type: Optional[str] = None,
        object_id: Optional[Any] = None,
        **extra_metadata,
    ):
        """
        Log an error with required context.

        Error messages should be redacted/generic, not contain sensitive content.
        """
        self._validate_no_content(extra_metadata)

        # Truncate error message to prevent content leakage
        safe_error_message = error_message[:500] if error_message else "Unknown error"

        extra = {
            "tenant_id": tenant_id,
            "correlation_id": str(correlation_id),
            "error_type": error_type,
        }

        if actor:
            extra["actor"] = actor
        if object_type:
            extra["object_type"] = object_type
        if object_id:
            extra["object_id"] = str(object_id)

        if extra_metadata:
            extra["extra_data"] = self._filter_extras(extra_metadata)

        self._logger.error(f"Error: {error_type} | {safe_error_message}", extra=extra)

    def _validate_no_content(self, metadata: Dict[str, Any]):
        """
        Validate that metadata doesn't contain forbidden content fields.

        Raises ValueError if forbidden fields are present.
        """
        formatter = StructuredLogFormatter()
        for key in metadata.keys():
            if any(field in key.lower() for field in formatter.FORBIDDEN_CONTENT_FIELDS):
                raise ValueError(
                    f"Forbidden content field '{key}' in log metadata. "
                    f"Per DOC-21.2: Logs must not contain content (email bodies, documents, etc.)"
                )

    def _filter_extras(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Filter extra metadata for PII and content."""
        formatter = StructuredLogFormatter()
        return formatter._filter_content(metadata)


def get_no_content_logger(name: str) -> NoContentLogger:
    """
    Get a no-content logger instance.

    Usage:
        from modules.core.structured_logging import get_no_content_logger
        logger = get_no_content_logger(__name__)
    """
    return NoContentLogger(name)


def configure_structured_logging():
    """
    Configure structured logging with JSON formatter.

    Call this during application startup to set up structured logging.
    """
    root_logger = logging.getLogger()

    # Create structured formatter
    formatter = StructuredLogFormatter()

    # Apply to all handlers
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)


# Logging validation utilities for testing
class LogValidator:
    """
    Validates that logs comply with DOC-21.2 requirements.

    Use in tests to ensure logging compliance.
    """

    @staticmethod
    def validate_log_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate a log record for DOC-21.2 compliance.

        Returns list of compliance violations (empty if compliant).
        """
        violations = []

        # Check required fields per docs/21 section 4
        # Note: tenant_id and actor may not be present in all contexts
        if "correlation_id" not in record:
            violations.append("Missing required field: correlation_id")

        # Check for forbidden content
        formatter = StructuredLogFormatter()
        for key in record.keys():
            if any(field in key.lower() for field in formatter.FORBIDDEN_CONTENT_FIELDS):
                violations.append(f"Forbidden content field present: {key}")

        # Check message for potential content leakage
        message = record.get("message", "")
        if len(message) > 1000:
            violations.append("Message too long (>1000 chars), potential content leak")

        return violations

    @staticmethod
    def is_compliant(record: Dict[str, Any]) -> bool:
        """Check if log record is DOC-21.2 compliant."""
        return len(LogValidator.validate_log_record(record)) == 0
