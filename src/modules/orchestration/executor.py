"""
Orchestration Execution Engine (DOC-11.1 per docs/11 section 3-6).

Implements:
- Idempotent execution creation
- Step execution with retry logic
- Error classification and DLQ routing
- Concurrency control

DOC-11.1: Resilient to partial failures, duplicated jobs, and concurrency.
"""

import time
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional

from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.firm.audit import AuditEvent
from modules.orchestration.models import (
    OrchestrationDefinition,
    OrchestrationDLQ,
    OrchestrationExecution,
    StepExecution,
)


class OrchestrationExecutor:
    """
    Orchestration execution engine per docs/11.

    Handles execution lifecycle, step execution, retries, and DLQ routing.
    """

    def __init__(self, firm, user=None):
        """
        Initialize executor.

        Args:
            firm: Firm context
            user: User context (for audit)
        """
        self.firm = firm
        self.user = user
        self.correlation_id = str(uuid.uuid4())

    @transaction.atomic
    def create_execution(
        self,
        definition: OrchestrationDefinition,
        target_object_type: str,
        target_object_id: int,
        input_data: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> OrchestrationExecution:
        """
        Create an orchestration execution (idempotent) per docs/11 section 6.1.

        Args:
            definition: OrchestrationDefinition to execute
            target_object_type: Type of target object
            target_object_id: ID of target object
            input_data: Input data for execution
            idempotency_key: Optional idempotency key (auto-generated if not provided)

        Returns:
            OrchestrationExecution instance

        DOC-11.1: Creating an execution MUST accept an idempotency key.
        If called multiple times with same key, returns same execution_id.
        """
        # Validate definition is published
        if definition.status != "published":
            raise ValueError("Only published definitions can be executed")

        # Generate idempotency key if not provided
        if not idempotency_key:
            idempotency_key = OrchestrationExecution.compute_idempotency_key(
                self.firm.id,
                definition.code,
                target_object_type,
                target_object_id,
            )

        # Try to create execution (idempotent)
        try:
            execution = OrchestrationExecution.objects.create(
                firm=self.firm,
                definition=definition,
                definition_version=definition.version,
                status="running",
                target_object_type=target_object_type,
                target_object_id=target_object_id,
                input_data=input_data,
                idempotency_key=idempotency_key,
                correlation_id=self.correlation_id,
                created_by=self.user,
            )

            # Audit the execution creation
            self._audit_execution_started(execution)

            return execution

        except IntegrityError:
            # Idempotency: execution already exists
            return OrchestrationExecution.objects.get(
                idempotency_key=idempotency_key
            )

    @transaction.atomic
    def execute_step(
        self,
        execution: OrchestrationExecution,
        step_def: Dict[str, Any],
    ) -> StepExecution:
        """
        Execute a single step per docs/11 section 2.2.

        Args:
            execution: OrchestrationExecution instance
            step_def: Step definition from orchestration definition

        Returns:
            StepExecution instance

        DOC-11.1: Step execution with error classification and retry logic.
        """
        step_id = step_def["step_id"]
        step_name = step_def.get("name", step_id)

        # Get or create step execution
        step_execution = self._get_or_create_step_execution(
            execution, step_id, step_name
        )

        # Check if already completed
        if step_execution.status in ["succeeded", "skipped"]:
            return step_execution

        # Update status to running
        step_execution.status = "running"
        step_execution.started_at = timezone.now()
        step_execution.save()

        try:
            # Execute the step handler
            result = self._execute_step_handler(step_def, execution, step_execution)

            # Mark as succeeded
            step_execution.status = "succeeded"
            step_execution.finished_at = timezone.now()
            step_execution.result_data = result
            step_execution.save()

            return step_execution

        except Exception as e:
            # Classify error per docs/11 section 4
            error_class = self._classify_error(e, step_def)
            error_summary = self._redact_error(str(e))

            step_execution.error_class = error_class
            step_execution.error_summary = error_summary
            step_execution.finished_at = timezone.now()

            # Determine retry behavior
            if self._should_retry(step_execution, step_def, error_class):
                # Schedule retry
                retry_delay = self._calculate_retry_delay(
                    step_execution, step_def
                )
                step_execution.status = "retrying"
                step_execution.retry_after_at = timezone.now() + retry_delay
                step_execution.save()

                # Create next attempt
                self._create_retry_attempt(execution, step_id, step_name)

            else:
                # Mark as failed
                step_execution.status = "failed"
                step_execution.save()

                # Route to DLQ if appropriate
                if error_class in [
                    "NON_RETRYABLE",
                    "COMPENSATION_REQUIRED",
                ] or step_execution.attempt_number >= step_def.get(
                    "max_attempts", 3
                ):
                    self._route_to_dlq(execution, step_execution, error_class)

            return step_execution

    def _get_or_create_step_execution(
        self, execution: OrchestrationExecution, step_id: str, step_name: str
    ) -> StepExecution:
        """
        Get or create step execution (idempotent) per docs/11 section 6.2.

        Args:
            execution: OrchestrationExecution instance
            step_id: Step ID from definition
            step_name: Human-readable step name

        Returns:
            StepExecution instance
        """
        # Try to get existing step execution for this attempt
        step_executions = StepExecution.objects.filter(
            execution=execution,
            step_id=step_id,
        ).order_by("-attempt_number")

        if step_executions.exists():
            latest = step_executions.first()
            # If latest is retrying, we may want current attempt
            if latest.status in ["pending", "retrying"]:
                return latest

        # Create new step execution
        attempt_number = step_executions.count() + 1 if step_executions.exists() else 1

        return StepExecution.objects.create(
            firm=self.firm,
            execution=execution,
            step_id=step_id,
            step_name=step_name,
            attempt_number=attempt_number,
            status="pending",
        )

    def _execute_step_handler(
        self,
        step_def: Dict[str, Any],
        execution: OrchestrationExecution,
        step_execution: StepExecution,
    ) -> Dict[str, Any]:
        """
        Execute the actual step handler logic per docs/11 section 2.2.

        Dispatches to appropriate handler based on step type.

        Args:
            step_def: Step definition
            execution: OrchestrationExecution instance
            step_execution: StepExecution instance

        Returns:
            Step result dict

        DOC-11.1: Step handlers must be idempotent and accept idempotency_key.

        Meta-commentary:
        - **Current Status:** Dispatches built-in step types and custom handlers by name.
        - **Follow-up (T-066):** Add handler registry and compensation hooks for custom steps.
        - **Assumption:** Step definitions provide valid handler names for custom types.
        - **Missing:** Handler existence validation and structured error classification.
        - **Limitation:** Custom handler resolution is string-based and untyped.
        """
        step_type = step_def.get("type", "custom")
        handler_name = step_def.get("handler")

        # Generate step-level idempotency key
        step_idempotency_key = f"{execution.idempotency_key}:step:{step_execution.step_id}:attempt:{step_execution.attempt_number}"

        # Dispatch based on step type
        if step_type == "email":
            return self._execute_email_handler(step_def, execution, step_execution, step_idempotency_key)
        elif step_type == "notification":
            return self._execute_notification_handler(step_def, execution, step_execution, step_idempotency_key)
        elif step_type == "webhook":
            return self._execute_webhook_handler(step_def, execution, step_execution, step_idempotency_key)
        elif step_type == "delay":
            return self._execute_delay_handler(step_def, execution, step_execution, step_idempotency_key)
        elif step_type == "custom" and handler_name:
            # Custom handler lookup by name
            return self._execute_custom_handler(handler_name, step_def, execution, step_execution, step_idempotency_key)
        else:
            # Default: no-op step
            return {
                "status": "completed",
                "message": f"Step {step_execution.step_name} completed (no-op)",
            }

    def _execute_email_handler(
        self,
        step_def: Dict[str, Any],
        execution: OrchestrationExecution,
        step_execution: StepExecution,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """Execute email step handler."""
        from modules.core.notifications import EmailNotification

        to = step_def.get("to", [])
        subject = step_def.get("subject", "")
        template = step_def.get("template")
        context = step_def.get("context", {})

        # Merge execution input_data into context
        context.update(execution.input_data)

        if template:
            # Use template-based email
            EmailNotification.send_template(
                to=to,
                template=template,
                context=context,
                idempotency_key=idempotency_key,
            )
        else:
            # Use direct email
            EmailNotification.send(
                to=to,
                subject=subject,
                html_content=step_def.get("html_content", ""),
                idempotency_key=idempotency_key,
            )

        return {
            "status": "completed",
            "message": f"Email sent to {len(to)} recipient(s)",
        }

    def _execute_notification_handler(
        self,
        step_def: Dict[str, Any],
        execution: OrchestrationExecution,
        step_execution: StepExecution,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """Execute notification step handler."""
        from modules.core.notifications import NotificationService

        notification_type = step_def.get("notification_type", "info")
        message = step_def.get("message", "")
        recipients = step_def.get("recipients", [])

        NotificationService.send(
            firm=self.firm,
            notification_type=notification_type,
            message=message,
            recipients=recipients,
            idempotency_key=idempotency_key,
        )

        return {
            "status": "completed",
            "message": f"Notification sent to {len(recipients)} recipient(s)",
        }

    def _execute_webhook_handler(
        self,
        step_def: Dict[str, Any],
        execution: OrchestrationExecution,
        step_execution: StepExecution,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """Execute webhook step handler."""
        import requests

        url = step_def.get("url")
        method = step_def.get("method", "POST")
        headers = step_def.get("headers", {})
        payload = step_def.get("payload", {})

        # Merge execution input_data into payload
        payload.update(execution.input_data)

        # Add idempotency key to headers
        headers["X-Idempotency-Key"] = idempotency_key

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=payload,
            timeout=step_def.get("timeout", 30),
        )

        response.raise_for_status()

        return {
            "status": "completed",
            "message": f"Webhook {method} to {url} succeeded",
            "response_status": response.status_code,
        }

    def _execute_delay_handler(
        self,
        step_def: Dict[str, Any],
        execution: OrchestrationExecution,
        step_execution: StepExecution,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """Execute delay step handler."""
        import time

        delay_seconds = step_def.get("delay_seconds", 0)

        if delay_seconds > 0:
            time.sleep(delay_seconds)

        return {
            "status": "completed",
            "message": f"Delayed for {delay_seconds} seconds",
        }

    def _execute_custom_handler(
        self,
        handler_name: str,
        step_def: Dict[str, Any],
        execution: OrchestrationExecution,
        step_execution: StepExecution,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """
        Execute custom handler by name.

        Looks up handler from registry or imports from module path.
        """
        # Try to import handler from common locations
        handler_registry = {
            # Add registered handlers here
            # "my_handler": my_handler_function,
        }

        if handler_name in handler_registry:
            handler = handler_registry[handler_name]
            return handler(
                step_def=step_def,
                execution=execution,
                step_execution=step_execution,
                idempotency_key=idempotency_key,
                firm=self.firm,
                user=self.user,
            )

        # Try to import from module path (e.g., "modules.my_module.my_handler")
        try:
            module_path, func_name = handler_name.rsplit(".", 1)
            module = __import__(module_path, fromlist=[func_name])
            handler = getattr(module, func_name)

            return handler(
                step_def=step_def,
                execution=execution,
                step_execution=step_execution,
                idempotency_key=idempotency_key,
                firm=self.firm,
                user=self.user,
            )
        except (ImportError, AttributeError, ValueError) as e:
            raise ValueError(
                f"Handler '{handler_name}' not found. "
                f"Register in handler_registry or provide valid module path. Error: {str(e)}"
            )

    def _classify_error(
        self, error: Exception, step_def: Dict[str, Any]
    ) -> str:
        """
        Classify error per docs/11 section 4.

        Args:
            error: The exception that occurred
            step_def: Step definition

        Returns:
            Error class string (TRANSIENT, RETRYABLE, etc.)

        DOC-11.1: Error classification MUST be deterministic.
        """
        # Simple classification logic (extend based on error types)
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Timeout errors
        if "timeout" in error_str or error_type in ["TimeoutError"]:
            return "TRANSIENT"

        # Rate limit errors
        if "rate limit" in error_str or "429" in error_str:
            return "RATE_LIMITED"

        # Validation errors
        if "validation" in error_str or error_type in [
            "ValidationError",
            "ValueError",
        ]:
            return "NON_RETRYABLE"

        # Permission errors
        if "permission" in error_str or "forbidden" in error_str:
            return "NON_RETRYABLE"

        # Network errors
        if (
            "connection" in error_str
            or "network" in error_str
            or error_type in ["ConnectionError", "RequestException"]
        ):
            return "TRANSIENT"

        # Default to retryable
        return "RETRYABLE"

    def _redact_error(self, error_message: str) -> str:
        """
        Redact sensitive information from error message per docs/21 section 4.

        Redacts common PII patterns:
        - Email addresses
        - Phone numbers
        - SSN/EIN
        - Credit card numbers
        - API keys/tokens

        Args:
            error_message: Raw error message

        Returns:
            Redacted error summary
        """
        import re

        # Truncate to prevent unbounded storage
        max_length = 1000
        if len(error_message) > max_length:
            error_message = error_message[:max_length] + "... (truncated)"

        # Redact email addresses
        error_message = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL_REDACTED]',
            error_message
        )

        # Redact phone numbers (various formats)
        error_message = re.sub(
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            '[PHONE_REDACTED]',
            error_message
        )

        # Redact SSN/EIN patterns
        error_message = re.sub(
            r'\b\d{3}-\d{2}-\d{4}\b',
            '[SSN_REDACTED]',
            error_message
        )

        # Redact credit card numbers (13-16 digits)
        error_message = re.sub(
            r'\b\d{13,16}\b',
            '[CARD_REDACTED]',
            error_message
        )

        # Redact common API key patterns
        error_message = re.sub(
            r'(api[_-]?key|token|secret|password)[\s:=]+[\'"]?[\w\-\.]+[\'"]?',
            r'\1=[REDACTED]',
            error_message,
            flags=re.IGNORECASE
        )

        # Redact AWS-style keys
        error_message = re.sub(
            r'AKIA[0-9A-Z]{16}',
            '[AWS_KEY_REDACTED]',
            error_message
        )

        return error_message

    def _should_retry(
        self,
        step_execution: StepExecution,
        step_def: Dict[str, Any],
        error_class: str,
    ) -> bool:
        """
        Determine if step should be retried per docs/11 section 5.

        Args:
            step_execution: StepExecution instance
            step_def: Step definition
            error_class: Classified error type

        Returns:
            True if should retry, False otherwise

        DOC-11.1: Retry matrix determines retry behavior.
        """
        # Check max attempts
        max_attempts = step_def.get("max_attempts", 3)
        if step_execution.attempt_number >= max_attempts:
            return False

        # Check error class retry policy per docs/11 section 5.2
        retry_on_classes = step_def.get("retry_on_classes", [
            "TRANSIENT",
            "RETRYABLE",
            "RATE_LIMITED",
            "DEPENDENCY_FAILED",
        ])

        return error_class in retry_on_classes

    def _calculate_retry_delay(
        self, step_execution: StepExecution, step_def: Dict[str, Any]
    ) -> timedelta:
        """
        Calculate retry delay per docs/11 section 5.1.

        Args:
            step_execution: StepExecution instance
            step_def: Step definition

        Returns:
            Retry delay timedelta

        DOC-11.1: Supports fixed, exponential, jittered backoff.
        """
        backoff_strategy = step_def.get("backoff_strategy", "exponential")
        initial_delay_ms = step_def.get("initial_delay_ms", 1000)
        max_delay_ms = step_def.get("max_delay_ms", 60000)

        if backoff_strategy == "fixed":
            delay_ms = initial_delay_ms
        elif backoff_strategy == "exponential":
            delay_ms = initial_delay_ms * (2 ** (step_execution.attempt_number - 1))
        elif backoff_strategy == "jittered":
            import random

            base_delay = initial_delay_ms * (2 ** (step_execution.attempt_number - 1))
            delay_ms = base_delay * (0.5 + random.random() * 0.5)
        else:
            delay_ms = initial_delay_ms

        # Cap at max delay
        delay_ms = min(delay_ms, max_delay_ms)

        return timedelta(milliseconds=delay_ms)

    def _create_retry_attempt(
        self, execution: OrchestrationExecution, step_id: str, step_name: str
    ) -> None:
        """
        Create a new retry attempt for a step.

        Args:
            execution: OrchestrationExecution instance
            step_id: Step ID
            step_name: Step name
        """
        # The next get_or_create_step_execution call will create the new attempt
        pass

    def _route_to_dlq(
        self,
        execution: OrchestrationExecution,
        step_execution: StepExecution,
        error_class: str,
    ) -> None:
        """
        Route failed step to DLQ per docs/11 section 5.2.

        Args:
            execution: OrchestrationExecution instance
            step_execution: StepExecution instance
            error_class: Error classification

        DOC-11.1: Steps that exceed max attempts or hit NON_RETRYABLE
        MUST be routed to DLQ.
        """
        # Determine DLQ reason
        if step_execution.attempt_number >= 3:  # Default max attempts
            reason = "max_retries_exceeded"
        elif error_class == "NON_RETRYABLE":
            reason = "non_retryable_error"
        elif error_class == "COMPENSATION_REQUIRED":
            reason = "compensation_required"
        else:
            reason = "timeout_exceeded"

        OrchestrationDLQ.objects.create(
            firm=self.firm,
            step_execution=step_execution,
            execution=execution,
            reason=reason,
            error_class=error_class,
            error_summary=step_execution.error_summary,
        )

    def _audit_execution_started(
        self, execution: OrchestrationExecution
    ) -> None:
        """
        Audit execution start per docs/11 section 10.

        Args:
            execution: OrchestrationExecution instance
        """
        AuditEvent.objects.create(
            firm=self.firm,
            category=AuditEvent.CATEGORY_SYSTEM,
            action="orchestration_execution_started",
            severity=AuditEvent.SEVERITY_INFO,
            actor_user=self.user,
            resource_type="OrchestrationExecution",
            resource_id=str(execution.id),
            metadata={
                "definition_code": execution.definition.code,
                "definition_version": execution.definition_version,
                "target_type": execution.target_object_type,
                "target_id": execution.target_object_id,
                "correlation_id": self.correlation_id,
                "idempotency_key": execution.idempotency_key,
            },
        )
