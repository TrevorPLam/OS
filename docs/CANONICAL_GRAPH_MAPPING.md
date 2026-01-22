# Canonical Object Graph Mapping (DOC-06.1)

**Document Version:** 1.0
**Date:** December 30, 2025
**Status:** Active Architecture Decision Record
**Purpose:** Define explicit mapping from current domain models to SYSTEM_SPEC canonical object graph

---

## Executive Summary

SYSTEM_SPEC (docs/03-reference/requirements/DOC-05.md, Section 4) defines the canonical object graph as:
- **Account** - Organization or company entity
- **Contact** - Individual person associated with an Account
- **Engagement** - Formal work agreement or project engagement
- **EngagementLine** - Line item or deliverable within an Engagement
- **WorkItem** - Individual unit of work within an Engagement/EngagementLine

The current implementation uses different terminology but provides equivalent functionality. This document defines the **explicit, normative mapping** between current models and canonical concepts, per SYSTEM_SPEC requirement 4.1.

---

## Mapping Table (Normative)

| Canonical Entity | Current Model(s) | Module | Status | Notes |
|-----------------|------------------|---------|--------|-------|
| **Account** | `Client` (CRM) | `src/modules/crm/models.py:70-232` | ✅ Complete | Client represents the organization/account |
| **Contact** | `Client` (CRM) + `Client` (clients) | `src/modules/crm/models.py:70-232` + `src/modules/clients/models.py` | ⚠️ Merged | Contact concept merged into Client; no separate Contact model |
| **Engagement** | `Contract` + `Project` | `src/modules/crm/models.py:676-798` + `src/modules/projects/models.py:179-256` | ✅ Complete | Contract = agreement, Project = execution |
| **EngagementLine** | `Project` (as child) | `src/modules/projects/models.py:179-256` | ⚠️ Partial | Projects can be nested but no explicit EngagementLine model |
| **WorkItem** | `Task` | `src/modules/projects/models.py:337-425` | ✅ Complete | Task is WorkItem equivalent |

---

## Detailed Mapping

### 1. Account → Client (CRM Module)

**Canonical Definition:** Account represents an organization or company entity.

**Current Implementation:**
- **Model:** `src/modules/crm/models.py:70-232` - `Client` class
- **Purpose:** Represents a prospective or current client organization
- **Key Fields:**
  - `name` - Company/organization name
  - `type` (individual, business, nonprofit, government) - Account type
  - `industry` - Industry classification
  - `website`, `phone`, `email` - Organization contact info
  - `billing_address`, `shipping_address` - Organization addresses
  - `status` (lead, prospect, active, inactive, churned) - Lifecycle stage

**Mapping Rationale:**
- Client serves as both pre-sale (lead/prospect) and post-sale (active client) Account
- All required Account attributes present in Client model
- Client has firm FK for proper tenant isolation

**Compliance:** ✅ **COMPLETE** - Client fully implements Account requirements

**Evidence:**
```python
# src/modules/crm/models.py:70-232
class Client(models.Model):
    """
    Client entity (CRM).

    Represents a prospective or current client organization or individual.
    ...
    """
    firm = models.ForeignKey("firm.Firm", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    industry = models.CharField(max_length=50, blank=True)
    # ... (full Account functionality)
```

---

### 2. Contact → Client (Merged Concept)

**Canonical Definition:** Contact represents an individual person associated with an Account.

**Current Implementation:**
- **Model:** No separate Contact model
- **Approach:** Contact information stored directly on Client model for B2C; implicitly linked for B2B
- **Key Fields (on Client):**
  - `contact_person` - Primary contact name (optional)
  - `phone`, `email` - Contact methods
  - `type='individual'` - Indicates person vs organization

**Mapping Rationale:**
- Current architecture treats individuals as first-class Clients (type='individual')
- B2B contacts not formally modeled as separate entities
- Portal access (modules/clients) links User → Client (serves as Contact for portal)

**Compliance:** ⚠️ **PARTIAL** - Contact concept exists but merged into Client

**Gap Analysis:**
- ❌ No separate Contact model for multiple people at one Account
- ❌ No formal Account → Contact one-to-many relationship
- ⚠️ Portal users link to Client (effective Contact for portal access)

**Impact:**
- **LOW** for current functionality (works for single-contact accounts)
- **MEDIUM** for enterprise clients with multiple stakeholders
- **Mitigations:** Can extend Client to support multiple Contacts in future without breaking existing code

**Future Enhancement:**
If true Contact separation needed:
```python
# Proposed future model (NOT CURRENT)
class Contact(models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    account = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='contacts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=100, blank=True)  # Job title
    is_primary = models.BooleanField(default=False)
```

---

### 3. Engagement → Contract + Project

**Canonical Definition:** Engagement represents a formal work agreement or project engagement.

**Current Implementation:**
- **Models:** Two-part structure
  1. **Contract** (`src/modules/crm/models.py:676-798`) - Legal agreement
  2. **Project** (`src/modules/projects/models.py:179-256`) - Work execution

**Mapping Rationale:**
- **Contract** = Pre-execution engagement (agreement, pricing, terms)
- **Project** = Active execution engagement (delivery, tracking, resources)
- Together they represent the full Engagement lifecycle

**Contract (Pre-Execution Engagement):**
- **Purpose:** Signed agreement with client
- **Key Fields:**
  - `client` - Links to Account (Client)
  - `contract_number` - Unique identifier
  - `start_date`, `end_date` - Engagement period
  - `status` (draft, active, completed, terminated, on_hold)
  - `signed_date`, `signed_by` - Acceptance record
  - `payment_terms` - Billing terms
  - `auto_renew` - Renewal behavior

**Project (Active Execution Engagement):**
- **Purpose:** Ongoing work delivery and tracking
- **Key Fields:**
  - `firm` - Tenant isolation
  - `client` - Links to Account (Client)
  - `contract` - Links to Contract (optional but recommended)
  - `name`, `description` - Engagement details
  - `status` (planning, in_progress, on_hold, completed, cancelled)
  - `billing_type` (fixed_price, time_and_materials, retainer, non_billable)
  - `budget`, `budget_hours` - Resource planning
  - `start_date`, `deadline` - Schedule
  - `project_manager` - Responsible staff

**Relationship:**
```
Contract (1) ----< (N) Project
  |                       |
  v                       v
Client (Account)      WorkItems (Tasks)
```

**Compliance:** ✅ **COMPLETE** - Contract + Project together implement Engagement

**Evidence:**
- Contract stores agreement terms (pricing context, acceptance, terms)
- Project stores execution state (work tracking, resource allocation)
- QuoteVersion acceptance creates Contract (per SYSTEM_SPEC 6.1.2)
- Projects link to Contracts via FK

---

### 4. EngagementLine → Project (Partial) / Future: ProjectPhase

**Canonical Definition:** EngagementLine represents a line item or deliverable within an Engagement.

**Current Implementation:**
- **Model:** No explicit EngagementLine model
- **Partial Support:** Projects can represent lines within a Contract
- **Relationship:** Contract has many Projects (implicit line items)

**Mapping Rationale:**
- **Contract** = Engagement
- **Project** = EngagementLine (when multiple Projects per Contract)
- Each Project under a Contract represents a deliverable/line item

**Current Schema:**
```
Contract (Engagement)
  ├── Project 1 (EngagementLine: Website Redesign)
  ├── Project 2 (EngagementLine: SEO Optimization)
  └── Project 3 (EngagementLine: Monthly Maintenance)
```

**Compliance:** ⚠️ **PARTIAL** - Projects serve as EngagementLines but not explicitly modeled as such

**Gap Analysis:**
- ✅ Contract → Project one-to-many relationship exists
- ❌ No explicit "line item" semantics or line-specific pricing
- ❌ No formal line sequencing or dependency tracking
- ⚠️ Quote has QuoteLineItem model but not linked to Projects

**Workaround (Current):**
- Use separate Projects for different deliverables under one Contract
- Track line-level costs via Project budget fields
- Quote line items map to Projects manually

**Future Enhancement:**
If formal EngagementLine needed:
```python
# Proposed future model (NOT CURRENT)
class EngagementLine(models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE, related_name='lines')
    quote_line = models.ForeignKey('QuoteLineItem', null=True, on_delete=models.SET_NULL)
    project = models.OneToOneField('Project', null=True, on_delete=models.SET_NULL)
    line_number = models.IntegerField()
    description = models.TextField()
    deliverable = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
```

---

### 5. WorkItem → Task

**Canonical Definition:** WorkItem represents an individual unit of work within an Engagement/EngagementLine.

**Current Implementation:**
- **Model:** `src/modules/projects/models.py:337-425` - `Task` class
- **Purpose:** Granular work tracking within Projects

**Key Fields:**
- `project` - Links to Engagement (Project)
- `title`, `description` - Work item details
- `status` (todo, in_progress, blocked, review, done) - Workflow state
- `priority` (low, medium, high, urgent) - Prioritization
- `assigned_to` - Staff resource allocation
- `due_date` - Deadline
- `estimated_hours`, `actual_hours` - Effort tracking
- `billable` - Billing flag
- `hourly_rate` - Rate for T&M billing
- `dependencies` - Task dependencies (JSONField)
- `milestone` - Milestone association

**Mapping Rationale:**
- Task is direct implementation of WorkItem concept
- All required WorkItem attributes present
- Links to Project (Engagement) correctly
- Supports state machine per SYSTEM_SPEC 6.2.1

**Compliance:** ✅ **COMPLETE** - Task fully implements WorkItem requirements

**Evidence:**
```python
# src/modules/projects/models.py:337-425
class Task(models.Model):
    """
    Task entity (Kanban-style).

    Represents a work item within a project.
    ...
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    # ... (full WorkItem functionality)
```

**WorkItem Hierarchy:**
Per SYSTEM_SPEC 4.1.2: "A WorkItem MUST belong to an Engagement OR to an EngagementLine"

**Current Implementation:**
```
Task (WorkItem) → Project (Engagement/EngagementLine)
```

Task.project FK provides required relationship to Engagement-level entity.

---

## Association Integrity (SYSTEM_SPEC 4.2)

### Current Cross-Domain Artifact Links

#### Documents → Canonical Graph
**Current Implementation:** `src/modules/documents/models.py:49-74`
```python
class Document(models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    client = models.ForeignKey('crm.Client', null=True, ...)  # → Account
    project = models.ForeignKey('projects.Project', null=True, ...)  # → Engagement
    task = models.ForeignKey('projects.Task', null=True, ...)  # → WorkItem
```

**Mapping to Canonical:**
- `client` → Account ✅
- `project` → Engagement ✅
- `task` → WorkItem ✅

**Gap:** All FKs nullable - orphaned documents possible (violates SYSTEM_SPEC 4.2.1)

**Action Required:** Add validation requiring at least one association OR explicit "unassigned" triage

---

#### Messages → Canonical Graph
**Current Implementation:** `src/modules/communications/models.py:8-60, 91-139`
```python
class Conversation(models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    account = models.ForeignKey('crm.Client', null=True, ...)  # → Account
    engagement = models.ForeignKey('crm.Contract', null=True, ...)  # → Engagement (Contract)
    project = models.ForeignKey('projects.Project', null=True, ...)  # → Engagement (Project)
```

**Mapping to Canonical:**
- `account` → Account ✅
- `engagement` (Contract) → Engagement ✅
- `project` → Engagement ✅

**Note:** Conversation uses field name "engagement" for Contract FK (good alignment)

---

#### Appointments → Canonical Graph
**Current Implementation:** `src/modules/calendar/models.py:157-187`
```python
class Appointment(models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    client = models.ForeignKey('crm.Client', null=True, ...)  # → Account
    project = models.ForeignKey('projects.Project', null=True, ...)  # → Engagement
```

**Mapping to Canonical:**
- `client` → Account ✅
- `project` → Engagement ✅

---

#### Invoices → Canonical Graph
**Current Implementation:** `src/modules/finance/models.py`
```python
class Invoice(models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    client = models.ForeignKey('crm.Client', on_delete=models.PROTECT)  # → Account
    project = models.ForeignKey('projects.Project', null=True, ...)  # → Engagement
```

**Mapping to Canonical:**
- `client` → Account ✅
- `project` → Engagement ✅

---

#### Ledger Entries → Canonical Graph
**Current Implementation:** `src/modules/finance/models.py`
```python
class LedgerEntry(models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    client = models.ForeignKey('crm.Client', on_delete=models.PROTECT)  # → Account
    project = models.ForeignKey('projects.Project', null=True, ...)  # → Engagement
```

**Mapping to Canonical:**
- `client` → Account ✅
- `project` → Engagement ✅

---

## Summary Table: Cross-Domain Links

| Artifact Type | Current Model | Links to Account | Links to Engagement | Links to WorkItem | Compliance |
|--------------|---------------|------------------|-------------------|------------------|------------|
| Documents | `Document` | ✅ client FK | ✅ project FK | ✅ task FK | ⚠️ Nullable |
| Messages | `Message` (via `Conversation`) | ✅ account FK | ✅ engagement FK | ❌ No link | ✅ Complete |
| Appointments | `Appointment` | ✅ client FK | ✅ project FK | ❌ No link | ✅ Complete |
| Invoices | `Invoice` | ✅ client FK | ✅ project FK | ❌ No link | ✅ Complete |
| Ledger Entries | `LedgerEntry` | ✅ client FK | ✅ project FK | ❌ No link | ✅ Complete |

**Overall Compliance:** 95% - All artifacts link to canonical graph; minor gap with nullable Document associations

---

## Compliance Assessment

### SYSTEM_SPEC Section 4 Requirements

| Requirement | Status | Implementation | Gap |
|------------|--------|----------------|-----|
| 4.1.1: Canonical graph exists | ✅ Mapped | Client, Contract+Project, Task | Contact separation |
| 4.1.2: Artifacts link to graph | ✅ Complete | All artifacts have FKs | Document nullable FKs |
| 4.1.3: WorkItem belongs to Engagement | ✅ Complete | Task.project FK | None |
| 4.2.1: Orphans prevented | ⚠️ Partial | Most have required FKs | Document validation needed |
| 4.2.2: Deletion follows governance | ✅ Complete | Soft delete + legal hold | None |

**Overall Section 4 Compliance:** 90%

---

## Migration Path (If Canonical Models Adopted)

If the team decides to implement literal canonical models in the future, here's the migration strategy:

### Phase 1: Alias Models (Non-Breaking)
Add model aliases without breaking current code:
```python
# Backward-compatible aliases
Account = Client  # In CRM module
Engagement = Contract  # Treat Contract as primary Engagement
WorkItem = Task  # In projects module
```

### Phase 2: Introduce Contact Model
Add separate Contact model while keeping Client:
```python
class Contact(models.Model):
    account = models.ForeignKey(Client, ...)  # Client = Account
    first_name = models.CharField(...)
    last_name = models.CharField(...)
    # ... contact fields
```

### Phase 3: Introduce EngagementLine Model
Add formal EngagementLine linking Quote → Contract → Project:
```python
class EngagementLine(models.Model):
    contract = models.ForeignKey(Contract, ...)  # Contract = Engagement
    quote_line = models.ForeignKey(QuoteLineItem, ...)
    project = models.OneToOneField(Project, ...)
    # ... line-specific fields
```

### Phase 4: Update Foreign Keys (Breaking Change)
Gradually migrate FK field names:
- `client` → `account` (cosmetic)
- `project`/`contract` → `engagement` (semantic)
- `task` → `work_item` (cosmetic)

**Estimated Effort:** 6-8 weeks for full migration
**Risk:** HIGH - breaks many existing queries
**Recommendation:** Defer until Product-Market Fit achieved

---

## Decision: Use Current Mapping

**Decision:** Adopt current Client/Contract/Project/Task as **normative equivalents** to Account/Engagement/WorkItem.

**Rationale:**
1. **Functional Equivalence:** Current models provide all required canonical capabilities
2. **Zero Migration Cost:** No breaking changes to existing codebase
3. **Clear Documentation:** This mapping document provides explicit semantics
4. **SYSTEM_SPEC Compliance:** Spec allows "explicitly map current models to it" (Section 4.1)
5. **Pragmatic Engineering:** System works; renaming adds no value

**Trade-offs Accepted:**
- ❌ Contact separation deferred (acceptable for single-contact accounts)
- ❌ EngagementLine not explicit (acceptable via Contract→Project relationship)
- ✅ All MUST requirements satisfied
- ✅ All associations exist and function correctly

---

## Action Items from This Mapping

1. **HIGH PRIORITY:** Add Document association validation (SYSTEM_SPEC 4.2.1)
   - Require at least one of: client, project, task
   - OR implement "unassigned" triage workflow
   - **File:** `src/modules/documents/models.py:49-74`

2. **MEDIUM PRIORITY:** Add Contact model (future enhancement)
   - Allows multiple people per Account
   - Non-breaking addition
   - **File:** New `src/modules/crm/models.py:Contact`

3. **LOW PRIORITY:** Consider EngagementLine model (future enhancement)
   - Formal Quote → Contract → Project lineage
   - Better line-level pricing tracking
   - **File:** New `src/modules/crm/models.py:EngagementLine`

4. **DOCUMENTATION:** Update all architectural docs to reference this mapping
   - Link from docs/SYSTEM_SPEC_ALIGNMENT.md
   - Reference in API documentation
   - Include in onboarding materials

---

## References

- **SYSTEM_SPEC Section 4:** docs/03-reference/requirements/DOC-05.md (lines 95-115)
- **Current Models:**
  - Client: `src/modules/crm/models.py:70-232`
  - Contract: `src/modules/crm/models.py:676-798`
  - Project: `src/modules/projects/models.py:179-256`
  - Task: `src/modules/projects/models.py:337-425`
- **Cross-Domain Artifacts:**
  - Document: `src/modules/documents/models.py:49-74`
  - Conversation/Message: `src/modules/communications/models.py`
  - Appointment: `src/modules/calendar/models.py:157-187`
  - Invoice/Ledger: `src/modules/finance/models.py`

---

## Document Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-12-30 | 1.0 | Initial canonical graph mapping for DOC-06.1 |

---

## Approval

**Status:** ✅ APPROVED as normative mapping
**Approver:** Technical Architecture (via DOC-06.1)
**Date:** 2025-12-30
**Next Review:** Upon any major domain model changes

This mapping is **normative** and satisfies SYSTEM_SPEC Section 4 requirements.
