# Communications Specification (COMMUNICATIONS_SPEC)

Defines native chat/messaging for staff↔staff and staff↔client, thread models, message types, attachment handling, email integration boundaries, retention, and audit requirements.

Normative. If conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals
1. Communications MUST be in-context with the canonical object graph.
2. Staff↔staff and staff↔client messaging MUST be supported.
3. Attachments MUST be governed Documents (DOCUMENTS_AND_STORAGE_SPEC.md).
4. Access MUST be permission-gated and auditable.
5. Email integration MUST ingest artifacts without making email the authoritative conversation model.

---

## 2) Core concepts

### 2.1 Conversation (thread)
A Conversation is a thread of messages. Conversations can be:
- internal_only (staff participants only)
- client_visible (includes portal participants)

Fields (conceptual):
- conversation_id
- visibility (internal_only | client_visible)
- subject (optional)
- created_at
- created_by_actor
- status (active | archived)
- last_message_at
- primary_anchor (optional: object_type/object_id)
- correlation_id (creation)

Conversations MUST be linked to the domain via ConversationLink (DOMAIN_MODEL.md).

### 2.2 Participants
Participants are either:
- StaffUser
- PortalIdentity (mapped to Contact)

Fields:
- conversation_id
- participant_type (staff | portal)
- participant_id
- role (member | owner | moderator; optional)
- joined_at
- left_at (nullable)

Invariants:
- internal_only conversations MUST NOT include portal participants.
- client_visible conversations MAY include staff and portal participants.
- Adding/removing participants MUST be permission-gated and auditable.

### 2.3 Message
Fields (conceptual):
- message_id
- conversation_id
- sender_actor_type (staff | portal | system)
- sender_actor_id (nullable for system)
- message_type (text | system_event | attachment | action)
- body (bounded; may be empty for attachment-only)
- created_at
- edited_at (optional; if edits allowed)
- deleted_at (optional; if deletes allowed)
- metadata (bounded; e.g., mentions)
- correlation_id

Invariants:
- Messages are append-only by default. If edits/deletes exist, they MUST preserve history (see Section 7).

### 2.4 Attachments
Attachments MUST be Documents.
Linking options:
- MessageAttachment(message_id, document_id)
- Or store document links with role=attachment and include message reference metadata

Constraints:
- A portal user upload as an attachment MUST route through governed upload flow (signed URL + scan hooks).
- Attachment visibility MUST match conversation visibility and document portal-shareable rules.

---

## 3) Thread types and creation rules

### 3.1 Client thread (recommended pattern)
For each Account, the system SHOULD support a default “Client Messages” conversation that:
- is client_visible
- includes allowed portal identities for that Account
- includes assigned staff members or a role-based staff group

Creation:
- MAY be auto-created when portal access is granted
- or created on first message

### 3.2 Internal thread
Internal threads support:
- staff coordination
- sensitive notes that must never be visible to clients

Internal threads MUST be clearly labeled in UI and enforced server-side.

---

## 4) Context linking rules

1. Conversations MUST be linkable to:
- Account
- Engagement
- EngagementLine
- WorkItem
- Invoice
- Appointment

2. A conversation MAY have multiple links (ConversationLink) but SHOULD have one primary anchor for UI context.

3. Linking/unlinking MUST be auditable.

---

## 5) Permissions (communications)

Staff:
- can create internal and client-visible conversations if role permits
- can message in any conversation they are a participant in
- can add/remove participants only with elevated permissions (e.g., Manager/Admin)

Portal:
- can only access client_visible conversations scoped to granted Accounts
- can only message within those conversations
- cannot add/remove participants unless explicitly allowed (default: no)

All read/mutation enforcement MUST be server-side per PERMISSIONS_MODEL.md.

---

## 6) Email integration boundary

Email is handled via EMAIL_INGESTION_SPEC.md and MUST NOT become the authoritative thread model by default.

Rules:
1. Ingested emails become EmailArtifacts and Documents (attachments) with mapping suggestions.
2. The system MAY provide “Create conversation from email” as a staff action that:
- creates a client_visible or internal conversation
- posts a system_event message referencing the email artifact
- links attachments as governed documents
3. Auto-posting ingested emails into conversations SHOULD be off by default unless a strong mapping policy exists (to avoid cross-client leakage).

---

## 7) Retention, edits, deletes, and audit

### 7.1 Retention classes
- Client-visible messages (CONF)
- Internal messages (CONF, possibly more sensitive)
Retention durations are governed by DATA_GOVERNANCE.md.

### 7.2 Edits/deletes (policy)
Default recommendation:
- Allow edits within a short window; preserve revision history.
- Allow deletes only as soft delete; preserve tombstone and audit record.

If edits are allowed:
- store MessageRevision records:
  - message_id
  - revision_number
  - body snapshot
  - edited_at
  - edited_by_actor

All edits/deletes MUST be auditable.

---

## 8) Notifications
The system SHOULD support:
- mentions (@user)
- assignment notifications when a message triggers a work item
- client message alerts
- escalation when no response within SLA (optional)

Notification dispatch MUST be idempotent.

---

## 9) Testing requirements
- portal cannot access internal threads (IDOR tests)
- participant add/remove permission checks
- attachment upload/download permission checks
- audit events on participant changes and mapping actions
- email-to-conversation conversion correctness
- retention policies honored

---

