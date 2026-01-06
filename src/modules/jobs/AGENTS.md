# AGENTS.md — Jobs Module (Background Queue & DLQ)

Last Updated: 2026-01-06
Applies To: `src/modules/jobs/`

## Purpose

Background job queue with dead letter queue (DLQ), concurrency locks, and category-based processing.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | JobQueue, DeadLetterQueue, ConcurrencyLock (~484 LOC) |
| `queue.py` | Job queue operations |
| `jobs.py` | Job definitions |
| `payload_validator.py` | Payload schema validation |
| `admin_views.py` | Admin job management |

## Domain Model

```
JobQueue (pending/processing jobs)
    └── DeadLetterQueue (failed jobs for review)

ConcurrencyLock (prevents duplicate execution)
```

## Key Models

### JobQueue

Background job record:

```python
class JobQueue(models.Model):
    job_id: UUID                      # Primary key
    firm: FK[Firm]                    # Tenant isolation
    
    # Classification
    category: str                     # ingestion, sync, recurrence, etc.
    job_type: str                     # Specific job (e.g., "email_fetch")
    
    # Payload
    payload_version: str              # Schema version
    payload: JSONField                # Job-specific data
    
    # Status
    status: str                       # pending, processing, completed, failed, dlq
    priority: int                     # 0=critical, 1=high, 2=normal, 3=low
    
    # Retry tracking
    attempts: int
    max_attempts: int
    last_error: str
    
    # Timing
    scheduled_at: DateTime
    started_at: DateTime
    completed_at: DateTime
    
    # Concurrency
    lock_key: str                     # For deduplication
```

### DeadLetterQueue

Jobs that exhausted retries:

```python
class DeadLetterQueue(models.Model):
    original_job: FK[JobQueue]
    
    moved_at: DateTime
    reason: str
    
    # For manual review
    reviewed_by: FK[User]
    reviewed_at: DateTime
    resolution: str                   # reprocessed, discarded, escalated
```

### ConcurrencyLock

Prevents duplicate execution:

```python
class ConcurrencyLock(models.Model):
    lock_key: str                     # Unique identifier
    acquired_at: DateTime
    expires_at: DateTime
    holder_id: str                    # Worker ID
```

## Job Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `ingestion` | External data import | email_fetch, calendar_sync |
| `sync` | Bi-directional sync | google_calendar_push |
| `recurrence` | Recurring generation | work_item_generation |
| `orchestration` | Workflow steps | step_execution |
| `documents` | Document processing | malware_scan, ocr |
| `notifications` | Message sending | email_send, sms_send |
| `export` | Data export | firm_export, gdpr_export |
| `maintenance` | Cleanup tasks | archive_old_logs |

## Payload Rules

Per `payload_validator.py`:

```python
# REQUIRED fields in every payload
{
    "tenant_id": 123,                 # Firm ID (REQUIRED)
    "version": "1.0",                 # Payload version
    "correlation_id": "uuid",         # For tracing
    # ... job-specific fields
}
```

## Job Lifecycle

```
1. Job created (status=pending)
2. Worker picks up (status=processing)
3. Worker acquires ConcurrencyLock
4. Job executes
5. On success:
   - status=completed
   - Lock released
6. On failure:
   - attempts++
   - If attempts < max_attempts: status=pending (retry)
   - If attempts >= max_attempts: status=dlq
```

## Retry Policy

```python
# Default retry policy
{
    "max_attempts": 3,
    "backoff": "exponential",
    "base_delay_seconds": 60,
    "max_delay_seconds": 3600,
}

# Delay calculation
# Attempt 1: 60s
# Attempt 2: 120s
# Attempt 3: 240s (capped at max_delay)
```

## Concurrency Locking

Prevents duplicate execution:

```python
from modules.jobs.queue import acquire_lock, release_lock

# Before processing
lock = acquire_lock(
    key=f"email-fetch-{connection.id}",
    ttl_seconds=300,  # Auto-release after 5 min
)

if not lock:
    # Another worker is processing
    return

try:
    # Do work
    process_job()
finally:
    release_lock(lock)
```

## DLQ Processing

Jobs in DLQ require manual review:

```python
# Admin reviews DLQ
dlq_item = DeadLetterQueue.objects.get(id=dlq_id)

# Options:
# 1. Reprocess (fix underlying issue first)
dlq_item.reprocess()

# 2. Discard (data no longer relevant)
dlq_item.discard(reason="Duplicate data")

# 3. Escalate (needs developer attention)
dlq_item.escalate(reason="Unknown error pattern")
```

## Dependencies

- **Depends on**: `firm/`
- **Used by**: All modules that need background processing
- **Related**: `orchestration/` (step execution uses jobs)

## URLs

Admin endpoints (`/api/v1/jobs/admin/`):

```
GET        /queues/                   # Queue stats by category
GET        /jobs/                     # List jobs (filterable)
GET        /jobs/{id}/                # Job detail
POST       /jobs/{id}/retry/          # Manual retry

GET        /dlq/                      # DLQ items
GET        /dlq/{id}/                 # DLQ item detail
POST       /dlq/{id}/reprocess/
POST       /dlq/{id}/discard/
```
