# Audit Event Taxonomy & Retention Policy

**TIER 3.2 — Data Integrity & Privacy**

**Last Updated:** December 24, 2025

---

## Overview

This document defines the comprehensive audit event taxonomy and retention policy for the ConsultantPro platform. The audit system is a foundational component of TIER 3 compliance, ensuring:

- **Immutability:** Audit events cannot be modified or deleted via application code
- **Tenant Isolation:** All audit events are firm-scoped (multi-tenant safe)
- **Privacy-First:** Audit events contain only metadata, never customer content
- **Retention Compliance:** Events are retained according to legal and operational requirements
- **Transparency:** Platform operations are traceable and reviewable

---

## Escalation Path for Anomalies

When reviewers detect anomalous or unauthorized activity, escalation follows a consistent path:

1. **Review Owner** documents findings and opens an incident ticket.
2. **Security Lead** evaluates impact and containment within 24 hours.
3. **CTO/VP Engineering** is engaged for critical severity or customer-impacting incidents.
4. **Legal/Compliance** is engaged when regulatory exposure, customer disputes, or data deletion requests are involved.

---

## Audit Event Categories

The platform defines **10 event categories**, each with specific retention policies and review cadences:

### 1. AUTH — Authentication & Authorization

**Purpose:** Track authentication attempts, session management, and authorization failures

**Examples:**
- `user.login.success` — User successfully logged in
- `user.login.failure` — Failed login attempt
- `user.logout` — User logged out
- `session.expired` — Session expired
- `password.reset` — Password reset requested
- `mfa.enabled` — Multi-factor authentication enabled
- `api_token.created` — API token generated

**Retention:** 90 days
**Review Cadence:** Monthly
**Review Owner:** Platform Operations
**Review Focus:** Identify authentication anomalies, brute force attempts, unauthorized access patterns

---

### 2. PERMISSIONS — Permission Changes

**Purpose:** Track changes to user roles, permissions, and access controls

**Examples:**
- `role.assigned` — User role changed
- `permission.granted` — Specific permission granted
- `permission.revoked` — Permission removed
- `firm_membership.created` — User added to firm
- `firm_membership.deactivated` — User removed from firm
- `access_control.modified` — Access control rule changed

**Retention:** 1 year (365 days)
**Review Cadence:** Monthly
**Review Owner:** Platform Security Team
**Review Focus:** Detect privilege escalation, unauthorized role changes, anomalous permission grants

---

### 3. BREAK_GLASS — Break-Glass Content Access

**Purpose:** Track all break-glass activations and content access by platform operators

**Examples:**
- `break_glass.activate` — Break-glass session activated
- `break_glass.revoke` — Break-glass session revoked early
- `break_glass.expire` — Break-glass session expired
- `break_glass.content_access` — Content accessed during break-glass
- `break_glass.review` — Break-glass session reviewed

**Retention:** 7 years (2555 days) — **Legal/Compliance Requirement**
**Review Cadence:** Weekly
**Review Owner:** Platform Security Team
**Review Focus:** All break-glass activations must be reviewed; verify reason strings are legitimate; confirm proper authorization

**Critical Requirements:**
- **Reason string is MANDATORY** for all break-glass events
- All break-glass events are **SEVERITY_CRITICAL**
- Break-glass events are **NEVER DELETED** (7-year retention)

---

### 4. BILLING_METADATA — Billing Metadata Operations

**Purpose:** Track billing-related operations (metadata only, not payment details)

**Examples:**
- `invoice.created` — Invoice created
- `invoice.sent` — Invoice sent to client
- `invoice.voided` — Invoice voided (with reason)
- `payment.recorded` — Payment recorded (amount only, no PII)
- `subscription.changed` — Subscription tier changed
- `credit.applied` — Credit applied to account
- `billing_override.applied` — Manual billing adjustment (requires reason)

**Retention:** 7 years (2555 days) — **Financial Records Requirement**
**Review Cadence:** Monthly
**Review Owner:** Finance Team
**Review Focus:** Ensure billing operations are auditable; detect anomalous adjustments; compliance with financial regulations

**Note:** Payment processor events (PCI-DSS scope) are logged separately by the payment provider. This category covers platform metadata only.

---

### 5. PURGE — Data Purge/Deletion

**Purpose:** Track all hard deletions and content purges (legal/compliance)

**Examples:**
- `document.purge` — Document content purged (metadata retained)
- `message.purge` — Message content purged (tombstone created)
- `client.purge` — Client data purged (legal request)
- `firm.offboard` — Firm data purged after retention period
- `user.gdpr_erasure` — GDPR right-to-erasure request fulfilled

**Retention:** **Forever (never deleted)** — `None`
**Review Cadence:** Weekly
**Review Owner:** Platform Security + Legal
**Review Focus:** Every purge must be reviewed; verify reason strings reference legal requests or customer authorization; ensure tombstones are created

**Critical Requirements:**
- **Reason string is MANDATORY** for all purge events
- All purge events are **SEVERITY_CRITICAL**
- Purge events **SURVIVE FOREVER** (even after firm offboarding)
- Purge events must reference legal request ID or customer authorization

---

### 6. CONFIG — Configuration Changes

**Purpose:** Track platform and firm-level configuration changes

**Examples:**
- `firm.settings.updated` — Firm settings modified
- `feature_flag.changed` — Feature flag toggled
- `integration.enabled` — Third-party integration enabled
- `webhook.configured` — Webhook endpoint configured
- `rate_limit.adjusted` — Rate limit changed (with reason)
- `subscription_tier.changed` — Firm subscription tier modified

**Retention:** 1 year (365 days)
**Review Cadence:** Monthly
**Review Owner:** Platform Operations
**Review Focus:** Detect unauthorized configuration changes; verify security-impacting changes are authorized

---

### 7. DATA_ACCESS — Data Access Events

**Purpose:** Track significant data access operations (portal access, reports, exports)

**Examples:**
- `portal.login` — Client portal user logged in
- `report.generated` — Analytics report generated
- `search.executed` — Search query executed (metadata only, not results)
- `bulk_export.requested` — Bulk data export requested
- `api.access` — API endpoint accessed (high-value endpoints only)

**Retention:** 90 days
**Review Cadence:** Quarterly
**Review Owner:** Platform Operations
**Review Focus:** Detect anomalous access patterns; identify potential data exfiltration attempts

**Note:** Not all data access is logged (would be excessive). Only high-value or sensitive endpoints are audited.

---

### 8. ROLE_CHANGE — Role & Membership Changes

**Purpose:** Track firm membership and role lifecycle events

**Examples:**
- `firm_membership.invited` — User invited to firm
- `firm_membership.accepted` — User accepted firm invitation
- `firm_membership.role_changed` — User role changed within firm
- `firm_membership.deactivated` — User removed from firm
- `firm_ownership.transferred` — Firm ownership transferred
- `contractor.added` — Contractor added to firm

**Retention:** 1 year (365 days)
**Review Cadence:** Monthly
**Review Owner:** Platform Security Team
**Review Focus:** Detect unauthorized membership changes; verify ownership transfers are legitimate

---

### 9. EXPORT — Data Export Operations

**Purpose:** Track data export operations (firm offboarding, customer exports)

**Examples:**
- `firm.export.requested` — Firm data export requested
- `firm.export.completed` — Firm data export package ready
- `client.export.requested` — Client data export requested
- `support.export.created` — Support diagnostics package created
- `api.bulk_export` — Bulk API export operation

**Retention:** 1 year (365 days)
**Review Cadence:** Quarterly
**Review Owner:** Platform Operations
**Review Focus:** Monitor export operations; detect potential data exfiltration; ensure export requests are legitimate

---

### 10. SIGNING — Document Signing Events

**Purpose:** Track document signing lifecycle (immutable, survives content purges)

**Examples:**
- `document.signed` — Document signed by user
- `signature.verified` — Signature verification performed
- `document.version_signed` — Specific document version signed
- `signing_certificate.issued` — Digital signing certificate issued
- `signature.evidence_retained` — Signature evidence archived

**Retention:** **Forever (never deleted)** — `None`
**Review Cadence:** As Needed (during disputes)
**Review Owner:** Legal + Compliance
**Review Focus:** Signing evidence must survive content purges; verify signatures are cryptographically valid; support legal disputes

**Critical Requirements:**
- Signing events **SURVIVE FOREVER**
- Signing events must reference **document version hash**, not plaintext content
- Signature evidence must be **cryptographically verifiable**
- Signing events survive document purges (tombstone pattern)

---

## Event Fields (Standard Schema)

Every audit event contains the following structured fields:

### Required Fields
- `firm` (ForeignKey) — Tenant context (required for all events)
- `category` (CharField) — Event category (one of 10 defined categories)
- `action` (CharField) — Action string (e.g., `user.login`, `break_glass.activate`)
- `timestamp` (DateTimeField) — When the event occurred (auto_now_add, immutable)

### Actor Context (Who)
- `actor` (ForeignKey to User) — User who performed the action (null for system events)
- `actor_ip` (GenericIPAddressField) — IP address of actor
- `actor_user_agent` (TextField) — User agent string

### Target Context (What)
- `target_content_type` (ForeignKey to ContentType) — Type of object acted upon
- `target_object_id` (CharField) — ID of target object
- `target_object` (GenericForeignKey) — Django generic foreign key
- `target_description` (CharField) — Human-readable description (survives target deletion)

### Additional Context
- `client` (ForeignKey to Client) — Client context (if action is client-scoped)
- `reason` (TextField) — Reason string (MANDATORY for BREAK_GLASS and PURGE)
- `metadata` (JSONField) — Content-free structured data (operational metadata only)
- `severity` (CharField) — info / warning / critical

### Retention Management
- `retention_until` (DateTimeField) — When this event can be deleted (null = keep forever)

---

## Retention Policy Summary

| Category | Retention Period | Keep Forever? | Reason |
|----------|-----------------|---------------|--------|
| AUTH | 90 days | No | Operational security monitoring |
| PERMISSIONS | 1 year | No | Compliance and security review |
| BREAK_GLASS | 7 years | No* | Legal/compliance requirement |
| BILLING_METADATA | 7 years | No* | Financial records retention |
| PURGE | Forever | **Yes** | Liability protection |
| CONFIG | 1 year | No | Operational review |
| DATA_ACCESS | 90 days | No | Anomaly detection |
| ROLE_CHANGE | 1 year | No | Security review |
| EXPORT | 1 year | No | Compliance monitoring |
| SIGNING | Forever | **Yes** | Legal evidence |

**Note:** While BREAK_GLASS and BILLING_METADATA have 7-year retention, they are not kept forever. Only PURGE and SIGNING events are kept indefinitely.

---

## Review Ownership & Cadence

### Weekly Reviews (High-Risk)
- **BREAK_GLASS** — Platform Security Team
- **PURGE** — Platform Security + Legal

### Monthly Reviews (Security & Compliance)
- **AUTH** — Platform Operations
- **PERMISSIONS** — Platform Security Team
- **BILLING_METADATA** — Finance Team
- **CONFIG** — Platform Operations
- **ROLE_CHANGE** — Platform Security Team

### Quarterly Reviews (Operational)
- **DATA_ACCESS** — Platform Operations
- **EXPORT** — Platform Operations

### As-Needed Reviews (Disputes)
- **SIGNING** — Legal + Compliance

---

## Audit Event Invariants

### Immutability
1. Audit events **CANNOT be updated** after creation
2. Audit events **CANNOT be deleted** via Django ORM
3. Updates and deletes via application code raise `ValidationError`
4. Only retention cleanup jobs can delete expired events

### Tenant Isolation
1. All audit events **MUST** have a `firm` foreign key
2. Queries without firm context raise `ValueError`
3. Firm-scoped queryset helpers enforce isolation
4. Platform operators cannot bypass firm scoping

### Privacy-First (Content-Free)
1. Audit metadata **MUST NOT** contain customer content
2. Forbidden metadata keys: `password`, `token`, `secret`, `content`, `body`, `message_text`
3. Metadata validation enforced on save
4. Only operational metadata is allowed

### Mandatory Reason Strings
1. **BREAK_GLASS** events require `reason` (ValidationError if missing)
2. **PURGE** events require `reason` (ValidationError if missing)
3. Reason strings must reference authorization (support ticket, legal request, etc.)

---

## Usage Examples

### Example 1: Break-Glass Activation

```python
from modules.firm.models import create_audit_event, AuditEvent

# Create break-glass audit event
create_audit_event(
    firm=request.firm,
    category=AuditEvent.CATEGORY_BREAK_GLASS,
    action='break_glass.activate',
    actor=request.user,
    actor_ip=get_client_ip(request),
    actor_user_agent=request.META.get('HTTP_USER_AGENT', ''),
    reason='Customer support case #12345: Debug billing issue',
    severity=AuditEvent.SEVERITY_CRITICAL,
    metadata={
        'session_id': break_glass_session.id,
        'duration_minutes': 60,
        'client_id': client.id,
    }
)
```

### Example 2: Document Purge

```python
# Purge document content (legal request)
create_audit_event(
    firm=document.firm,
    category=AuditEvent.CATEGORY_PURGE,
    action='document.purge',
    actor=request.user,
    actor_ip=get_client_ip(request),
    target_object=document,
    target_description=f"Document: {document.name} (ID: {document.id})",
    client=document.client,
    reason='GDPR right-to-erasure request: Case #GDPR-2025-001',
    severity=AuditEvent.SEVERITY_CRITICAL,
    metadata={
        'document_id': str(document.id),
        'original_filename': document.name,
        'file_size_bytes': document.size,
        'legal_request_id': 'GDPR-2025-001',
    }
)

# Then purge the document content
document.content = None
document.is_purged = True
document.purged_at = timezone.now()
document.save()
```

### Example 3: Role Change

```python
# User role changed
create_audit_event(
    firm=membership.firm,
    category=AuditEvent.CATEGORY_ROLE_CHANGE,
    action='firm_membership.role_changed',
    actor=request.user,
    target_object=membership,
    target_description=f"{membership.user.get_full_name()} role changed",
    metadata={
        'user_id': membership.user.id,
        'old_role': 'staff',
        'new_role': 'admin',
        'changed_by': request.user.username,
    }
)
```

### Example 4: Querying Audit Events

```python
# Get all break-glass events for a firm
break_glass_events = AuditEvent.objects.for_firm(firm).break_glass_events()

# Get critical events in the last 7 days
critical_events = AuditEvent.objects.for_firm(firm).critical_events().since(
    timezone.now() - timedelta(days=7)
)

# Get events eligible for deletion (past retention period)
expired_events = AuditEvent.objects.eligible_for_deletion()

# Get all purge events (never deleted)
purge_events = AuditEvent.objects.purge_events()
```

---

## Implementation Status

### ✅ COMPLETE (TIER 3.2)
- [x] Audit event model created (`AuditEvent`)
- [x] Event categories defined (10 categories)
- [x] Retention policies defined (per-category retention)
- [x] Review ownership and cadence defined
- [x] Immutability enforcement (no updates, no deletes)
- [x] Tenant scoping enforced (firm-scoped queries)
- [x] Privacy-first validation (content-free metadata)
- [x] Structured audit write helper (`create_audit_event()`)
- [x] Django admin integration (read-only, immutable)
- [x] Database migration created (`0004_audit_event.py`)
- [x] Comprehensive documentation

### 🔄 NEXT STEPS (TIER 3.3+)
- [ ] Integrate audit events with break-glass activation (TIER 3.3)
- [ ] Integrate audit events with purge operations (TIER 3.1)
- [ ] Integrate audit events with billing operations (TIER 4)
- [ ] Create retention cleanup job (tenant-aware background job)
- [ ] Implement audit event export for platform operators
- [ ] Create audit review dashboard for security team
- [ ] Add alerting for critical audit events (break-glass, purge)

---

## Compliance & Legal Notes

### GDPR Compliance
- Audit events contain **metadata only**, not personal data content
- GDPR right-to-erasure: Customer content is purged, but **purge events survive**
- Audit events are **legitimate interest** (security, fraud prevention, legal compliance)

### SOC 2 Compliance
- Audit events provide **security monitoring** (CC6.1, CC6.2)
- Immutability ensures **audit integrity** (CC6.3)
- Retention policies support **availability commitments** (A1.2)

### Financial Regulations
- 7-year retention for **BILLING_METADATA** and **BREAK_GLASS** (IRS, GAAP)
- **PURGE** events kept forever (liability protection)
- **SIGNING** events kept forever (contract evidence)

---

## Security Considerations

### Threat Model

**Threat:** Malicious insider deletes audit events to cover tracks
**Mitigation:** Audit events are immutable; Django ORM prevents updates/deletes

**Threat:** Audit events leak customer content
**Mitigation:** Metadata validation forbids content keys; content-free enforcement

**Threat:** Cross-tenant audit event access
**Mitigation:** Firm-scoped querysets; tenant context required for all queries

**Threat:** Audit event retention exceeds policy (storage costs)
**Mitigation:** Retention cleanup job deletes expired events (non-forever categories)

**Threat:** Break-glass abuse goes undetected
**Mitigation:** Weekly review cadence; critical severity; mandatory reason strings

---

## References

- **Authoritative Rules:** `docs/claude/NOTES_TO_CLAUDE.md`
- **TODO:** `TODO.md` (TIER 3.2 complete)
- **Models:** `src/modules/firm/models.py` (AuditEvent model)
- **Admin:** `src/modules/firm/admin.py` (AuditEventAdmin)
- **Migration:** `src/modules/firm/migrations/0004_audit_event.py`

---

**Document Status:** ✅ COMPLETE
**TIER 3.2 Status:** ✅ COMPLETE
**Next Task:** TIER 3.1 (Purge semantics) or TIER 3.3 (Audit review ownership)
