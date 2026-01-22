"""
Job Payload Validation Utilities.

Implements DOC-20.1: Payload rules per docs/03-reference/requirements/DOC-20.md section 2.
"""

from typing import Dict, List, Optional
import uuid


class PayloadValidator:
    """
    Validates job payloads per docs/03-reference/requirements/DOC-20.md section 2.

    Payload rules (MUST):
    1. Minimal and avoid embedding sensitive content
    2. Include: tenant_id, correlation_id, idempotency_key, primary object refs
    3. Versioned if structure may evolve
    """

    REQUIRED_FIELDS = ["tenant_id", "correlation_id", "idempotency_key"]

    @classmethod
    def validate_payload(
        cls,
        payload: Dict,
        category: str,
        additional_required: Optional[List[str]] = None,
    ) -> tuple[bool, List[str]]:
        """
        Validate a job payload.

        Args:
            payload: Payload dictionary to validate
            category: Job category (for category-specific validation)
            additional_required: Additional required fields beyond standard set

        Returns:
            (is_valid, errors)
        """
        errors = []

        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in payload:
                errors.append(f"Missing required field: {field}")

        # Validate field types
        if "tenant_id" in payload and not isinstance(payload["tenant_id"], int):
            errors.append("tenant_id must be an integer")

        if "correlation_id" in payload:
            try:
                uuid.UUID(str(payload["correlation_id"]))
            except (ValueError, AttributeError):
                errors.append("correlation_id must be a valid UUID")

        if "idempotency_key" in payload and not isinstance(payload["idempotency_key"], str):
            errors.append("idempotency_key must be a string")

        # Check additional required fields
        if additional_required:
            for field in additional_required:
                if field not in payload:
                    errors.append(f"Missing category-specific field: {field}")

        # Category-specific validation
        errors.extend(cls._validate_category_specific(payload, category))

        # Check for sensitive content (basic check)
        errors.extend(cls._check_sensitive_content(payload))

        return len(errors) == 0, errors

    @classmethod
    def _validate_category_specific(cls, payload: Dict, category: str) -> List[str]:
        """Validate category-specific payload requirements."""
        errors = []

        if category == "ingestion":
            # Ingestion: connection_id, external_message_id
            if "connection_id" not in payload:
                errors.append("Ingestion jobs require connection_id")

        elif category == "sync":
            # Sync: connection_id, appointment_id or operation
            if "connection_id" not in payload:
                errors.append("Sync jobs require connection_id")

        elif category == "recurrence":
            # Recurrence: recurrence_rule_id, period_key
            if "recurrence_rule_id" not in payload:
                errors.append("Recurrence jobs require recurrence_rule_id")

        elif category == "orchestration":
            # Orchestration: orchestration_execution_id, step_id
            if "orchestration_execution_id" not in payload:
                errors.append("Orchestration jobs require orchestration_execution_id")

        elif category == "documents":
            # Documents: document_id, version_id
            if "document_id" not in payload:
                errors.append("Document jobs require document_id")

        elif category == "notifications":
            # Notifications: recipient_id, notification_type
            if "recipient_id" not in payload and "recipient_ids" not in payload:
                errors.append("Notification jobs require recipient_id or recipient_ids")

        return errors

    @classmethod
    def _check_sensitive_content(cls, payload: Dict) -> List[str]:
        """
        Check for sensitive content in payload per docs/03-reference/requirements/DOC-20.md section 2.

        Payloads should be minimal and avoid embedding sensitive content.
        """
        errors = []

        # Check for common sensitive field names
        sensitive_keys = [
            "password",
            "secret",
            "token",
            "api_key",
            "private_key",
            "ssn",
            "credit_card",
            "email_body",
            "document_content",
            "message_body",
        ]

        for key in sensitive_keys:
            if key in payload:
                errors.append(
                    f"Payload contains potentially sensitive field '{key}' - "
                    f"payloads should be minimal and reference IDs, not embed content"
                )

        # Check payload size (warn if > 10KB)
        import json
        payload_size = len(json.dumps(payload).encode())
        if payload_size > 10240:  # 10KB
            errors.append(
                f"Payload size ({payload_size} bytes) exceeds recommended 10KB limit - "
                f"payloads should be minimal and avoid embedding content"
            )

        return errors

    @classmethod
    def create_payload(
        cls,
        tenant_id: int,
        correlation_id: uuid.UUID,
        idempotency_key: str,
        **kwargs,
    ) -> Dict:
        """
        Create a validated payload with required fields.

        Args:
            tenant_id: Firm ID for tenant isolation
            correlation_id: Correlation ID for tracing
            idempotency_key: Unique key for at-most-once processing
            **kwargs: Additional payload fields

        Returns:
            Validated payload dictionary
        """
        payload = {
            "tenant_id": tenant_id,
            "correlation_id": str(correlation_id),
            "idempotency_key": idempotency_key,
            **kwargs,
        }

        return payload
