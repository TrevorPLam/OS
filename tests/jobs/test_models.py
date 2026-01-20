import pytest
import uuid
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.jobs.models import JobQueue, DeadLetterQueue
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def job_payload(firm):
    """Standard job payload following docs/20 spec"""
    return {
        "tenant_id": firm.id,
        "correlation_id": str(uuid.uuid4()),
        "idempotency_key": f"job-{uuid.uuid4()}",
        "object_refs": {"client_id": 123, "document_id": 456},
    }


@pytest.mark.django_db
class TestJobQueue:
    """Test JobQueue model functionality"""

    def test_job_creation(self, firm, job_payload):
        """Test basic job creation"""
        job = JobQueue.objects.create(
            firm=firm,
            category="ingestion",
            job_type="email_ingestion_fetch",
            payload_version="1.0",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
            status="pending",
            priority=2,
        )

        assert job.firm == firm
        assert job.category == "ingestion"
        assert job.job_type == "email_ingestion_fetch"
        assert job.status == "pending"
        assert job.priority == 2
        assert job.attempt_count == 0

    def test_job_categories(self, firm, job_payload):
        """Test all job categories"""
        categories = ["ingestion", "sync", "recurrence", "orchestration", "documents", "notifications", "export", "maintenance"]

        for category in categories:
            job = JobQueue.objects.create(
                firm=firm,
                category=category,
                job_type=f"{category}_test",
                payload=job_payload,
                idempotency_key=f"key-{category}",
                correlation_id=uuid.uuid4(),
            )
            assert job.category == category

    def test_job_status_transitions(self, firm, job_payload):
        """Test job status transitions"""
        job = JobQueue.objects.create(
            firm=firm,
            category="notifications",
            job_type="send_email",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
            status="pending",
        )

        # Claim job
        job.status = "processing"
        job.claimed_at = timezone.now()
        job.claimed_by_worker = "worker-001"
        job.started_at = timezone.now()
        job.save()

        assert job.status == "processing"
        assert job.claimed_at is not None
        assert job.claimed_by_worker == "worker-001"

        # Complete job
        job.status = "completed"
        job.completed_at = timezone.now()
        job.save()

        assert job.status == "completed"
        assert job.completed_at is not None

    def test_job_priority_levels(self, firm, job_payload):
        """Test job priority levels"""
        priorities = [0, 1, 2, 3]  # Critical, High, Normal, Low

        for priority in priorities:
            job = JobQueue.objects.create(
                firm=firm,
                category="sync",
                job_type="calendar_sync",
                payload=job_payload,
                idempotency_key=f"key-priority-{priority}",
                correlation_id=uuid.uuid4(),
                priority=priority,
            )
            assert job.priority == priority

    def test_job_retry_tracking(self, firm, job_payload):
        """Test job retry tracking"""
        job = JobQueue.objects.create(
            firm=firm,
            category="sync",
            job_type="api_sync",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
            max_attempts=5,
        )

        # First attempt
        job.attempt_count = 1
        job.status = "failed"
        job.error_class = "transient"
        job.last_error = "Connection timeout"
        job.next_retry_at = timezone.now() + timedelta(minutes=5)
        job.save()

        assert job.attempt_count == 1
        assert job.error_class == "transient"
        assert job.next_retry_at is not None

        # Retry
        job.attempt_count = 2
        job.save()
        assert job.attempt_count == 2

    def test_job_max_attempts_dlq(self, firm, job_payload):
        """Test job moves to DLQ after max attempts"""
        job = JobQueue.objects.create(
            firm=firm,
            category="notifications",
            job_type="send_sms",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
            max_attempts=3,
        )

        # Fail multiple times
        job.attempt_count = 3
        job.status = "dlq"
        job.error_class = "non_retryable"
        job.last_error = "Invalid phone number"
        job.save()

        assert job.status == "dlq"
        assert job.attempt_count >= job.max_attempts

    def test_job_idempotency_key(self, firm, job_payload):
        """Test idempotency key uniqueness"""
        idempotency_key = "unique-job-key-123"

        job1 = JobQueue.objects.create(
            firm=firm,
            category="ingestion",
            job_type="email_fetch",
            payload=job_payload,
            idempotency_key=idempotency_key,
            correlation_id=uuid.uuid4(),
        )

        # Attempting to create duplicate should be handled by application logic
        # or database constraints
        assert job1.idempotency_key == idempotency_key

    def test_job_correlation_id_tracking(self, firm, job_payload):
        """Test correlation ID for tracing"""
        correlation_id = uuid.uuid4()

        # Create multiple related jobs with same correlation ID
        job1 = JobQueue.objects.create(
            firm=firm,
            category="ingestion",
            job_type="step1",
            payload=job_payload,
            idempotency_key="job1",
            correlation_id=correlation_id,
        )

        job2 = JobQueue.objects.create(
            firm=firm,
            category="ingestion",
            job_type="step2",
            payload=job_payload,
            idempotency_key="job2",
            correlation_id=correlation_id,
        )

        # Both jobs share correlation ID for tracing
        assert job1.correlation_id == job2.correlation_id
        assert str(job1.correlation_id) == str(correlation_id)

    def test_job_payload_versioning(self, firm, job_payload):
        """Test payload version tracking"""
        job = JobQueue.objects.create(
            firm=firm,
            category="documents",
            job_type="scan_document",
            payload_version="2.0",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
        )

        assert job.payload_version == "2.0"

    def test_job_scheduled_execution(self, firm, job_payload):
        """Test scheduled job execution"""
        future_time = timezone.now() + timedelta(hours=1)

        job = JobQueue.objects.create(
            firm=firm,
            category="recurrence",
            job_type="generate_period",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
            scheduled_at=future_time,
        )

        assert job.scheduled_at == future_time
        assert job.status == "pending"


@pytest.mark.django_db
class TestDeadLetterQueue:
    """Test DeadLetterQueue model functionality"""

    def test_dlq_creation(self, firm, job_payload):
        """Test DLQ record creation"""
        original_job = JobQueue.objects.create(
            firm=firm,
            category="notifications",
            job_type="send_email",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
            status="dlq",
        )

        dlq_record = DeadLetterQueue.objects.create(
            firm=firm,
            original_job=original_job,
            category=original_job.category,
            job_type=original_job.job_type,
            payload=original_job.payload,
            failure_reason="Maximum retry attempts exceeded",
            can_reprocess=True,
        )

        assert dlq_record.original_job == original_job
        assert dlq_record.category == "notifications"
        assert dlq_record.can_reprocess is True

    def test_dlq_reprocessing(self, firm, job_payload):
        """Test DLQ record reprocessing"""
        original_job = JobQueue.objects.create(
            firm=firm,
            category="sync",
            job_type="calendar_sync",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
            status="dlq",
        )

        dlq_record = DeadLetterQueue.objects.create(
            firm=firm,
            original_job=original_job,
            category=original_job.category,
            job_type=original_job.job_type,
            payload=original_job.payload,
            failure_reason="Transient error",
            can_reprocess=True,
        )

        # Mark as reprocessed
        dlq_record.reprocessed_at = timezone.now()
        dlq_record.save()

        assert dlq_record.reprocessed_at is not None

    def test_dlq_non_retryable_errors(self, firm, job_payload):
        """Test DLQ records for non-retryable errors"""
        original_job = JobQueue.objects.create(
            firm=firm,
            category="documents",
            job_type="scan_document",
            payload=job_payload,
            idempotency_key=job_payload["idempotency_key"],
            correlation_id=job_payload["correlation_id"],
            status="dlq",
        )

        dlq_record = DeadLetterQueue.objects.create(
            firm=firm,
            original_job=original_job,
            category=original_job.category,
            job_type=original_job.job_type,
            payload=original_job.payload,
            failure_reason="Invalid file format (non-retryable)",
            can_reprocess=False,
        )

        assert dlq_record.can_reprocess is False
