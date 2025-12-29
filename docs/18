# API Contracts (API_CONTRACTS)

Defines endpoint groups per domain, auth/permission patterns, event emission patterns, and list/pagination conventions.

Blueprint. This document is normative for API consistency; domain rules remain in SYSTEM_SPEC/DOMAIN_MODEL.

---

## 1) API principles
1. All endpoints MUST enforce permissions server-side (PERMISSIONS_MODEL.md).
2. Mutations MUST be idempotent where side effects occur (idempotency key header or body).
3. Pagination, filtering, sorting MUST follow consistent conventions.

---

## 2) Conventions

Auth:
- Staff: bearer token; includes staff identity + roles
- Portal: bearer token; includes portal identity + account scope grants

Headers (recommended):
- X-Tenant-Id (if not derivable)
- X-Idempotency-Key (for side-effecting mutations)
- X-Correlation-Id (optional; otherwise generated)

Pagination:
- cursor-based preferred
- query params: `limit`, `cursor`
Filtering:
- `filter[field]=value`
Sorting:
- `sort=field` or `sort=-field`

Errors:
- stable error codes
- error_class aligns with orchestration retry matrix where relevant

---

## 3) Domain endpoint groups (minimum)

CRM
- /accounts (list/create/read/update)
- /contacts (list/create/read/update)
- /deals (pipeline inside CRM)

Engagements
- /engagements (draft/activate/pause/cancel/complete)
- /engagement-lines

Work
- /work-items (create/update/transition/assign)
- /delivery-templates (create/validate/publish/instantiate)

Pricing
- /pricing/evaluate
- /quotes (draft/issue)
- /quote-versions (read/accept)

Documents
- /documents (create metadata)
- /documents/{id}/versions (create)
- /documents/{id}/lock (lock/unlock)
- /documents/{id}/signed-url (upload/download)
- /upload-requests

Communications
- /conversations (create/list)
- /messages (send)
- /attachments (link documents)

Calendar
- /appointments (create/update/cancel)
- /calendar/connections (admin)
- /calendar/sync (admin tooling endpoints)

Billing
- /invoices (draft/issue/void)
- /payments (post)
- /retainers (deposit/apply)
- /ledger (restricted read)

Automation
- /orchestrations (create/status/retry/cancel)
- /recurrence (rules/generate/backfill)

Admin
- /roles, /users, /portal-grants
- /audit (restricted)
- /governance (retention/legal hold)

---

## 4) Event emission patterns (optional but recommended)
If events are used:
- emit domain events on state transitions and postings
- include correlation_id and tenant_id
- document event catalog (optional file)

---

