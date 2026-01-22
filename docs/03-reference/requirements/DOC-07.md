# Data Governance (DATA_GOVERNANCE)

This document defines the platform’s data governance rules: classification, retention, soft delete behavior, anonymization/erasure workflows, and audit vs activity retention requirements.

This document is normative. If it conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Objectives

1. The platform MUST classify and handle sensitive data consistently across:
   - APIs
   - UIs
   - background workers
   - integrations (email/calendar)
   - storage/document pipelines

2. The platform MUST support:
   - least-privilege access
   - auditability (who accessed/changed what)
   - retention and deletion policies (soft delete, legal hold, anonymization where required)

3. The platform MUST minimize the spread of PII into non-governed stores (logs, analytics, exports).

---

## 2) Data classification

### 2.1 Classification levels
All fields and artifacts MUST be assigned a classification level. Default classification applies unless overridden explicitly.

- Public (PUB)
  - safe to display publicly
  - no personal or confidential business information

- Internal (INT)
  - internal platform operational info
  - not intended for public exposure, but not regulated PII

- Confidential (CONF)
  - business-sensitive client data (financial reports, internal processes)
  - requires strict access controls, but not necessarily regulated PII

- Restricted PII (R-PII)
  - personal identifying data: names + contact info, identifiers, etc.
  - access must be least-privilege, auditable

- Highly Restricted (HR)
  - credentials/secrets
  - regulated identifiers (government IDs, tax IDs), sensitive financial account numbers
  - special handling required: masking, encryption, limited access, no exposure in logs

### 2.2 Default classification by object type (baseline)
This is a baseline; field-level overrides may apply.

- Account:
  - name: R-PII (if individual/household) or CONF (if business)
  - business metadata: CONF

- Contact:
  - name/email/phone: R-PII
  - role label: INT/CONF depending on context

- Engagement / EngagementLine / WorkItem:
  - titles/descriptions: CONF (may embed PII; treat as CONF by default)
  - internal notes: CONF

- Documents:
  - default: CONF
  - may be R-PII or HR depending on content type (classification label MUST be stored)

- Communications (messages/emails):
  - default: CONF
  - treat email headers/addresses as R-PII

- Billing (invoices/ledger):
  - amounts/services: CONF
  - payment instrument references: HR (if stored at all; prefer tokenization)

- Audit logs:
  - metadata: INT/CONF
  - MUST avoid payloads containing HR data

### 2.3 Field-level classification registry
The platform SHOULD maintain a registry that maps:
- entity.field → classification
- document type → default classification
- export/report → allowed fields

This registry MUST be used by:
- serialization layers (API responses)
- logging redaction
- export tooling

---

## 3) Data handling rules

### 3.1 Minimization
1. Systems MUST NOT collect HR data unless required.
2. Integrations SHOULD store references/tokens instead of raw sensitive values where possible.
3. Logs MUST NOT include HR data and SHOULD avoid R-PII where not required.

### 3.2 Encryption
1. Data at rest MUST be encrypted at the storage layer.
2. HR fields (if stored) SHOULD use application-layer encryption in addition to storage encryption.
3. Secrets MUST be stored in a dedicated secrets manager (not in DB, not in repo, not in logs).

### 3.3 Redaction and masking
1. API responses MUST support redaction where permissions do not allow field-level access.
2. Logs MUST redact:
   - HR values always
   - R-PII values unless strictly required for troubleshooting (and then only partial masking)
3. UI MUST mask HR-like fields by default (last-4 only, etc.) if they exist.

### 3.4 Access logging
1. Access to governed artifacts MUST be logged:
   - document download/view
   - document version upload
   - permission grants/revocations
   - quote acceptance
   - ledger posting
2. Access logs MUST include:
   - actor (staff or portal)
   - timestamp
   - object reference(s)
   - correlation ID

---

## 4) Soft delete policy

### 4.1 Default behavior
1. Tenant data MUST be soft-deleted by default using `deleted_at` (or equivalent).
2. Soft-deleted records MUST be excluded from default queries unless explicitly requested by an authorized role.
3. Soft delete MUST be auditable (who, when, why).

### 4.2 Cascades and dependents
1. Soft delete MUST NOT silently remove dependent audit-critical artifacts.
2. Dependent objects MAY be soft-deleted with explicit cascade rules, but:
   - audit logs MUST remain consistent
   - document versions and ledger entries MUST follow their own retention rules (often longer)

### 4.3 Immutable records
Some records MUST be immutable and never “edited away,” only compensated or superseded:
- LedgerEntry (compensate via new entries)
- QuoteVersion (immutable after acceptance)
- DocumentVersion (immutable content revision)
- AuditEvent (append-only)

---

## 5) Retention rules

Retention rules MUST be explicit and consistent. This section defines categories and requirements; actual durations can be configured but must be documented.

### 5.1 Retention categories
- Operational activity (ACT)
  - chat messages, comments, task updates, sync attempt logs
- Audit records (AUD)
  - permission changes, ledger postings, quote acceptance, document access logs
- Governing artifacts (ART)
  - documents and versions, signed artifact metadata, issued invoices
- Integration traces (INTG)
  - ingestion mapping suggestions, confidence scores, sync attempts, error payloads (redacted)

### 5.2 Baseline retention expectations (configurable)
1. AUD retention SHOULD be longer than ACT retention.
2. ART retention SHOULD meet or exceed typical professional-services audit needs.
3. INTG retention MAY be shorter but MUST preserve enough information to explain why an artifact exists.

### 5.3 Legal hold
1. The platform MUST support legal hold flags that override deletion/anonymization for affected objects.
2. Legal hold MUST be auditable:
   - who applied, when, scope, reason

---

## 6) Anonymization and erasure workflows

### 6.1 Erasure vs anonymization
- Erasure: removing data permanently
- Anonymization: removing identifying information while preserving operational/audit integrity

Because the platform supports audit-sensitive workflows, anonymization will often be preferred to preserve ledger and audit meaning.

### 6.2 Erasure request workflow (normative)
1. The system MUST support an erasure request record that includes:
   - requester identity
   - scope (account/contact)
   - reason and legal basis (if applicable)
   - timestamps and approvals
2. The system MUST evaluate:
   - active engagements
   - outstanding invoices/ledger obligations
   - legal hold
   - contractual retention requirements
3. The system MUST produce a deterministic plan:
   - which fields will be anonymized
   - which artifacts will be retained due to audit/legal requirements
4. Execution MUST be:
   - idempotent
   - logged as an audit event
   - reversible only via restoring from backup (not via “undo” in-app)

### 6.3 Required preservation
Even when anonymizing, the system MUST preserve:
- ledger consistency (amounts, dates, allocations)
- audit event integrity (who performed actions may be anonymized but event structure remains)
- document integrity where required (document may be retained but access removed and identifying metadata anonymized)

### 6.4 Anonymization guidelines (examples)
- Contact: replace names with “Anonymized Contact,” remove email/phone, preserve internal IDs
- Account: replace name if individual, preserve business references if required and permitted
- Messages: redact personal identifiers where feasible; preserve message timestamps and linkage
- Documents: preserve document record and versions if required; remove title/metadata; revoke access

---

## 7) Audit vs activity retention rules

### 7.1 Definitions
- Activity records are day-to-day operational signals (comments, status updates).
- Audit records prove control and accountability (permissions, access, billing).

### 7.2 Requirements
1. Audit events MUST be append-only and MUST NOT be edited.
2. Activity records MAY be editable only with explicit audit trails (e.g., message edit creates a new revision record).
3. Deleting activity records SHOULD be possible under retention policy, but:
   - deletions MUST be auditable
   - deletions MUST NOT break referential integrity (use tombstones where needed)

---

## 8) Logging, analytics, and exports

### 8.1 Logging
1. Logs MUST include correlation IDs and tenant identifiers.
2. Logs MUST NOT include HR data.
3. Logs SHOULD avoid R-PII; if included, must be masked.

### 8.2 Analytics / telemetry
1. Any analytics store MUST be treated as a derived system with strict minimization.
2. Tenant data MUST NOT be mixed without explicit aggregation boundaries and controls.
3. Raw document contents MUST NOT be exported to analytics by default.

### 8.3 Exports
1. Exports MUST respect permission scopes and classification rules.
2. Exports MUST be auditable:
   - who exported, what scope, when
3. Exports SHOULD support redacted modes for least privilege.

---

## 9) Governance enforcement points (where rules must be applied)

These are mandatory enforcement points:

1. API serialization (field-level redaction)
2. Document upload/download (access logging, signed URLs, classification tagging)
3. Integration ingestion (redaction before persistence where needed)
4. Worker job payloads (avoid embedding sensitive content)
5. Error reporting (strip payloads; store redacted traces)
6. Export tooling (permission-gated, audited)

---

## 10) Open items (to be resolved via specs/decisions)

1. Exact retention durations by category (AUD/ACT/ART/INTG)
2. Legal hold scope granularity (per Account vs per Engagement vs per Document)
3. Message edit/delete policy (whether allowed; if allowed, revision model)
4. Document classification UX and defaults (by type, by location, by template)

These must be resolved and recorded in DECISION_LOG.md and/or OPEN_QUESTIONS.md.

---

