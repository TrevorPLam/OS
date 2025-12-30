# Strategic TODO Implementation Plan

**Created:** December 30, 2025
**Branch:** claude/assess-todos-plan-tasks-UqOcX
**Author:** Claude Code
**Status:** Active

---

## Executive Summary

This document provides a strategic implementation plan for addressing remaining TODO items across the ConsultantPro codebase. The plan prioritizes tasks based on:

1. **Criticality** - Security, data integrity, and blocking issues
2. **Impact** - User-facing features vs infrastructure improvements
3. **Dependencies** - Tasks that unblock other work
4. **Risk** - Changes that could introduce regressions

**Current State:**
- **Constitution Compliance:** 11/12 complete (92%)
- **ChatGPT Assessment Remediation:** 1/22 complete (4.5%)
- **In-Code TODOs:** 22 identified (categorized)

**Recommended Approach:** Focus on **ChatGPT Assessment Critical Fixes** first (Phase 1), then complete **Constitution Compliance** (Phase 2), then address remaining items in priority order.

---

## Phase 1: CRITICAL FIXES (Week 1-2) 🔥

**Objective:** Fix blocking test failures, security vulnerabilities, and data integrity issues

### 1.1 Data Model Fixes (CRITICAL - Blocks Tests)

#### ASSESS-C3.1 / ASSESS-D4.1 / ASSESS-D4.7: Fix Prospect.stage Field Naming
**Priority:** P0 (CRITICAL)
**Effort:** 2-4 hours
**Risk:** Low (naming fix)

**Problem:**
- Model has `pipeline_stage` field (src/modules/crm/models.py:373)
- Tests/API/frontend may expect `stage` field
- Blocks 12+ tests according to assessment

**Solution:**
1. Audit all references to `Prospect.pipeline_stage` vs `Prospect.stage`
2. Decide on canonical name (recommend `stage` for API consistency)
3. Create migration to rename field: `pipeline_stage` → `stage`
4. Update all serializers, views, forms, admin, tests
5. Run full test suite to verify

**Files to Check:**
- `src/modules/crm/models.py:373`
- `src/modules/crm/serializers.py`
- `src/modules/crm/views.py`
- `src/modules/crm/admin.py`
- `src/api/crm/views.py`
- All test files in `src/tests/crm/`

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] API uses `stage` field consistently
- [ ] Migration is reversible
- [ ] Admin interface works correctly

---

#### ASSESS-C3.1b: Replace Float with Decimal for Currency
**Priority:** P0 (CRITICAL - Data Integrity)
**Effort:** 4-8 hours
**Risk:** Medium (requires migration + testing)

**Problem:**
- Financial calculations using `float` instead of `Decimal`
- Precision errors in money calculations
- Rounding issues in billing

**Solution:**
1. Audit all finance module models for float usage
2. Identify fields representing currency/money
3. Create migrations to change fields from float to DecimalField
4. Update all calculations to use Decimal arithmetic
5. Add test cases for precision edge cases

**Files to Audit:**
- `src/modules/finance/models.py` (all currency fields)
- `src/modules/projects/models.py` (estimated_value, etc.)
- `src/modules/crm/models.py` (annual_revenue, estimated_value)
- Any billing/payment calculation logic

**Search Pattern:**
```python
grep -r "FloatField.*value\|FloatField.*amount\|FloatField.*price\|FloatField.*cost" src/modules/
```

**Acceptance Criteria:**
- [ ] All currency fields use DecimalField(max_digits=12, decimal_places=2)
- [ ] All money calculations use Decimal type
- [ ] Test cases verify precision (e.g., 0.1 + 0.2 = 0.3)
- [ ] Migrations tested with production-like data

---

#### ASSESS-D4.4b: Fix company_name Uniqueness Scope
**Priority:** P1 (HIGH - Data Integrity)
**Effort:** 2-3 hours
**Risk:** Low (constraint change)

**Problem:**
- `Prospect.company_name` is globally unique
- Should be unique per firm only
- Blocks multi-tenant use case

**Solution:**
1. Find unique constraint on `Prospect.company_name`
2. Replace with `unique_together('firm', 'company_name')`
3. Create migration
4. Update validation logic in serializers/forms

**Files:**
- `src/modules/crm/models.py` (Prospect model)
- Check for `unique=True` on `company_name`

**Acceptance Criteria:**
- [ ] Two firms can have prospects with same company name
- [ ] Same firm cannot have duplicate company names
- [ ] Validation errors are clear

---

### 1.2 Security Fixes (CRITICAL)

#### ASSESS-S6.2: Fix Multi-Tenancy Gaps in Async/Signals
**Priority:** P0 (CRITICAL - IDOR Risk)
**Effort:** 8-16 hours
**Risk:** High (security-critical)

**Problem:**
- Async tasks may not enforce firm isolation
- Django signals may bypass tenant scoping
- IDOR (Insecure Direct Object Reference) vulnerability

**Solution:**
1. **Audit Phase** (4-6 hours):
   - List all Celery tasks and async functions
   - List all Django signal handlers
   - Check each for `firm_id` or `firm` parameter
   - Check for use of `FirmScopedQuerySet`

2. **Fix Phase** (4-10 hours):
   - Add `firm_id` to all task signatures
   - Add firm validation at start of each task
   - Update signal handlers to use firm-scoped queries
   - Add test cases for cross-tenant access attempts

**Files to Audit:**
- `src/modules/*/tasks.py` (Celery tasks)
- `src/modules/*/signals.py` (Signal handlers)
- Search for `@shared_task`, `@receiver`, `post_save`, `pre_save`

**Test Pattern:**
```python
# Test that firm A cannot trigger actions on firm B's data
# via async tasks or signal handlers
```

**Acceptance Criteria:**
- [ ] All async tasks require firm_id parameter
- [ ] All tasks validate firm ownership before operations
- [ ] All signal handlers use firm-scoped queries
- [ ] Cross-tenant test cases pass

---

#### ASSESS-I5.6: Fix SSRF Validation Gaps
**Priority:** P1 (HIGH - Security)
**Effort:** 3-5 hours
**Risk:** Medium (security)

**Problem:**
- URL inputs may not be validated against SSRF attacks
- Internal IPs/localhost could be accessible

**Solution:**
1. Find existing `InputValidator.validate_url()` utility
2. Audit all URL input fields (webhooks, integrations, etc.)
3. Apply validation to block:
   - `localhost`, `127.0.0.1`, `::1`
   - Private IP ranges (10.x, 192.168.x, 172.16-31.x)
   - Cloud metadata endpoints (169.254.169.254)
4. Add test cases

**Files to Check:**
- `src/modules/core/input_validation.py` (check if validator exists)
- `src/modules/sms/models.py` (webhook URLs)
- Any webhook/integration URL fields

**Acceptance Criteria:**
- [ ] All URL inputs use `validate_safe_url` validator
- [ ] SSRF test cases pass (localhost, private IPs blocked)
- [ ] Legitimate external URLs still work

---

#### ASSESS-D4.4: Fix Idempotency Gaps
**Priority:** P1 (HIGH - Data Integrity)
**Effort:** 4-6 hours
**Risk:** Medium (payment handling)

**Problem:**
- Stripe PaymentIntent calls may lack idempotency keys
- Webhook events may be processed multiple times

**Solution:**
1. **Stripe PaymentIntent**:
   - Add `idempotency_key` parameter to all `stripe.PaymentIntent.create()` calls
   - Generate from: `f"payment_{invoice_id}_{timestamp}"`

2. **Webhook Dedupe**:
   - Store processed webhook event IDs
   - Check before processing
   - Add model: `ProcessedWebhookEvent(event_id, processed_at)`

**Files:**
- `src/modules/finance/services.py` (Stripe integration)
- `src/api/finance/webhooks.py` (webhook handler)

**Acceptance Criteria:**
- [ ] PaymentIntent creation is idempotent
- [ ] Duplicate webhook events are ignored
- [ ] Test cases verify dedupe logic

---

### 1.3 Test Infrastructure (CRITICAL)

#### ASSESS-C3.10: Eliminate Test Non-Determinism
**Priority:** P1 (HIGH - CI Reliability)
**Effort:** 2-4 hours
**Risk:** Low (test config)

**Problem:**
- Tests may use SQLite locally, Postgres in CI
- SQLite foreign key enforcement may be disabled
- Schema differences cause flaky tests

**Solution:**
1. **Option A (Recommended):** Use Postgres everywhere
   - Update test settings to use Postgres
   - Add docker-compose for local Postgres
   - Document setup

2. **Option B:** Fix SQLite config
   - Enable foreign key enforcement: `PRAGMA foreign_keys = ON;`
   - Add to test database configuration

**Files:**
- `src/config/settings.py` (DATABASES config)
- `.github/workflows/ci.yml` (CI database setup)
- Add `docker-compose.test.yml` if needed

**Acceptance Criteria:**
- [ ] Tests use same database engine locally and in CI
- [ ] Foreign key constraints enforced
- [ ] No schema drift between environments

---

## Phase 2: CONSTITUTION COMPLETION (Week 3) ⚙️

**Objective:** Complete remaining constitution compliance items

### 2.1 CONST-5: Develop Threat Model (Section 6.7)
**Priority:** P2 (MEDIUM - Governance)
**Effort:** 8-12 hours
**Risk:** Low (documentation)

**Requirements (from codingconstitution.md:162-164):**
- Threat model must exist and be updated for major changes
- Each mitigation must point to code/tests

**Solution:**
1. **Create `docs/THREAT_MODEL.md`** with STRIDE analysis:

```markdown
# Threat Model - ConsultantPro Platform

## 1. System Overview
- Multi-tenant SaaS platform for professional services firms
- Django/Python backend, React frontend
- Handles sensitive client data, financial transactions

## 2. Assets
- Client PII (contact info, documents, communications)
- Financial data (invoices, payments, retainers)
- Authentication credentials (user accounts, API keys)
- Business logic (pricing rules, delivery templates)

## 3. Threat Scenarios (STRIDE)

### Spoofing Identity
**T-1: Unauthorized Portal Access**
- Attack: Attacker guesses client portal credentials
- Impact: Access to client data
- Likelihood: Medium
- Mitigation: Rate limiting on login (src/api/portal/throttling.py)
- Test: test_portal_rate_limiting.py:50
- Status: ✅ Implemented

**T-2: API Key Theft**
- Attack: Stolen API key used to access staff endpoints
- Impact: Data breach
- Likelihood: Medium
- Mitigation: Token rotation, revocation (src/modules/auth/tokens.py)
- Test: test_token_revocation.py
- Status: ✅ Implemented

### Tampering
**T-3: Billing Ledger Tampering**
- Attack: Modify immutable ledger entries
- Impact: Financial fraud
- Likelihood: Low (requires DB access)
- Mitigation: Immutability enforcement (src/modules/finance/billing_ledger.py:45)
- Test: test_billing_ledger.py:120
- Status: ✅ Implemented

**T-4: Document Version Manipulation**
- Attack: Alter signed document after signature
- Impact: Evidence destruction
- Likelihood: Low
- Mitigation: Version checksums, immutability (src/modules/documents/models.py)
- Test: test_document_versioning.py
- Status: ✅ Implemented

### Repudiation
**T-5: Deny Performing Sensitive Action**
- Attack: User denies deleting data
- Impact: Disputes, compliance
- Likelihood: Medium
- Mitigation: Audit logging (src/modules/firm/audit.py)
- Test: test_audit_immutability.py
- Status: ✅ Implemented

### Information Disclosure
**T-6: Cross-Tenant Data Leak**
- Attack: Firm A accesses Firm B's data via IDOR
- Impact: Data breach, compliance violation
- Likelihood: Medium (if async tasks unprotected)
- Mitigation: FirmScopedQuerySet (src/modules/firm/utils.py)
- Test: test_tenant_isolation.py
- Status: ⚠️ Partial (async/signals need audit - see ASSESS-S6.2)

**T-7: Portal User Access to Other Accounts**
- Attack: Portal user manipulates client_id to see other accounts
- Impact: PII leak
- Likelihood: Medium
- Mitigation: Portal scope gating (src/api/portal/permissions.py)
- Test: test_portal_multi_account.py
- Status: ✅ Implemented

**T-8: SSRF via Webhook URLs**
- Attack: Attacker provides internal URL to webhook config
- Impact: Access to cloud metadata, internal services
- Likelihood: Medium
- Mitigation: URL validation (src/modules/core/input_validation.py)
- Test: test_ssrf_protection.py
- Status: ⚠️ Partial (needs validation on all URL inputs - see ASSESS-I5.6)

### Denial of Service
**T-9: Portal Abuse**
- Attack: Automated requests to portal endpoints
- Impact: Service degradation
- Likelihood: High
- Mitigation: Rate limiting (src/api/portal/throttling.py)
- Test: test_portal_rate_limiting.py
- Status: ✅ Implemented

**T-10: Expensive Queries**
- Attack: Request unbounded lists
- Impact: Database overload
- Likelihood: Medium
- Mitigation: Pagination (src/config/settings.py:BoundedPageNumberPagination)
- Test: test_pagination_limits.py
- Status: ✅ Implemented

### Elevation of Privilege
**T-11: Role Escalation**
- Attack: Staff user grants self admin privileges
- Impact: Unauthorized access
- Likelihood: Low
- Mitigation: Role change audit (src/modules/firm/models.py)
- Test: test_role_change_audit.py
- Status: ✅ Implemented

**T-12: Bypass Tenant Isolation**
- Attack: Craft query to access other firm's data
- Impact: Multi-tenant breach
- Likelihood: Medium
- Mitigation: FirmScopedQuerySet default manager (src/modules/firm/utils.py)
- Test: test_tenant_isolation.py
- Status: ⚠️ Partial (async/signals need audit - see ASSESS-S6.2)

## 4. Residual Risks (Require Remediation)

| ID | Threat | Mitigation Status | Remediation Plan |
|----|--------|-------------------|------------------|
| T-6 | Cross-tenant leak via async | ⚠️ Partial | ASSESS-S6.2: Audit async tasks/signals |
| T-8 | SSRF via webhooks | ⚠️ Partial | ASSESS-I5.6: Add URL validation |
| T-12 | Tenant bypass in async | ⚠️ Partial | ASSESS-S6.2: Firm scoping in signals |

## 5. Review Schedule

- **Next Review:** March 30, 2026 (quarterly)
- **Trigger for Ad-Hoc Review:**
  - New external integration added
  - New data type introduced (e.g., health records)
  - Significant architecture change (e.g., microservices)
  - Security incident or near-miss

## 6. References

- [Security Model](docs/24)
- [Constitution Analysis](CONSTITUTION_ANALYSIS.md)
- [ChatGPT Assessment](docs/ChatGPT_CODEBASE_ASSESMENT)
- [Audit System](src/modules/firm/audit.py)
```

**Acceptance Criteria:**
- [ ] THREAT_MODEL.md created
- [ ] All STRIDE categories covered
- [ ] Each threat maps to mitigation + test
- [ ] Residual risks documented
- [ ] Review schedule established

---

### 2.2 CONST-10: Add Boundary Rules Enforcement (Section 15)
**Priority:** P2 (MEDIUM - Architecture)
**Effort:** 4-8 hours
**Risk:** Low (CI check)

**Requirements (from codingconstitution.md:397):**
- CI check: boundary rules (forbidden imports) enforced by tooling

**Solution:**
1. **Install `import-linter`:**
```bash
pip install import-linter
echo "import-linter" >> requirements-dev.txt
```

2. **Create `.importlinter` config:**
```ini
[importlinter]
root_package = src

[importlinter:contract:1]
name = UI layer must not import infrastructure directly
type = forbidden
source_modules =
    src.api
    src.frontend
forbidden_modules =
    src.modules.*.tasks
    src.modules.*.signals

[importlinter:contract:2]
name = Domain must not import Django ORM in business logic
type = forbidden
source_modules =
    src.modules.*.services
    src.modules.*.domain
forbidden_modules =
    django.db

[importlinter:contract:3]
name = No circular dependencies between modules
type = independence
modules =
    src.modules.crm
    src.modules.finance
    src.modules.projects
    src.modules.documents
```

3. **Add to CI:**
```yaml
# .github/workflows/ci.yml
- name: Check Boundary Rules
  run: |
    pip install import-linter
    lint-imports
```

**Files:**
- Create `.importlinter` config
- Update `.github/workflows/ci.yml`
- Update `requirements-dev.txt`

**Acceptance Criteria:**
- [ ] import-linter configured
- [ ] CI fails on forbidden imports
- [ ] Existing codebase passes (or violations documented)
- [ ] README documents boundary rules

---

## Phase 3: API & DATA QUALITY (Week 4-5) 📋

**Objective:** Improve API design, data alignment, and testing infrastructure

### 3.1 API Design Improvements

#### ASSESS-I5.1: Implement API Versioning
**Priority:** P2 (MEDIUM)
**Effort:** 6-10 hours

**Solution:**
1. Add `/api/v1/` prefix to all endpoints
2. Create versioning policy document
3. Plan for `/api/v2/` when needed

---

#### ASSESS-I5.5: Add Pagination to All List Endpoints
**Priority:** P2 (MEDIUM)
**Effort:** 4-6 hours

**Solution:**
1. Verify `BoundedPageNumberPagination` is global default
2. Audit all ViewSets for `pagination_class = None` overrides
3. Update frontend to handle pagination

---

#### ASSESS-I5.4: Improve Error Model
**Priority:** P3 (LOW-MEDIUM)
**Effort:** 8-12 hours

**Solution:**
1. Create structured error response format:
```json
{
  "error": {
    "code": "CARD_DECLINED",
    "message": "Payment card was declined",
    "details": {},
    "request_id": "req_123"
  }
}
```
2. Map Stripe errors to codes
3. Update exception handlers

---

### 3.2 Data Alignment

#### ASSESS-D4.6: Align Test/Prod Environments
**Priority:** P2 (MEDIUM)
**Effort:** 3-5 hours

**Solution:**
- Use Postgres for local tests (Docker)
- Document in CONTRIBUTING.md

---

#### ASSESS-C3.9: Refactor Complexity Hotspots
**Priority:** P3 (LOW-MEDIUM)
**Effort:** 16-24 hours (multi-phase)

**Solution:**
- Split large files into submodules:
  - `finance/models.py` (~1489 lines) → `finance/models/invoices.py`, `finance/models/payments.py`, etc.
  - `calendar/models.py` (~1000+ lines) → similar split

---

## Phase 4: COMPLIANCE & PRIVACY (Week 6-8) 🔒

**Objective:** GDPR compliance, reconciliation, feature alignment

### 4.1 GDPR Requirements

#### ASSESS-L19.2: Implement Consent Tracking
**Effort:** 6-10 hours

---

#### ASSESS-L19.3: Build Right-to-Delete/Export
**Effort:** 12-20 hours

---

#### ASSESS-L19.4: Define Retention Policies
**Effort:** 8-12 hours

---

### 4.2 Integration Resilience

#### ASSESS-G18.5: Add Stripe Reconciliation
**Effort:** 8-12 hours

---

#### ASSESS-G18.5b: Add S3 Reconciliation
**Effort:** 6-10 hours

---

## Phase 5: DOCUMENTATION & PROCESS (Week 9-10) 📚

### 5.1 Feature Alignment

#### ASSESS-R1.2: Implement or Document Missing Features
**Effort:** Variable (depends on scope decision)

**Features:**
- Slack integration (notifications.py:431)
- E-signature workflow (clients/views.py:769)
- SMS notifications (notifications.py:454)
- E2EE (deferred - infrastructure dependency)

**Decision Matrix:**
- Implement: High-value, low-complexity
- Document as "Coming Soon": Medium-value
- Remove claims: Low-value, high-complexity

---

#### ASSESS-R1.4: Align Spec with Reality
**Effort:** 4-8 hours

**Solution:**
- Audit docs/marketing for advertised features
- Remove claims for non-implemented features
- Update roadmap

---

#### ASSESS-R1.7: Establish Definition of Done
**Effort:** 2-4 hours

**Solution:**
Create PR checklist in `.github/PULL_REQUEST_TEMPLATE.md`:
```markdown
## Definition of Done
- [ ] All tests pass
- [ ] Docs updated (if applicable)
- [ ] No TODO comments in code (use DEFERRED with references)
- [ ] Acceptance criteria met
- [ ] Migration tested (if applicable)
- [ ] Security review (for sensitive changes)
```

---

## Execution Strategy

### Week-by-Week Breakdown

**Week 1:**
- ASSESS-C3.1: Prospect.stage field fix (4h)
- ASSESS-D4.4b: company_name uniqueness (3h)
- ASSESS-C3.10: Test determinism (4h)
- Start ASSESS-S6.2: Async/signals audit (8h)

**Week 2:**
- Complete ASSESS-S6.2 (8h)
- ASSESS-C3.1b: Float to Decimal conversion (8h)
- ASSESS-I5.6: SSRF validation (4h)
- ASSESS-D4.4: Idempotency gaps (6h)

**Week 3:**
- CONST-5: Threat model documentation (12h)
- CONST-10: Boundary rules enforcement (6h)
- Buffer for Phase 1 fixes

**Week 4-5:**
- API versioning, pagination, error model
- Data environment alignment
- Start complexity refactoring

**Week 6-8:**
- GDPR compliance features
- Reconciliation jobs
- Retention policies

**Week 9-10:**
- Documentation alignment
- Process improvements
- Definition of Done

---

## Risk Mitigation

### High-Risk Changes

1. **Float to Decimal conversion** (ASSESS-C3.1b)
   - Risk: Data migration with production data
   - Mitigation: Test with production-like dataset first, backup before migration

2. **Async/signals audit** (ASSESS-S6.2)
   - Risk: Breaking existing functionality
   - Mitigation: Comprehensive test suite, staged rollout

3. **API versioning** (ASSESS-I5.1)
   - Risk: Breaking existing clients
   - Mitigation: Maintain `/api/` as alias to `/api/v1/` initially

---

## Success Metrics

### Phase 1 (Critical Fixes)
- [ ] All CI tests pass
- [ ] Zero P0/P1 security issues
- [ ] Data integrity verified (currency calculations correct)

### Phase 2 (Constitution)
- [ ] 12/12 constitution items complete (100%)
- [ ] Threat model reviewed and approved
- [ ] CI enforces boundary rules

### Phase 3-5 (Quality & Compliance)
- [ ] API design score: 8/10
- [ ] GDPR compliance: 80%+
- [ ] Documentation alignment: 90%+

---

## Appendix A: In-Code TODOs (22 items)

**High Priority (Feature Completion):**
- [ ] `src/api/portal/views.py` - Implement organization-based multi-account logic (DOC-26.1 account switcher)
- [ ] `src/api/portal/views.py` - Add document access logging per DOC-14.2
- [ ] `src/api/portal/views.py` - Implement staff notification on portal upload
- [ ] `src/modules/sms/views.py` - Queue webhook processing for background execution
- [ ] `src/modules/orchestration/executor.py` - Implement actual step handler dispatch based on step type
- [ ] `src/modules/orchestration/executor.py` - Add PII redaction logic to error messages

**Medium Priority (Implementation Details):**
- [ ] `src/api/portal/views.py` - Update session/token context with new client_id on account switch
- [ ] `src/api/portal/views.py` - Link uploaded documents to Contact if available
- [ ] `src/api/portal/views.py` - Notify staff of appointment cancellation
- [ ] `src/modules/calendar/views.py` - Get account from validated_data if provided
- [ ] `src/modules/marketing/views.py` - Trigger actual email send jobs
- [ ] `src/modules/delivery/instantiator.py` - Implement role-based assignment lookup
- [ ] `src/modules/firm/provisioning.py` - Implement when configuration models are defined

**Deferred (External Dependencies):**
- [ ] `src/modules/core/notifications.py` - Slack API integration (See TODO_ANALYSIS.md #10)
- [ ] `src/modules/core/notifications.py` - SMS service integration (See TODO_ANALYSIS.md #11)
- [ ] `src/modules/clients/views.py` - E-signature workflow (See TODO_ANALYSIS.md #12)

**Low Priority (Future Enhancements):**
- [ ] `src/modules/documents/models.py` - Implement document approval workflow (TODO 2.7)
- [ ] `src/modules/onboarding/models.py` - Trigger email/notification to client on workflow events

---

## Appendix B: Missing Features (NON-FUNCTIONAL)

**NOTE:** These features have code but are **non-functional** due to missing migrations and broken model references. See [IMPLEMENTATION_ASSESSMENT.md](./IMPLEMENTATION_ASSESSMENT.md).

**Recommendation:** Defer until Phase 6 (beyond this plan) or deprecate.

- MISSING-1: Support/Ticketing System
- MISSING-2: Meeting Polls
- MISSING-3: Meeting Workflow Automation
- MISSING-4: Email Campaign Templates (partial)
- MISSING-5: Tag-based Segmentation (partial)
- MISSING-6: Client Onboarding Workflows
- MISSING-7: API Layer Completion
- MISSING-8: Snippets System
- MISSING-9: User Profile Customization (check status)
- MISSING-10: Lead Scoring Automation (check status)
- MISSING-11: SMS Integration
- MISSING-12: Calendar Sync (Google/Outlook)

---

## Appendix C: Reference Documents

- [TODO.md](./TODO.md) - Master TODO list
- [TODO_ANALYSIS.md](./TODO_ANALYSIS.md) - Historical TODO analysis
- [CONSTITUTION_ANALYSIS.md](./CONSTITUTION_ANALYSIS.md) - Constitution compliance analysis
- [ChatGPT_CODEBASE_ASSESMENT](./docs/ChatGPT_CODEBASE_ASSESMENT) - External audit findings
- [IMPLEMENTATION_ASSESSMENT.md](./IMPLEMENTATION_ASSESSMENT.md) - Missing features assessment
- [docs/codingconstitution.md](./docs/codingconstitution.md) - Coding constitution
- [docs/SYSTEM_SPEC_ALIGNMENT.md](./docs/SYSTEM_SPEC_ALIGNMENT.md) - System spec alignment

---

**End of Strategic Implementation Plan**
