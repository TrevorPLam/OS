# No-Content Logging & PII Minimization (DOC-21.2)

**Status:** ✅ Complete
**Last Updated:** December 30, 2025
**Complies with:** docs/21 OBSERVABILITY_AND_SRE section 4

---

## Overview

This document describes the implementation of DOC-21.2: No-content logging guarantees + PII minimization in telemetry.

The implementation enforces:
1. **Required fields** in all logs: tenant_id, correlation_id, actor, primary object ids
2. **No-content logging**: Never log email bodies, document content, message bodies
3. **PII minimization**: Mask/redact R-PII and HR data per docs/7

---

## 1. Log Requirements (docs/21 section 4)

### 1.1 Required Fields

Per docs/21 section 4, logs MUST include:

| Field | Required | When | Purpose |
|-------|----------|------|---------|
| `tenant_id` | When applicable | All tenant-scoped operations | Tenant isolation |
| `correlation_id` | Always | All operations | Tracing across systems |
| `actor` | When applicable | User-initiated operations | Accountability |
| `object_type` | When applicable | Entity operations | Context |
| `object_id` | When applicable | Entity operations | Primary key reference |

### 1.2 Forbidden Content Fields

The following fields **MUST NEVER** appear in logs:

- `body`, `content`
- `email_body`, `message_body`
- `document_content`, `file_content`
- `raw_data`, `payload_content`
- `full_text`, `html_content`, `text_content`
- `attachment_data`

**Rationale:** These fields contain user/customer content and violate no-content logging guarantees.

### 1.3 PII Fields (Minimized)

The following fields should be **masked/redacted** per docs/7:

**R-PII (Restricted PII):**
- `email`, `phone`, `address`
- Names (contact names, user names)

**HR (Highly Restricted):**
- `ssn`, `tax_id`, `credit_card`
- `password`, `secret`, `token`, `api_key`

---

## 2. Implementation

### 2.1 Structured Logging

**StructuredLogFormatter** (JSON formatter):
- Enforces required fields (tenant_id, correlation_id, actor, object_id)
- Filters forbidden content fields
- Masks PII fields
- Outputs JSON for structured log aggregation

**Implementation:** `src/modules/core/structured_logging.py::StructuredLogFormatter`

### 2.2 NoContentLogger

**NoContentLogger** enforces no-content guarantees:

```python
from modules.core.structured_logging import get_no_content_logger

logger = get_no_content_logger(__name__)

# ✅ SAFE: Log operation with required fields
logger.log_operation(
    tenant_id=firm.id,
    correlation_id=correlation_id,
    actor=user.username,
    operation="document_upload",
    object_type="Document",
    object_id=document.pk,
    status="success",
    duration_ms=150,
)

# ❌ UNSAFE: This will raise ValueError
logger.log_operation(
    tenant_id=firm.id,
    correlation_id=correlation_id,
    email_body="sensitive content",  # FORBIDDEN!
)
```

**Implementation:** `src/modules/core/structured_logging.py::NoContentLogger`

### 2.3 Governance-Aware Logging (DOC-07.1)

**SafeLogger** integrates with governance classification registry:

```python
from modules.core.logging_utils import get_safe_logger

logger = get_safe_logger(__name__)

# Logs with automatic redaction based on governance classification
logger.info_entity('Contact', contact_data, "Contact created")
```

**Implementation:** `src/modules/core/logging_utils.py::SafeLogger`

---

## 3. Usage Examples

### 3.1 API Request Logging

```python
from modules.core.structured_logging import get_no_content_logger
from modules.core.observability import get_correlation_id_from_request

logger = get_no_content_logger(__name__)

def my_api_view(request):
    correlation_id = get_correlation_id_from_request(request)

    logger.log_operation(
        tenant_id=request.firm.id,
        correlation_id=correlation_id,
        actor=request.user.username,
        operation="api_document_list",
        status="success",
        duration_ms=45,
    )
```

**Log output:**
```json
{
  "timestamp": "2025-12-30T10:30:00.123Z",
  "level": "INFO",
  "logger": "mymodule",
  "message": "Operation: api_document_list | Status: success",
  "tenant_id": 123,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "actor": "john.doe",
  "operation": "api_document_list",
  "status": "success",
  "duration_ms": 45
}
```

### 3.2 Background Job Logging

```python
from modules.core.structured_logging import get_no_content_logger

logger = get_no_content_logger(__name__)

def process_email_ingestion_job(job):
    logger.log_operation(
        tenant_id=job.payload["tenant_id"],
        correlation_id=uuid.UUID(job.payload["correlation_id"]),
        operation="email_ingestion_fetch",
        object_type="EmailArtifact",
        object_id=job.payload.get("external_message_id"),
        status="success",
        duration_ms=250,
    )
```

**Log output:**
```json
{
  "timestamp": "2025-12-30T10:30:00.123Z",
  "level": "INFO",
  "logger": "email_ingestion",
  "message": "Operation: email_ingestion_fetch | Status: success | Object: EmailArtifact#msg_789",
  "tenant_id": 123,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "operation": "email_ingestion_fetch",
  "object_type": "EmailArtifact",
  "object_id": "msg_789",
  "status": "success",
  "duration_ms": 250
}
```

### 3.3 Security Event Logging

```python
logger.log_security_event(
    tenant_id=firm.id,
    correlation_id=correlation_id,
    event_type="permission_denied",
    actor=user.username,
    resource_type="Document",
    resource_id=document.pk,
    action="download",
    result="denied",
    reason="insufficient_permissions",
)
```

**Log output:**
```json
{
  "timestamp": "2025-12-30T10:30:00.123Z",
  "level": "WARNING",
  "logger": "security",
  "message": "Security Event: permission_denied | Actor: john.doe | Action: download | Result: denied",
  "tenant_id": 123,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "permission_denied",
  "actor": "john.doe",
  "object_type": "Document",
  "object_id": "456",
  "action": "download",
  "result": "denied",
  "extra_data": {
    "reason": "insufficient_permissions"
  }
}
```

### 3.4 Error Logging with PII Filtering

```python
logger.log_error(
    tenant_id=firm.id,
    correlation_id=correlation_id,
    error_type="ValidationError",
    error_message="Invalid email format",
    object_type="Contact",
    object_id=contact.pk,
    provided_email="user@example.com",  # Will be masked
)
```

**Log output:**
```json
{
  "timestamp": "2025-12-30T10:30:00.123Z",
  "level": "ERROR",
  "logger": "contacts",
  "message": "Error: ValidationError | Invalid email format",
  "tenant_id": 123,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "error_type": "ValidationError",
  "object_type": "Contact",
  "object_id": "789",
  "extra_data": {
    "provided_email": "us***(17 chars)"  // Masked per PII rules
  }
}
```

---

## 4. Safe vs Unsafe Logging Patterns

### 4.1 ✅ SAFE Patterns

```python
# ✅ Log with object ID reference, not content
logger.log_operation(
    tenant_id=firm.id,
    correlation_id=correlation_id,
    operation="email_processed",
    object_id=email.external_message_id,  # ID only
    status="success",
)

# ✅ Log error type, not error details with PII
logger.log_error(
    tenant_id=firm.id,
    correlation_id=correlation_id,
    error_type="ParseError",
    error_message="Failed to parse email headers",  # Generic
)

# ✅ Log document operation with size, not content
logger.log_operation(
    tenant_id=firm.id,
    correlation_id=correlation_id,
    operation="document_uploaded",
    object_id=document.pk,
    file_size_bytes=1024000,  # Metadata only
    status="success",
)
```

### 4.2 ❌ UNSAFE Patterns

```python
# ❌ FORBIDDEN: Logging email body (content)
logger.info(f"Received email: {email.body}")  # NEVER DO THIS

# ❌ FORBIDDEN: Logging document content
logger.debug(f"Document content: {document.content}")  # NEVER DO THIS

# ❌ FORBIDDEN: Logging PII without redaction
logger.info(f"User email: {user.email}")  # Use object ID instead

# ❌ FORBIDDEN: Logging sensitive payload
logger.debug(f"Request data: {json.dumps(request.data)}")  # May contain PII/content
```

---

## 5. Compliance Verification

### 5.1 LogValidator

Use `LogValidator` in tests to verify compliance:

```python
from modules.core.structured_logging import LogValidator

def test_log_compliance():
    log_record = {
        "timestamp": "2025-12-30T10:30:00.123Z",
        "level": "INFO",
        "tenant_id": 123,
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Operation completed",
    }

    violations = LogValidator.validate_log_record(log_record)
    assert len(violations) == 0, f"Log compliance violations: {violations}"

    assert LogValidator.is_compliant(log_record)
```

### 5.2 Compliance Checklist

For each log statement, verify:

- [ ] Includes `tenant_id` (when applicable)
- [ ] Includes `correlation_id` (always)
- [ ] Includes `actor` (when user-initiated)
- [ ] Includes `object_id` (when entity-related)
- [ ] Does NOT include forbidden content fields
- [ ] PII fields are masked/redacted
- [ ] Message length < 1000 chars (prevent content leakage)

---

## 6. Integration with Existing Systems

### 6.1 Observability Metrics (DOC-21.1)

Metrics tracking from `modules/core/observability.py` already includes required fields:

```python
from modules.core.observability import track_api_request

track_api_request(
    route="/api/documents/",
    status_code=200,
    duration_ms=45,
    correlation_id=correlation_id,  # ✅ Included
    tenant_id=firm.id,  # ✅ Included
)
```

### 6.2 Governance Classification (DOC-07.1)

SafeLogger from `modules/core/logging_utils.py` integrates with governance registry:

```python
from modules.core.logging_utils import get_safe_logger

logger = get_safe_logger(__name__)

# Automatic redaction based on governance classification
logger.info_entity('Contact', contact_data, "Contact updated")
# HR fields automatically redacted
# R-PII fields automatically masked
```

---

## 7. Configuration

### 7.1 Application Startup

Configure structured logging in your application startup (e.g., `settings.py` or `wsgi.py`):

```python
from modules.core.structured_logging import configure_structured_logging
from modules.core.logging_utils import configure_governance_logging

# Configure structured JSON logging
configure_structured_logging()

# Configure governance redaction filter
configure_governance_logging()
```

### 7.2 Django Logging Configuration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            '()': 'modules.core.structured_logging.StructuredLogFormatter',
        },
    },
    'filters': {
        'governance': {
            '()': 'modules.core.logging_utils.GovernanceRedactionFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
            'filters': ['governance'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

---

## 8. Compliance Matrix

| Requirement | docs/21 Section | Status | Implementation |
|-------------|-----------------|--------|----------------|
| Logs include tenant_id | 4 | ✅ Complete | StructuredLogFormatter, NoContentLogger |
| Logs include correlation_id | 4 | ✅ Complete | Required parameter in log_operation() |
| Logs include actor (when applicable) | 4 | ✅ Complete | Optional parameter in log_operation() |
| Logs include primary object ids | 4 | ✅ Complete | object_type + object_id parameters |
| Logs redact HR data | 4 | ✅ Complete | StructuredLogFormatter._filter_content() |
| Logs minimize PII | 4 | ✅ Complete | PII masking in StructuredLogFormatter |
| No-content logging (forbidden fields) | 4 (implied) | ✅ Complete | FORBIDDEN_CONTENT_FIELDS validation |
| Integration with governance registry | 4 | ✅ Complete | SafeLogger from logging_utils.py |
| Correlation IDs flow through systems | 1 | ✅ Complete | observability.py (DOC-21.1) |
| JSON structured logging | - | ✅ Complete | StructuredLogFormatter |

**Overall Compliance:** 10/10 requirements (100% with docs/21 section 4)

---

## 9. Related Documentation

- **docs/21**: OBSERVABILITY_AND_SRE (canonical requirements)
- **docs/7**: DATA_GOVERNANCE (classification levels, PII handling)
- **src/modules/core/logging_utils.py**: SafeLogger with governance integration (DOC-07.1)
- **src/modules/core/observability.py**: Correlation IDs and metrics (DOC-21.1)
- **docs/ALERT_CONFIGURATION.md**: Alert thresholds (DOC-21.1)

---

## 10. Summary

DOC-21.2 implementation provides:

✅ **Required fields**: tenant_id, correlation_id, actor, object_id enforced in all logs
✅ **No-content logging**: Forbidden content fields validated and blocked
✅ **PII minimization**: R-PII masked, HR redacted per governance classification
✅ **Structured JSON logging**: StructuredLogFormatter for log aggregation
✅ **NoContentLogger**: High-level API enforcing logging guarantees
✅ **LogValidator**: Testing utilities for compliance verification
✅ **100% compliance** with docs/21 section 4

The implementation builds on existing governance infrastructure (DOC-07.1) and observability (DOC-21.1) to provide comprehensive no-content logging guarantees with PII minimization.
