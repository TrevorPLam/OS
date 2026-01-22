# Email Ingestion Specification (EMAIL_INGESTION_SPEC)

Defines ingestion of email (Gmail/Outlook), storage of artifacts and attachments, mapping suggestions, confidence scoring, staleness heuristics, correction workflows, and audit requirements.

Normative. If conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals
1. Ingested emails and attachments MUST become governed artifacts.
2. Ingestion MUST be idempotent and retry-safe.
3. The system MUST suggest mappings (Account/Engagement/WorkItem) with confidence and allow correction with audit.
4. The system MUST handle staleness and threading ambiguity explicitly.

---

## 2) Core concepts

### 2.1 EmailArtifact
Represents an ingested email message.

Fields:
- email_artifact_id
- provider (gmail | outlook | other)
- connection_id
- external_message_id (required; unique per connection)
- thread_id (nullable; provider thread/conversation id)
- from_address, to_addresses, cc_addresses (governed; R-PII)
- subject (governed)
- sent_at, received_at
- body_preview (bounded)
- storage_ref (optional: full MIME stored as a document/artifact)
- status (ingested | mapped | triage | ignored)
- created_at

Uniqueness:
- (connection_id, external_message_id) MUST be unique.

### 2.2 Attachment handling
Each attachment MUST be stored as a Document/DocumentVersion under DOCUMENTS_AND_STORAGE_SPEC.md.
Attachments MUST link back to the EmailArtifact and then to domain objects via DocumentLink once mapped.

### 2.3 IngestionAttempt / SyncAttemptLog
Record every attempt:
- attempt_id
- email_artifact_id (nullable if failed before create)
- connection_id
- operation (fetch | parse | store | map)
- status (success | fail)
- error_summary (redacted)
- occurred_at
- correlation_id

---

## 3) Mapping suggestions

The system SHOULD attempt to map an email to:
- Account (highest priority)
- Engagement
- WorkItem (if strongly indicated)

Mapping signals (examples):
- sender/recipient domain matching known contacts
- subject keywords / engagement codes
- prior thread mappings
- explicit tags (if supported)
- attachment names (weak signal)

Suggestion output MUST include:
- candidate object refs
- confidence score (0–1)
- reasons (human-readable)
- required action (auto-map vs needs review)

Auto-map MUST only occur above a strict threshold and must be auditable.

---

## 4) Staleness heuristic and triage rules

Staleness applies when:
- contact email matches multiple accounts
- thread contains mixed clients
- subject changes across threads
- the last confident mapping is older than a threshold (configurable)

Rules:
1. If confidence is low or ambiguity exists, place in Triage.
2. Triage items MUST be reviewable and re-mappable.
3. Mapping changes MUST create audit events.

---

## 5) Correction workflow

Required operations:
- remap email to a different Account/Engagement/WorkItem
- add/remove attachment links
- mark ignored (with reason)

Constraints:
- Corrections MUST NOT delete the underlying artifact.
- Corrections MUST be auditable (before/after, who, when).

---

## 6) Permissions
- Only staff with appropriate roles can view triage and remap.
- Portal identities MUST NOT see raw ingested emails unless explicitly converted into a portal-visible conversation artifact (policy decision; default: no).

---

## 7) Testing requirements
- idempotent ingestion on retries
- attachment storage + linking
- mapping suggestion determinism (given same data)
- triage behavior for ambiguous cases
- audit event generation for remaps

---
