# AGENTS.md — Core Module (Shared Infrastructure)

Last Updated: 2026-01-06
Applies To: `src/modules/core/`

## Purpose

Cross-cutting infrastructure used by ALL other modules. This is the "plumbing" layer.

## Key Components

| File | Purpose |
|------|---------|
| `access_controls.py` | Break-glass access, impersonation controls |
| `encryption.py` | Field-level encryption service (KMS integration) |
| `erasure.py` | GDPR erasure/anonymization utilities |
| `governance.py` | Governance health checks |
| `input_validation.py` | Shared input validators |
| `logging_utils.py` | Legacy logging (prefer `structured_logging.py`) |
| `middleware.py` | Core middleware components |
| `notifications.py` | Notification dispatch utilities |
| `observability.py` | Metrics, tracing setup |
| `purge.py` | Content purge model (PurgedContent) |
| `rate_limiting.py` | Rate limit utilities |
| `retention.py` | Data retention policy enforcement |
| `security_monitoring.py` | Security event detection |
| `serializer_mixins.py` | Common serializer patterns |
| `structured_logging.py` | **PREFERRED** logging (no content in logs) |
| `telemetry.py` | Telemetry redaction and export |
| `validators.py` | `validate_safe_url`, common validators |

## Critical Rules

### 1. No Content Logging

**NEVER** log customer content. Use structured logging:

```python
from modules.core.structured_logging import get_logger

logger = get_logger(__name__)

# GOOD: Log metadata only
logger.info("document_uploaded", firm_id=firm.id, document_id=doc.id, size_bytes=doc.size)

# BAD: Logs content
logger.info(f"Document content: {doc.content}")  # VIOLATION
```

### 2. Field Encryption

For sensitive fields (PII, credentials):

```python
from modules.core.encryption import field_encryption_service

encrypted = field_encryption_service.encrypt(plaintext, firm.kms_key_id)
plaintext = field_encryption_service.decrypt(encrypted, firm.kms_key_id)
```

### 3. Safe URL Validation

Always validate user-provided URLs:

```python
from modules.core.validators import validate_safe_url

url = models.URLField(validators=[validate_safe_url])
```

## Models

### PurgedContent

Tracks content that has been purged (GDPR, retention policy):

```python
from modules.core.purge import PurgedContent

# Records are created automatically when content is purged
# Used for audit trail and compliance reporting
```

## Dependencies

- **Depends on**: Nothing (foundation module)
- **Used by**: All other modules

## Testing

Tests are scattered across `tests/` by feature. Key files:
- `tests/safety/test_telemetry_redaction.py` — Ensures no content in telemetry
- `tests/safety/test_query_guards.py` — Query scoping validation
