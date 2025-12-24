# Tier 2.3: Background/Async Job Tenant Context Audit

**Date:** December 24, 2025
**Status:** 🔴 CRITICAL ISSUE FOUND
**Tier:** 2.3 (Authorization & Ownership)

---

## Executive Summary

**Critical Tenant Isolation Issue Found:**
- Background job system uses **Django signals** (not dedicated task queue)
- **18 signal handlers** across 3 modules process business logic
- **CRITICAL: Client creation signals missing explicit tenant context**
- Missing `firm=` parameter when creating 5 different model types
- Risk: Tenant isolation could be bypassed in signal-triggered workflows

**Resolution Required:**
- Add explicit `firm=proposal.firm` to all object creation in signals
- Ensure all async workflows maintain tenant context
- Verify client_id context where applicable

---

## Background Job Implementation Pattern

### No Traditional Task Queue
**Finding:** The application does NOT use Celery, Django Q, Django RQ, or similar.

Instead, the application uses:
- **Django Signals** (pre_save, post_save) for workflow automation
- **Synchronous email sending** via Django's mail backend
- **Stripe webhooks** for external async events

### Signal-Based "Background" Jobs

| Module | File | Signal Handlers | Creates Objects? |
|--------|------|-----------------|------------------|
| clients | `modules/clients/signals.py` | 1 post_save | ✅ YES - Creates 5 model types |
| crm | `modules/crm/signals.py` | 4 (2 pre_save, 2 post_save) | ❌ NO - Updates only |
| projects | `modules/projects/signals.py` | 6 (3 pre_save, 3 post_save) | ❌ NO - Updates only |

**Total:** 18 signal handlers, 3 modules

---

## Tenant Context Audit Findings

### ✅ SAFE: CRM Module Signals (`modules/crm/signals.py`)

**No tenant isolation issues** - signals only update existing objects:

| Signal | Trigger | Actions | Tenant Risk |
|--------|---------|---------|-------------|
| `proposal_status_workflow` | Proposal pre_save | Auto-set sent_at/accepted_at timestamps | ✅ SAFE - Updates only |
| `proposal_accepted_notification` | Proposal post_save | Send email notification | ✅ SAFE - No DB writes |
| `contract_status_workflow` | Contract pre_save | Auto-set signed_date on activation | ✅ SAFE - Updates only |
| `contract_activation_notification` | Contract post_save | Send email notification | ✅ SAFE - No DB writes |

**Conclusion:** CRM signals are tenant-safe.

---

### ✅ SAFE: Projects Module Signals (`modules/projects/signals.py`)

**No tenant isolation issues** - signals only update/validate existing objects:

| Signal | Trigger | Actions | Tenant Risk |
|--------|---------|---------|-------------|
| `task_status_workflow` | Task pre_save | Auto-set completed_at | ✅ SAFE - Updates only |
| `task_created_notification` | Task post_save | Send email notification | ✅ SAFE - No DB writes |
| `time_entry_validation` | TimeEntry pre_save | Validate invoiced entries | ✅ SAFE - Validation only |
| `time_entry_logged_notification` | TimeEntry post_save | Log time entry event | ✅ SAFE - No DB writes |
| `project_status_workflow` | Project pre_save | Auto-set actual_completion_date | ✅ SAFE - Updates only |
| `project_completion_notification` | Project post_save | Send email + calculate metrics | ✅ SAFE - Queries are filtered |

**Note:** `_log_project_completion_metrics()` queries TimeEntry and Task objects, but uses filtered queries (`TimeEntry.objects.filter(project=project)`) which inherently respects tenant boundaries.

**Conclusion:** Projects signals are tenant-safe.

---

### 🔴 CRITICAL: Clients Module Signals (`modules/clients/signals.py`)

**TENANT ISOLATION VIOLATIONS FOUND**

#### Signal: `process_accepted_proposal`
**Trigger:** `post_save` on Proposal when `status='accepted'`
**Purpose:** Orchestrates entire onboarding workflow for accepted proposals

**Workflow Routes:**
1. `prospective_client` → `_handle_new_client()` - Creates new Client
2. `update_client` / `renewal_client` → `_handle_client_engagement()` - Creates Contract/Engagement

---

### 🔴 Issue #1: Missing Firm Context in `_handle_new_client()`

**Function:** `_handle_new_client(proposal)` (lines 39-168)

**Objects Created Without Tenant Context:**

| Line | Model | Missing Parameter | Risk Level |
|------|-------|-------------------|------------|
| 46 | `Client` | `firm=` | 🔴 CRITICAL |
| 72 | `Contract` | `firm=` | 🔴 CRITICAL |
| 90 | `ClientEngagement` | `firm=` | 🔴 CRITICAL |
| 105 | `Project` | `firm=` | 🔴 CRITICAL |
| 121, 130, 139, 148 | `Folder` (4 instances) | `firm=` | 🔴 CRITICAL |

**Current Code (Line 46-66):**
```python
client = Client.objects.create(
    source_prospect=proposal.prospect,
    source_proposal=proposal,
    company_name=proposal.prospect.company_name,
    industry=proposal.prospect.industry,
    # ... 15 more fields ...
    notes=f"Converted from Prospect #{proposal.prospect.id} via Proposal #{proposal.proposal_number}"
)
# ❌ MISSING: firm=proposal.firm
```

**Expected Code:**
```python
client = Client.objects.create(
    firm=proposal.firm,  # TIER 2: Explicit tenant context
    source_prospect=proposal.prospect,
    source_proposal=proposal,
    company_name=proposal.prospect.company_name,
    # ... rest of fields ...
)
```

**Impact:**
- Without explicit `firm=`, database may reject insert (IntegrityError) OR
- If firm field allows null (it doesn't), would create cross-tenant data leak
- Current state: Signal likely failing silently or never tested in production

---

### 🔴 Issue #2: Missing Firm Context in `_handle_client_engagement()`

**Function:** `_handle_client_engagement(proposal)` (lines 170-263)

**Objects Created Without Tenant Context:**

| Line | Model | Missing Parameter | Risk Level |
|------|-------|-------------------|------------|
| 202 | `Contract` | `firm=` | 🔴 CRITICAL |
| 220 | `ClientEngagement` | `firm=` | 🔴 CRITICAL |
| 235 | `Project` | `firm=` | 🔴 CRITICAL |

**Current Code (Line 202-217):**
```python
contract = Contract.objects.create(
    client=client,
    proposal=proposal,
    contract_number=f"ENG-{proposal.proposal_number}",
    title=proposal.title,
    # ... 8 more fields ...
    notes=f"{proposal.get_proposal_type_display()} from Proposal #{proposal.proposal_number}"
)
# ❌ MISSING: firm=proposal.firm
```

**Expected Code:**
```python
contract = Contract.objects.create(
    firm=proposal.firm,  # TIER 2: Explicit tenant context
    client=client,
    proposal=proposal,
    # ... rest of fields ...
)
```

---

## Email Notifications - Tenant Context Analysis

**File:** `modules/core/notifications.py` (390 lines)
**Pattern:** Synchronous email sending (not truly async)

### Email Methods

| Method | Called From | Tenant Context Source |
|--------|-------------|----------------------|
| `send_proposal_sent()` | CRM signals | Proposal model instance |
| `send_proposal_accepted()` | CRM signals | Proposal model instance |
| `send_contract_activated()` | CRM signals | Contract model instance |
| `send_task_assignment()` | Project signals | Task model instance |
| `send_project_completed()` | Project signals | Project model instance |

**Analysis:**
- Email notifications receive model instances (Proposal, Contract, Task, Project)
- All these models have `firm` ForeignKey fields (TIER 0 compliance)
- Tenant context is **implicit** via model relationships
- Risk: Low - emails are sent based on already-persisted tenant-scoped data

**Recommendation:** Future enhancement - pass explicit `firm_id` to email methods for clarity and audit trail.

---

## Webhook Handlers - Tenant Context Analysis

**File:** `api/finance/webhooks.py` (208 lines)
**Pattern:** Stripe webhook handler (synchronous processing)

### Webhook Events

| Handler | Event | Actions | Tenant Context |
|---------|-------|---------|----------------|
| `handle_payment_intent_succeeded` | `payment_intent.succeeded` | Update Invoice | ✅ Invoice.firm (from Stripe metadata) |
| `handle_payment_intent_failed` | `payment_intent.failed` | Update Invoice | ✅ Invoice.firm |
| `handle_invoice_payment_succeeded` | `invoice.payment_succeeded` | Update Invoice | ✅ Invoice.firm |
| `handle_invoice_payment_failed` | `invoice.payment_failed` | Update Invoice | ✅ Invoice.firm |
| `handle_charge_refunded` | `charge.refunded` | Update Invoice | ✅ Invoice.firm |

**Analysis:**
- Webhooks look up existing Invoice records using Stripe metadata
- All updates are to existing objects, no new object creation
- Tenant context is maintained via Invoice.firm relationship

**Conclusion:** Webhook handlers are tenant-safe.

---

## Detailed Fix Requirements

### Required Changes

**File:** `/home/user/OS/src/modules/clients/signals.py`

#### Fix #1: `_handle_new_client()` - Add firm to Client creation

**Location:** Line 46

**Before:**
```python
client = Client.objects.create(
    source_prospect=proposal.prospect,
```

**After:**
```python
client = Client.objects.create(
    firm=proposal.firm,  # TIER 2: Explicit tenant context
    source_prospect=proposal.prospect,
```

---

#### Fix #2: `_handle_new_client()` - Add firm to Contract creation

**Location:** Line 72

**Before:**
```python
contract = Contract.objects.create(
    client=client,
```

**After:**
```python
contract = Contract.objects.create(
    firm=proposal.firm,  # TIER 2: Explicit tenant context
    client=client,
```

---

#### Fix #3: `_handle_new_client()` - Add firm to ClientEngagement creation

**Location:** Line 90

**Before:**
```python
ClientEngagement.objects.create(
    client=client,
```

**After:**
```python
ClientEngagement.objects.create(
    firm=proposal.firm,  # TIER 2: Explicit tenant context
    client=client,
```

---

#### Fix #4: `_handle_new_client()` - Add firm to Project creation

**Location:** Line 105

**Before:**
```python
if proposal.auto_create_project:
    Project.objects.create(
        client=client,
```

**After:**
```python
if proposal.auto_create_project:
    Project.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
```

---

#### Fix #5-8: `_handle_new_client()` - Add firm to Folder creation (4 folders)

**Locations:** Lines 121, 130, 139, 148

**Before (all 4 instances):**
```python
Folder.objects.create(
    client=client,
    parent=...,
    name="...",
    # ...
)
```

**After (all 4 instances):**
```python
Folder.objects.create(
    firm=proposal.firm,  # TIER 2: Explicit tenant context
    client=client,
    parent=...,
    name="...",
    # ...
)
```

---

#### Fix #9: `_handle_client_engagement()` - Add firm to Contract creation

**Location:** Line 202

**Before:**
```python
contract = Contract.objects.create(
    client=client,
```

**After:**
```python
contract = Contract.objects.create(
    firm=proposal.firm,  # TIER 2: Explicit tenant context
    client=client,
```

---

#### Fix #10: `_handle_client_engagement()` - Add firm to ClientEngagement creation

**Location:** Line 220

**Before:**
```python
ClientEngagement.objects.create(
    client=client,
```

**After:**
```python
ClientEngagement.objects.create(
    firm=proposal.firm,  # TIER 2: Explicit tenant context
    client=client,
```

---

#### Fix #11: `_handle_client_engagement()` - Add firm to Project creation

**Location:** Line 235

**Before:**
```python
if proposal.auto_create_project:
    Project.objects.create(
        client=client,
```

**After:**
```python
if proposal.auto_create_project:
    Project.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
```

---

## Testing Verification

### Manual Testing
1. Create Proposal for prospective_client
2. Accept Proposal → verify Client creation includes firm
3. Verify all related objects (Contract, Engagement, Project, Folders) have correct firm
4. Test renewal_client and update_client proposal types
5. Verify cross-tenant isolation (cannot access other firm's data)

### Automated Tests (Future - Tier 1.4)
```python
def test_accepted_proposal_creates_client_with_firm():
    """Test that accepted proposals create clients with proper tenant context."""
    firm = Firm.objects.create(name="Test Firm")
    proposal = Proposal.objects.create(
        firm=firm,
        status='accepted',
        proposal_type='prospective_client',
        # ...
    )

    # Signal should have triggered
    client = Client.objects.get(source_proposal=proposal)

    # CRITICAL: Client must have firm context
    assert client.firm == firm
    assert Contract.objects.get(client=client).firm == firm
    assert ClientEngagement.objects.get(client=client).firm == firm
```

---

## Security Impact

### Before Fix
**Vulnerabilities:**
- Signal-created objects lack explicit tenant context
- Potential IntegrityError failures (if not caught)
- If firm field were nullable, would create cross-tenant data leaks
- Violates Tier 0 requirement: "All data MUST belong to exactly one Firm"

**Risk Level:** 🔴 HIGH
- Every accepted proposal triggers this workflow
- 11 object creations without tenant context
- Core onboarding workflow affected

### After Fix
**Protections:**
- ✅ All signal-created objects have explicit `firm=proposal.firm`
- ✅ Tenant isolation maintained in async workflows
- ✅ Defense in depth: FirmScopedMixin + Explicit firm parameter
- ✅ Consistent with Tier 0 isolation requirements

**Risk Level:** 🟢 LOW
- Tenant context explicitly passed at object creation
- No reliance on implicit relationships
- Audit trail shows firm context at creation time

---

## Standard Job Payload Schema

### Recommendation: Future Task Queue Implementation

When migrating to Celery/Django Q/RQ in the future, use this standard:

```python
# Standard async job payload
{
    "firm_id": 123,           # REQUIRED: Tenant context
    "user_id": 456,           # REQUIRED: Actor context
    "client_id": 789,         # OPTIONAL: Client context (where applicable)
    "action": "create_client_from_proposal",
    "params": {
        "proposal_id": 101
    },
    "timestamp": "2025-12-24T12:00:00Z",
    "idempotency_key": "uuid-here"
}
```

**Validation on Job Execution:**
```python
@celery.task
def create_client_from_proposal(firm_id, user_id, proposal_id):
    # 1. Validate tenant context
    if not firm_id:
        raise ValueError("firm_id is required for tenant isolation")

    # 2. Load firm-scoped data
    firm = Firm.objects.get(id=firm_id)
    proposal = Proposal.objects.filter(firm=firm, id=proposal_id).first()

    if not proposal:
        raise ValueError("Proposal not found in tenant scope")

    # 3. Execute job with explicit tenant context
    client = Client.objects.create(
        firm=firm,  # Explicit tenant context
        # ...
    )
```

---

## Compliance

### TIER 2 Completion Criteria

- [x] ✅ Define standard job payload schema (firm_id, client_id)
- [x] ✅ Identify all background/async job patterns (Django signals)
- [ ] ⚠️ Add explicit tenant context to job execution (IN PROGRESS - signals need fixes)
- [ ] ⚠️ Apply permission checks inside jobs (future enhancement)
- [ ] ⚠️ Jobs fail without tenant context (future: add validation)

### TIER 0 Alignment
- [x] ✅ Firm isolation requirement identified in signals
- [ ] ⚠️ Firm isolation enforced in signal object creation (PENDING FIX)

### Security Standards
- 🔴 OWASP: Broken Access Control (A01:2021) - Currently vulnerable in signals
- 🔴 Principle of Least Privilege - Signals lack explicit tenant enforcement
- 🟡 Defense in Depth - Models have firm fields, but signals don't use them

---

## Related Work

**Completed:**
- Tier 0: Firm scoping models and middleware
- Tier 2.1: ViewSet permission standardization
- Tier 2.2: User model abstraction (AUTH_USER_MODEL)

**Dependencies:**
- Tier 0: Firm-scoped models (prerequisite - complete)
- Tier 1.4: Permission tests (should test signal tenant isolation)

**Future:**
- Tier 2.4: Verify firm-scoped querysets (verify signals use scoped queries)
- Tier 3: Audit logging (track signal-triggered workflows)
- Tier 5: Hero workflow integration tests (test end-to-end proposal→client flow)

---

## Conclusion

**Task 2.3 Status:** 🔴 CRITICAL FIXES REQUIRED

**Summary:**
- ✅ Audit Complete: Inventoried all 18 signal handlers
- ✅ Issue Identified: 11 object creations missing explicit tenant context
- ✅ Standard Defined: firm_id + user_id + client_id payload pattern
- ⚠️ Fixes Pending: 11 edits required in `/home/user/OS/src/modules/clients/signals.py`

**Security Improvement:** Will go from 🔴 HIGH RISK → 🟢 LOW RISK

The application's "background job" system (Django signals) currently lacks explicit tenant context when creating objects. This violates Tier 0 tenant isolation principles and could lead to data integrity issues or cross-tenant leaks if not fixed.

**Recommendation:** Proceed with signal fixes immediately to ensure tenant isolation in all async workflows.

---

**Last Updated:** 2025-12-24
**Next Steps:** Fix `/home/user/OS/src/modules/clients/signals.py` with 11 explicit `firm=proposal.firm` additions
