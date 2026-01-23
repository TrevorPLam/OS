"""
Email Ingestion Retry Service.

Implements DOC-15.2: retry-safety with exponential backoff, error classification,
and replay tooling for failed ingestion attempts.

Complies with docs/03-reference/requirements/DOC-15.md section 2.3.
"""

import time
import random
from datetime import timedelta
from typing import List, Optional
from django.db import transaction
from django.utils import timezone

from modules.firm.audit import AuditEvent
from .models import IngestionAttempt, EmailConnection


class ErrorClassifier:
    """
    Classifies errors for retry logic.

    Implements error classification similar to orchestration engine (docs/03-reference/requirements/DOC-11.md).
    """

    @staticmethod
    def classify_error(error: Exception) -> str:
        """
        Classify an error into retry categories.

        Returns:
            error_class: transient | retryable | non_retryable | rate_limited

        Meta-commentary:
        - **Current Status:** Heuristic classification based on exception types and messages.
        - **Follow-up (T-066):** Add provider-specific mappings and structured error codes.
        - **Assumption:** Error messages include reliable rate-limit keywords.
        - **Missing:** Metrics to validate classification accuracy over time.
        - **Limitation:** String matching is brittle across providers and SDK versions.
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # Network/timeout errors - TRANSIENT
        if error_type in [
            "ConnectionError",
            "Timeout",
            "TimeoutError",
            "ConnectionResetError",
            "BrokenPipeError",
        ]:
            return "transient"

        # Rate limiting - RATE_LIMITED
        if error_type in ["HttpError", "APIError"]:
            if any(keyword in error_msg for keyword in ["rate limit", "quota", "429", "too many"]):
                return "rate_limited"

        # Database errors - RETRYABLE
        if error_type in [
            "OperationalError",
            "DatabaseError",
            "IntegrityError",
        ]:
            # Deadlock/lock timeout is retryable
            if any(keyword in error_msg for keyword in ["deadlock", "lock timeout"]):
                return "retryable"
            # Unique constraint violation is non-retryable (duplicate)
            if "unique" in error_msg or "duplicate" in error_msg:
                return "non_retryable"
            return "retryable"

        # Authentication/permission errors - NON_RETRYABLE
        if error_type in ["PermissionDenied", "Forbidden", "Unauthorized"]:
            return "non_retryable"

        # Validation errors - NON_RETRYABLE
        if error_type in ["ValidationError", "ValueError", "TypeError"]:
            return "non_retryable"

        # Provider-specific errors
        if "gmail" in error_msg or "google" in error_msg:
            if "not found" in error_msg:
                return "non_retryable"
            if "invalid" in error_msg:
                return "non_retryable"

        if "outlook" in error_msg or "microsoft" in error_msg:
            if "not found" in error_msg:
                return "non_retryable"
            if "invalid" in error_msg:
                return "non_retryable"

        # Default: retryable with backoff
        return "retryable"


class RetryStrategy:
    """
    Retry strategy with exponential backoff and jitter.

    Implements retry logic per DOC-15.2.
    """

    # Retry configuration
    MAX_RETRIES = 5
    BASE_DELAY_SECONDS = 2  # Start with 2 seconds
    MAX_DELAY_SECONDS = 300  # Cap at 5 minutes
    JITTER_FACTOR = 0.1  # 10% jitter

    @classmethod
    def calculate_next_retry(cls, retry_count: int, error_class: str) -> Optional[timedelta]:
        """
        Calculate delay until next retry based on error class and retry count.

        Returns:
            timedelta for next retry, or None if should not retry.
        """
        # Non-retryable errors: never retry
        if error_class == "non_retryable":
            return None

        # Max retries exceeded
        if retry_count >= cls.MAX_RETRIES:
            return None

        # Calculate base delay with exponential backoff
        if error_class == "transient":
            # Transient errors: faster retry (1s, 2s, 4s, 8s, 16s)
            delay = min(2 ** retry_count, cls.MAX_DELAY_SECONDS)
        elif error_class == "rate_limited":
            # Rate limited: slower backoff (60s, 120s, 240s, ...)
            delay = min(60 * (2 ** retry_count), cls.MAX_DELAY_SECONDS)
        else:
            # Retryable: standard backoff (2s, 4s, 8s, 16s, 32s)
            delay = min(cls.BASE_DELAY_SECONDS * (2 ** retry_count), cls.MAX_DELAY_SECONDS)

        # Add jitter to avoid thundering herd
        jitter = delay * cls.JITTER_FACTOR * random.uniform(-1, 1)
        delay_with_jitter = max(1, delay + jitter)

        return timedelta(seconds=delay_with_jitter)

    @classmethod
    def should_retry(cls, retry_count: int, error_class: str) -> bool:
        """Return True if should retry based on error class and count."""
        return cls.calculate_next_retry(retry_count, error_class) is not None


class IngestionRetryService:
    """
    Service for retrying failed ingestion attempts.

    Implements DOC-15.2: replay of failed attempts with audit trail.
    """

    def __init__(self):
        self.error_classifier = ErrorClassifier()
        self.retry_strategy = RetryStrategy()

    def get_failed_attempts_for_retry(
        self, firm_id: Optional[int] = None, connection_id: Optional[int] = None
    ) -> List[IngestionAttempt]:
        """
        Get failed attempts eligible for retry.

        Returns attempts where:
        - status = fail
        - max_retries_reached = False
        - next_retry_at is None or past
        - error_class is not non_retryable
        """
        queryset = IngestionAttempt.objects.filter(
            status="fail",
            max_retries_reached=False,
        ).exclude(error_class="non_retryable")

        if firm_id:
            queryset = queryset.filter(firm_id=firm_id)

        if connection_id:
            queryset = queryset.filter(connection_id=connection_id)

        # Filter by next_retry_at
        now = timezone.now()
        queryset = queryset.filter(
            models.Q(next_retry_at__isnull=True) | models.Q(next_retry_at__lte=now)
        )

        return list(queryset.order_by("occurred_at"))

    @transaction.atomic
    def record_retry_attempt(
        self,
        original_attempt: IngestionAttempt,
        error: Exception,
        user=None,
    ) -> IngestionAttempt:
        """
        Record a retry attempt for a failed ingestion.

        Creates a new IngestionAttempt with incremented retry_count,
        classifies the error, and schedules next retry if applicable.

        Args:
            original_attempt: The original failed attempt
            error: The error that occurred on retry
            user: User who initiated the retry (for audit)

        Returns:
            New IngestionAttempt record
        """
        error_class = self.error_classifier.classify_error(error)
        retry_count = original_attempt.retry_count + 1

        # Calculate next retry time
        next_retry_delay = self.retry_strategy.calculate_next_retry(retry_count, error_class)
        next_retry_at = timezone.now() + next_retry_delay if next_retry_delay else None
        max_retries_reached = not self.retry_strategy.should_retry(retry_count, error_class)

        # Create new attempt record
        new_attempt = IngestionAttempt.objects.create(
            firm=original_attempt.firm,
            connection=original_attempt.connection,
            email_artifact=original_attempt.email_artifact,
            operation=original_attempt.operation,
            status="fail",
            error_summary=f"Retry {retry_count}: {type(error).__name__}",
            error_class=error_class,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            max_retries_reached=max_retries_reached,
            correlation_id=original_attempt.correlation_id,
        )

        # Audit event for retry
        AuditEvent.objects.create(
            firm=original_attempt.firm,
            event_category="integration",
            event_type="email_ingestion_retry",
            actor_user=user,
            resource_type="IngestionAttempt",
            resource_id=str(new_attempt.attempt_id),
            severity="warning" if not max_retries_reached else "error",
            metadata={
                "original_attempt_id": original_attempt.attempt_id,
                "retry_count": retry_count,
                "error_class": error_class,
                "max_retries_reached": max_retries_reached,
                "next_retry_at": next_retry_at.isoformat() if next_retry_at else None,
                "connection_id": original_attempt.connection_id,
                "operation": original_attempt.operation,
            },
        )

        return new_attempt

    @transaction.atomic
    def manual_retry(
        self,
        attempt: IngestionAttempt,
        user,
    ) -> dict:
        """
        Manually retry a failed ingestion attempt (admin-gated).

        Implements DOC-15.2: admin retry tooling with audit trail.

        Args:
            attempt: The failed attempt to retry
            user: Staff user initiating the retry

        Returns:
            dict with retry result
        """
        # Audit the manual retry request
        AuditEvent.objects.create(
            firm=attempt.firm,
            event_category="integration",
            event_type="email_ingestion_manual_retry_requested",
            actor_user=user,
            resource_type="IngestionAttempt",
            resource_id=str(attempt.attempt_id),
            metadata={
                "attempt_id": attempt.attempt_id,
                "connection_id": attempt.connection_id,
                "operation": attempt.operation,
                "original_error": attempt.error_summary,
            },
        )

        # Import here to avoid circular dependency
        from .services import EmailIngestionService

        service = EmailIngestionService()

        try:
            # Retry the operation based on type
            if attempt.operation == "fetch":
                # For fetch failures, would need to re-fetch from provider
                # This requires provider-specific logic
                return {
                    "success": False,
                    "error": "Manual retry for fetch operations requires provider-specific implementation",
                }

            elif attempt.operation == "map":
                # Retry mapping for the email artifact
                if not attempt.email_artifact:
                    return {"success": False, "error": "No email artifact to remap"}

                email = attempt.email_artifact
                account, engagement, work_item, confidence, reasons = service.mapping_service.suggest_mapping(
                    email
                )

                # Update email with new mapping suggestions
                email.suggested_account = account
                email.suggested_engagement = engagement
                email.suggested_work_item = work_item
                email.mapping_confidence = confidence
                email.mapping_reasons = reasons
                email.save()

                # Log successful retry
                IngestionAttempt.objects.create(
                    firm=attempt.firm,
                    connection=attempt.connection,
                    email_artifact=email,
                    operation="map",
                    status="success",
                    correlation_id=attempt.correlation_id,
                    retry_count=attempt.retry_count + 1,
                )

                # Audit success
                AuditEvent.objects.create(
                    firm=attempt.firm,
                    event_category="integration",
                    event_type="email_ingestion_manual_retry_success",
                    actor_user=user,
                    resource_type="IngestionAttempt",
                    resource_id=str(attempt.attempt_id),
                    metadata={
                        "attempt_id": attempt.attempt_id,
                        "operation": attempt.operation,
                        "new_confidence": str(confidence),
                    },
                )

                return {
                    "success": True,
                    "email_artifact_id": email.email_artifact_id,
                    "confidence": confidence,
                    "reasons": reasons,
                }

            else:
                return {
                    "success": False,
                    "error": f"Retry not implemented for operation: {attempt.operation}",
                }

        except Exception as e:
            # Record retry failure
            self.record_retry_attempt(attempt, e, user)

            # Audit failure
            AuditEvent.objects.create(
                firm=attempt.firm,
                event_category="integration",
                event_type="email_ingestion_manual_retry_failed",
                actor_user=user,
                resource_type="IngestionAttempt",
                resource_id=str(attempt.attempt_id),
                severity="error",
                metadata={
                    "attempt_id": attempt.attempt_id,
                    "operation": attempt.operation,
                    "error": type(e).__name__,
                },
            )

            return {"success": False, "error": str(e)}

    def get_retry_statistics(self, connection: EmailConnection) -> dict:
        """
        Get retry statistics for a connection.

        Returns:
            dict with retry metrics
        """
        attempts = IngestionAttempt.objects.filter(connection=connection, status="fail")

        total_failures = attempts.count()
        max_retries_reached = attempts.filter(max_retries_reached=True).count()
        pending_retry = attempts.filter(
            max_retries_reached=False, next_retry_at__gt=timezone.now()
        ).count()
        eligible_for_retry = len(self.get_failed_attempts_for_retry(connection_id=connection.pk))

        error_breakdown = {}
        for error_class in ["transient", "retryable", "non_retryable", "rate_limited"]:
            error_breakdown[error_class] = attempts.filter(error_class=error_class).count()

        return {
            "total_failures": total_failures,
            "max_retries_reached": max_retries_reached,
            "pending_retry": pending_retry,
            "eligible_for_retry": eligible_for_retry,
            "error_breakdown": error_breakdown,
        }


# Import models.Q for queryset filtering
from django.db import models
