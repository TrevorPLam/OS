# Knowledge System Specification (KNOWLEDGE_SYSTEM_SPEC)

Defines the internal knowledge module: SOPs, training manuals, KPI definitions, and governance (versioning, publishing, access control).

Normative for module behavior. Knowledge items are governed artifacts; documents may be stored using the document system.

---

## 1) Goals
1. Provide a centralized, firm-owned knowledge base (SOPs, training, KPIs).
2. Support versioning, publishing workflows, and deprecation.
3. Enforce role-based access (some knowledge is restricted).
4. Support discoverability (search, tagging) and operational linking to work.

---

## 2) Core concepts

### 2.1 KnowledgeItem
Represents an article/manual/SOP/KPI definition.

Fields (conceptual):
- knowledge_item_id
- type (SOP | training | KPI | playbook | template)
- title
- summary
- content_format (markdown | rich_text)
- status (draft | published | deprecated | archived)
- version_number
- owner_staff_user_id
- reviewers (optional)
- tags
- created_at, updated_at
- published_at (nullable)
- deprecated_at (nullable)

Invariants:
- Published versions SHOULD be immutable; changes create a new version.
- Deprecation must retain history.

### 2.2 KnowledgeVersion (optional explicit model)
If you want explicit version records:
- knowledge_version_id
- knowledge_item_id
- version_number
- content_snapshot
- change_notes
- created_at, created_by_actor

### 2.3 Attachments and references
Knowledge can reference:
- Documents (policies, PDFs)
- Templates (DeliveryTemplates)
- Metrics definitions
- External links (allowed list policy)

Attachments should be Documents in the governed document system.

---

## 3) Publishing workflow

1. Draft created by an owner.
2. Optional review step:
- reviewer approves
- approval recorded in audit log
3. Publish:
- locks version
- makes item visible per access policy
4. Deprecate:
- item remains searchable but marked deprecated
- deprecation reason required
5. Archive:
- hidden from default views but retained

All transitions MUST be auditable.

---

## 4) Access control

Default:
- Knowledge is staff-only.
- Some categories may be restricted to Admin/Manager (e.g., security SOPs, HR policies).

Rules:
1. Viewing requires role permission.
2. Editing requires owner or elevated role.
3. Publishing/deprecating requires elevated role (Manager/Admin) or explicit permission.

---

## 5) Information architecture

Recommended sections:
- SOP Library
- Training
- KPI Definitions
- Playbooks
- Templates & Checklists

Each section supports:
- tags
- search
- filters (status, owner, updated date)

---

## 6) Operational linking

Knowledge should link into operations:
- WorkItem can reference a KnowledgeItem (“Run SOP-###”)
- Templates can reference KnowledgeItem (“This template implements SOP-###”)
- Recurrence rules can reference KnowledgeItem (optional)

These links improve execution consistency and reduce tribal knowledge.

---

## 7) Testing requirements
- versioning and immutability rules
- publish/deprecate transitions and audit events
- role-based access enforcement
- search indexing and visibility (published vs draft)

---
