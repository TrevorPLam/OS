# Tier 3: Audit Event System

**Status**: ✅ IMPLEMENTED
**Created**: 2025-12-25
**Last Updated**: 2025-12-25

## Overview

The audit event system provides structured, immutable logging for all critical platform actions, enabling compliance, security review, and incident investigation without exposing customer content.

## Architecture

### Core Model: `AuditEvent`

Location: `src/modules/firm/audit.py`

The `AuditEvent` model tracks all critical platform actions with:
- **Immutability**: No updates allowed after creation
- **Tenant Scoping**: All events belong to a Firm
- **Privacy First**: Only metadata, never customer content
- **Categorization**: Structured event taxonomy

### Event Categories

As per Tier 3 requirements, all events are categorized:

| Category | Description | Examples | Severity |
|----------|-------------|----------|----------|
| `AUTH` | Authentication & Authorization | login_success, login_failed, permission_denied | INFO/WARNING |
| `PERMISSIONS` | Permission/Role Changes | role_granted, role_revoked, membership_added | WARNING |
| `BREAK_GLASS` | Break-Glass Content Access | break_glass_activated, content_accessed | CRITICAL |
| `BILLING_METADATA` | Billing Events (metadata only) | invoice_created, payment_processed | INFO |
| `PURGE` | Content Purge Operations | document_purged, message_purged | CRITICAL |
| `CONFIG` | Configuration Changes | firm_settings_updated, feature_enabled | WARNING |
| `DATA_ACCESS` | Data Access Events | export_generated, report_downloaded | INFO |
| `SYSTEM` | System Events | migration_completed, backup_created | INFO |

### Event Fields

Every audit event includes:

#### Required Fields
- `firm`: Tenant context (FK to Firm, PROTECTED)
- `category`: Event category (see above)
- `action`: Specific action taken (e.g., "login_failed")
- `timestamp`: When event occurred (indexed)

#### Actor Fields (who performed the action)
- `actor`: User who performed action (FK, nullable for system events)
- `actor_email`: Email preserved even if user deleted
- `actor_role`: User's role at time of action

#### Target Fields (what was acted upon)
- `target_model`: Model name (e.g., "Document")
- `target_id`: Object ID
- `target_repr`: Human-readable representation (no sensitive data)

#### Context Fields
- `reason`: Why action was taken (required for break-glass, purge)
- `outcome`: Result (success, denied, failed)
- `severity`: INFO, WARNING, or CRITICAL
- `metadata`: Additional context (JSON, no customer content)

#### Request Context
- `ip_address`: Request IP
- `user_agent`: Browser/client info
- `request_id`: For correlation across systems

#### Review Tracking
- `reviewed_at`: When event was reviewed
- `reviewed_by`: Who reviewed it
- `review_notes`: Reviewer's notes

## Usage

### Basic Event Logging

```python
from modules.firm.audit import audit

# Authentication event
audit.log_auth_event(
    firm=request.firm,
    action='login_success',
    actor=user,
    outcome='success',
    ip_address=get_client_ip(request),
    metadata={'method': '2FA'}
)

# Permission change
audit.log_permission_change(
    firm=request.firm,
    action='role_granted',
    actor=request.user,
    target_model='FirmMembership',
    target_id=membership.id,
    metadata={'old_role': 'staff', 'new_role': 'admin'}
)
```

### Critical Events (Break-Glass, Purge)

```python
# Break-glass activation (CRITICAL)
audit.log_break_glass_event(
    firm=firm,
    action='break_glass_activated',
    actor=platform_operator,
    reason='Customer support ticket #12345 - urgent data recovery',
    metadata={'ticket_id': '12345', 'duration_minutes': 30}
)

# Content purge (CRITICAL)
audit.log_purge_event(
    firm=firm,
    action='document_purged',
    actor=master_admin,
    target_model='Document',
    target_id=document.id,
    reason='Legal hold expired, customer requested deletion',
    metadata={'legal_case_id': 'CASE-2024-001'}
)
```

### Custom Events

```python
# For custom events, use log_event directly
from modules.firm.audit import AuditEvent, audit

audit.log_event(
    firm=firm,
    category=AuditEvent.CATEGORY_SYSTEM,
    action='data_export_completed',
    actor=request.user,
    severity=AuditEvent.SEVERITY_INFO,
    metadata={
        'export_type': 'full_backup',
        'file_count': 1250,
        'size_mb': 450
    }
)
```

## Security Guarantees

### 1. Immutability

Audit events **cannot be modified** after creation:
- `save()` raises `ValidationError` if called on existing event
- `delete()` is blocked entirely
- Updates must create new events instead

### 2. Tenant Isolation

All audit events are tenant-scoped:
- `firm` FK is required
- Cascading deletes are prevented (`on_delete=PROTECT`)
- Queries must filter by firm

### 3. Privacy First

Audit events **never** contain customer content:
- Only metadata (IDs, timestamps, actions)
- `target_repr` must not include sensitive data
- `metadata` JSON must not include content

### 4. Tamper Evidence

Future enhancement: Hash chain validation
- Each event links to previous event hash
- Enables detection of log tampering
- Implementation planned for Tier 5

## Retention Policy

### Default Retention Windows

| Category | Retention Period | Rationale |
|----------|------------------|-----------|
| AUTH | 1 year | Security investigations |
| PERMISSIONS | 3 years | Compliance audits |
| BREAK_GLASS | 7 years | Legal liability |
| BILLING_METADATA | 7 years | Tax/accounting requirements |
| PURGE | 7 years | Legal proof of deletion |
| CONFIG | 1 year | Change tracking |
| DATA_ACCESS | 1 year | Privacy compliance |
| SYSTEM | 90 days | Operational debugging |

### Implementation

Retention enforcement planned for Tier 5:
- Automated archival after retention period
- Metadata preservation even after archival
- Legal hold support for extended retention

## Database Schema

### Indexes

Optimized for common query patterns:
- `(firm, category, timestamp DESC)` - Category-based review
- `(firm, actor, timestamp DESC)` - User activity tracking
- `(category, severity, timestamp DESC)` - Critical event review
- `(firm, action, timestamp DESC)` - Action-specific queries

### Permissions

Custom Django permissions:
- `review_audit_events`: Can review and mark events as reviewed
- `export_audit_events`: Can export audit logs for compliance

## Integration Points

### 1. Break-Glass Sessions

When break-glass session is activated:
```python
audit.log_break_glass_event(
    firm=firm,
    action='break_glass_activated',
    actor=operator,
    reason=session.reason,
    metadata={'session_id': session.id, 'expires_at': str(session.expires_at)}
)
```

### 2. Purge Operations

When content is purged (see PURGE_AND_TOMBSTONE_ARCHITECTURE.md):
```python
audit.log_purge_event(
    firm=firm,
    action='document_content_purged',
    actor=request.user,
    target_model='Document',
    target_id=document.id,
    reason=purge_reason,
    metadata={'tombstone_id': tombstone.id}
)
```

### 3. Permission Changes

When roles/permissions change:
```python
audit.log_permission_change(
    firm=request.firm,
    action='firm_membership_role_changed',
    actor=request.user,
    target_model='FirmMembership',
    target_id=membership.id,
    metadata={'old_role': old_role, 'new_role': new_role}
)
```

## Testing

See `tests/safety/test_audit_events.py` for comprehensive tests:
- Immutability enforcement
- Required field validation
- Category-specific helpers
- Privacy compliance (no content in metadata)

## Next Steps

### Tier 3 Completion
- ✅ Event taxonomy defined
- ✅ Immutable model implemented
- ✅ Helper utilities created
- ✅ Migration applied
- [ ] Integrate with break-glass system (update permissions.py)
- [ ] Integrate with purge flows (Task 3.1)
- [ ] Add review dashboard (Tier 4)

### Future Enhancements (Tier 5)
- Hash chain for tamper detection
- Automated retention enforcement
- Real-time anomaly detection
- SIEM integration (syslog export)
- Compliance report generation
