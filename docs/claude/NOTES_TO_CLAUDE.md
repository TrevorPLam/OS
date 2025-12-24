# NOTES TO CLAUDE (AUTHORITATIVE)

## Purpose

This document is authoritative. If code conflicts with these rules, code must change unless the system owner explicitly revises this document.

---

## Platform & Tenancy Model

* The system is a multi-firm SaaS.
* Firm is the top-level tenant boundary.
* Client belongs to exactly one Firm.
* Portal users belong to a Client.
* Organizations are optional context/grouping; not a security boundary.
* Cross-client interaction is allowed only within the same Organization.

### Firm Context Resolution (Explicit)

Every request must resolve an active Firm context using a combination of:

* URL/subdomain (preferred where available)
* user-selected firm (session state)
* token/session claims

No operation may proceed without a resolved Firm context.

---

## Privacy & Platform Access

* Platform staff cannot read customer content by default:
  * documents
  * messages
  * comments
  * notes
  * invoice line items
* Customer content is end-to-end encrypted.
* Platform retains liability metadata only:
  * billing totals and subscription records
  * payment processor events
  * auth and authorization logs
  * break-glass audit records
  * operational metadata (counts, timestamps, error traces)

### Break-Glass Access (Explicit)

* Exists for support/emergencies only.
* Triggered by firm consent OR predefined emergency policy.
* Requires:
  * explicit activation
  * reason string
  * time limit
  * immutable audit log
* Includes impersonation safeguards:
  * clear "impersonation mode" indicator
  * automatic expiry
  * explicit logging of all actions taken
* Not visible to firms by default.

---

## Roles

### Platform

* Platform Operator: metadata-only access
* Break-Glass Operator: rare, audited content access

### Firm

* Firm Master Admin (Owner): full control, overrides
* Firm Admin: granular permissions
* Staff: least privilege, permissions enabled explicitly

### Client

* Portal Users: client-scoped access only

---

## Engagements (Agreements)

* Engagement defines scope and pricing (package, hourly, or both).
* Once SIGNED, engagement is immutable.
* Changes occur via new draft engagement (renewal/update).
* Renewals create new engagement records.
* Clients can view current and historical engagements.

---

## Projects & Tasks (Work)

* Projects always belong to a Client.
* Projects may optionally reference the Engagement that created them.
* Engagement confirmation may create projects/tasks:
  * never duplicates
  * never deletes existing work
* Clients can:
  * view projects/tasks
  * comment
  * upload documents
  * mark client-actionable tasks complete
* Client task completion updates firm workflow state.

---

## Documents (Single Source of Truth)

* All files live in Documents module (canonical).
* Other modules link to documents; no duplicate storage.
* Documents are always client-scoped.
* Documents may be associated to:
  * client-general
  * engagement
  * project
  * task
* Deleting/archiving a project/task must not delete documents.

### Portal Folder Rules

* Client Folder:
  * Firm: CRUD
  * Client: read/download
* Upload Folder:
  * Client: CRUD
  * Firm: CRUD

### Document Signing (Explicit)

* Signing events are immutable.
* Signature evidence must be retained even if document content is purged.
* Signing metadata (who, when, version) must remain auditable.

---

## Communications

* Messages and comments are immutable.
* No edits or deletes by firm or clients.
* Master Admin may purge content only if legally required:
  * content removed
  * metadata preserved (tombstone)
  * action logged with reason

---

## Billing & Payments

* Invoice belongs to a Client.
* Default: invoice links to an Engagement (Master Admin can override).
* Invoices may optionally link to Projects.
* Billing supports:
  * package fees (auto-invoiced)
  * hourly fees (approved by staff/admin)
  * mixed invoices
* Recurring payments auto-pay invoices as issued.
* Credits (if enabled) are tracked via a ledger.

### Payment Exceptions (Explicit)

* Payment failures, disputes, and chargebacks must be tracked as first-class events.
* Platform retains dispute metadata but not billing context/content.

---

## Deletion & Audit

* Soft delete/archive by default across client-facing records.
* Hard delete/purge:
  * Master Admin only
  * explicit confirmation
  * reason required
  * fully logged
* History must remain visible unless legally purged.

### Audit Governance (Explicit)

* Audit events must be categorized (auth, billing, break-glass, purge).
* Logs must have defined retention windows.
* Ownership of audit review (who reviews, how often) must be defined.

---

## CI & Correctness

* CI must be truthful.
* No skipped checks that claim enforcement.
* If lint/build/tests exist, failures must fail CI.

---

## Expectations for Claude

* Enforce firm + client scoping everywhere.
* Default-deny for portal users.
* Never introduce unscoped querysets.
* Always cite exact file targets.
* Prefer small, verifiable diffs.
* Stop and ask if rules are ambiguous.
