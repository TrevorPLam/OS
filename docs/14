# Documents and Storage Specification (DOCUMENTS_AND_STORAGE_SPEC)

Defines governed documents, versioning, locking, signed URL policies, malware scanning hooks, and access logging.
Normative. If conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals
1. Documents MUST be governed artifacts (not unmanaged blobs).
2. The system MUST support versioning and (where required) locking.
3. Access MUST be permission-gated and logged.
4. Storage MUST be adapter-based (S3-compatible contract).

---

## 2) Core concepts

### 2.1 Document (logical artifact)
Fields:
- document_id
- title
- classification (DATA_GOVERNANCE)
- status (active | archived)
- created_by_actor
- created_at
- current_version_id (nullable)
- deleted_at (soft delete)

### 2.2 DocumentVersion (immutable revision)
Fields:
- document_version_id
- document_id
- version_number (monotonic per document)
- storage_key (object storage path)
- content_type
- size_bytes
- checksum (sha256)
- created_at, created_by_actor
- virus_scan_status (pending | clean | flagged | skipped)
- metadata (bounded)

Invariant:
- DocumentVersion MUST be immutable. New uploads create new versions.

### 2.3 DocumentLink (association)
Use the DOMAIN_MODEL.md linking layer.
Documents MUST be linked to the canonical object graph OR placed in an explicit triage bucket.

---

## 3) Storage adapter contract (S3-compatible)

Adapter MUST support:
- put_object (upload)
- get_object (download)
- head_object (metadata)
- delete_object (rare; only for lifecycle/hard delete workflows)
- generate_signed_url (upload/download)
- list_objects (optional; prefer DB metadata)

Signed URL generation MUST require an authorization decision first.

---

## 4) Signed URL policies (MUST)

1. URLs MUST be short-lived.
2. Upload URLs MUST be single-use semantics by policy (enforced by:
   - unique upload session ids, and/or
   - post-upload finalize step).
3. Download URLs MUST be scoped to a single object/version.
4. URL issuance MUST be logged (who, what, when, correlation id).
5. Portal downloads MUST enforce portal-visible rules from PERMISSIONS_MODEL.md.

---

## 5) Locking semantics

If locking is enabled for a document:
- DocumentLock fields:
  - document_id
  - locked_by_actor
  - locked_at
  - expires_at (optional)
  - lock_reason (optional)

Rules:
1. If locked, only the lock holder (or Admin override) may upload a new version.
2. Overrides MUST be auditable.
3. Locks SHOULD expire or require explicit release policy (choose and document).

---

## 6) Malware scanning hooks

1. The system MUST support a post-upload hook to scan new versions.
2. Until clean:
- downloads MAY be blocked for portal identities
- staff access may be restricted by policy
3. Scan results MUST be recorded on DocumentVersion and auditable.

---

## 7) Access logging requirements

Must log:
- document view/download
- version upload/finalize
- lock/unlock/override
- permission/share changes that affect visibility

Logs MUST include actor, tenant, object refs, timestamp, correlation id.

---

## 8) Triage / intake inbox

If documents arrive via portal upload or email ingestion:
- they MAY land in an “Intake Inbox” state
- require staff mapping/linking before being fully visible in the canonical graph
- mapping actions MUST be auditable

---

## 9) Testing requirements
- Version increment correctness
- Signed URL gating
- Portal visibility rules
- Lock enforcement and override auditing
- Scan hook invocation and policy behavior
- Access log completeness

---
