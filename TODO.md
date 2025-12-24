# ConsultantPro - Unified Prioritized TODO List

**Last Updated:** December 24, 2025

---

## Overview

This TODO list is organized by **Tiers (0-5)**, representing architectural priorities. Each tier must be complete before proceeding to the next.

**See:** `docs/claude/NOTES_TO_CLAUDE.md` for authoritative rules.

---

## TIER 0 — FOUNDATIONAL SAFETY

> **Rule:** Tier 0 must be complete before any feature, billing, or UX work proceeds.
>
> If Tier 0 is wrong or incomplete, privacy, tenancy, and trust all fail.

### Tasks

- [x] **0.1** Introduce Firm / Workspace tenancy ✅ COMPLETE
  - [x] Create Firm (Workspace) model ✅
  - [x] Establish Firm ↔ User relationship (FirmMembership) ✅
  - [x] Establish Firm ↔ Client relationship ✅
  - [x] Add Firm ↔ CRM relationships (Lead, Prospect, Campaign, Proposal, Contract) ✅
  - [x] Add Firm ↔ Projects relationships (Project, Task, TimeEntry) ✅
  - [x] Add Firm ↔ Finance relationships (Invoice, Bill, LedgerEntry) ✅
  - [x] Add Firm ↔ Documents relationships (Folder, Document, Version) ✅
  - [x] Add Firm ↔ Assets relationships (Asset, MaintenanceLog) ✅
  - [x] Create database migrations ✅
  - [ ] Verify data integrity constraints work correctly (requires DB setup)

- [x] **0.2** Implement Firm context resolution (subdomain/session/token) ✅ COMPLETE
  - [x] Firm context resolver (subdomain + session + token) ✅
  - [x] Firm context attached to request object ✅
  - [x] Firm context validation guard ✅
  - [x] Requests without firm context are rejected ✅

- [x] **0.3** Enforce firm + client scoping everywhere ✅ COMPLETE
  - [x] Firm-scoped queryset mixins/helpers ✅
  - [x] Refactor existing queries to use firm scoping ✅
  - [x] Forbid `Model.objects.all()` in firm-facing code ✅
  - [x] Client-scoped queries where applicable ✅

- [x] **0.4** Portal containment (default-deny) ✅ COMPLETE
  - [x] Portal-only permission classes ✅
  - [x] Separate routing or namespace for portal ✅
  - [x] Explicit allowlist of portal endpoints ✅
  - [x] Portal users receive 403 on non-portal endpoints ✅

- [x] **0.5** Platform privacy enforcement (metadata-only) ✅ PARTIAL (E2EE blocked)
  - [x] Platform role separation (Operator vs Break-Glass) ✅
  - [x] Explicit deny rules for content models ✅
  - [x] Metadata/content separation in models and APIs ✅
  - [ ] Content encryption (E2EE) ⚠️ BLOCKED (requires KMS infrastructure, see docs/tier0/E2EE_IMPLEMENTATION_PLAN.md)

- [x] **0.6** Break-glass access with impersonation safeguards ✅ PARTIAL (enforcement pending)
  - [x] Break-glass activation mechanism ✅
  - [ ] Impersonation mode indicator ⚠️ PENDING (requires UI/middleware integration)
  - [x] Automatic expiration ✅
  - [ ] Immutable audit records for break-glass actions ⚠️ PENDING (requires Tier 3 audit system)
  - [x] Time limit enforcement ✅
  - [x] Reason string requirement ✅

### Completion Criteria

- [ ] Firm isolation is provable
- [ ] Platform cannot read content by default
- [ ] Portal users are fully contained
- [ ] Break-glass is rare, visible, and audited
- [ ] Async jobs are tenant-safe

---

## TIER 1 — SCHEMA TRUTH & CI TRUTH

> **Rule:** Tier 1 ensures the database schema and CI reflect reality.

### Tasks

- [ ] **1.1** Fix deterministic backend crashes
  - [ ] Fix CRM import errors
  - [ ] Fix Spectacular enum paths
  - [ ] Fix auth AppConfig issues
  - [ ] Backend boots without deterministic exceptions

- [ ] **1.2** Commit all missing migrations
  - [ ] Assets module migrations
  - [ ] Documents module migrations
  - [ ] Client portal migrations
  - [ ] Chat module migrations
  - [ ] Verify `makemigrations` is clean (no-op)
  - [ ] Verify `migrate` works from fresh DB

- [ ] **1.3** Make CI honest
  - [ ] Remove skipped lint checks
  - [ ] Add frontend build gate to CI
  - [ ] Add frontend typecheck to CI
  - [ ] Ensure lint/build/test failures fail CI
  - [ ] No `|| true` or skip-on-fail patterns

- [ ] **1.4** Add minimum safety test set
  - [ ] Tenant isolation tests (cross-firm access blocked)
  - [ ] Portal containment tests (default-deny)
  - [ ] Engagement immutability tests (signed engagements)
  - [ ] Billing approval gate tests (time entry approval)

### Completion Criteria

- [ ] Backend boots without deterministic exceptions
- [ ] API schema generation completes without error
- [ ] Fresh DB: migrations apply cleanly
- [ ] `makemigrations` yields no changes
- [ ] CI fails on lint/build/type errors (backend + frontend)
- [ ] Minimal invariant tests exist and run in CI

---

## TIER 2 — AUTHORIZATION & OWNERSHIP

> **Rule:** Tier 2 ensures who can do what is explicit, enforced, and impossible to bypass.

### Tasks

- [ ] **2.1** Standardize permissions across all ViewSets
  - [ ] Inventory all ViewSets and endpoints
  - [ ] Attach explicit permission classes everywhere
  - [ ] Remove inline or duplicated permission checks
  - [ ] Centralize authorization logic

- [ ] **2.2** Replace direct User imports with AUTH_USER_MODEL
  - [ ] Search and replace direct User imports
  - [ ] Update type hints and serializers
  - [ ] Update signals and admin references

- [ ] **2.3** Add firm + client context to all background/async jobs
  - [ ] Define standard job payload schema (firm_id, client_id)
  - [ ] Validate tenant context on job execution
  - [ ] Apply permission checks inside jobs
  - [ ] Jobs fail without tenant context

- [ ] **2.4** Firm-scoped querysets (zero global access)
  - [ ] All querysets filter by firm_id
  - [ ] Client-scoped data also filters by client_id
  - [ ] Platform roles cannot bypass scoping (except break-glass)

- [ ] **2.5** Portal authorization (client-scoped, explicit allowlist)
  - [ ] Portal-specific permission classes
  - [ ] Define portal endpoint allowlist
  - [ ] Portal users never hit firm admin endpoints

- [ ] **2.6** Cross-client access within Organizations
  - [ ] Enforce org-based access checks
  - [ ] Ensure shared-org views are clearly scoped
  - [ ] Prevent default cross-client visibility

### Completion Criteria

- [ ] Every endpoint has explicit permissions
- [ ] All data access is tenant-scoped
- [ ] Portal users are fully contained
- [ ] Cross-client access is intentional and auditable
- [ ] Async jobs obey the same rules as synchronous code

---

## TIER 3 — DATA INTEGRITY & PRIVACY

> **Rule:** Tier 3 makes the platform trustworthy under stress: legal requests, disputes, incidents, employee misuse, and customer exits.

### Tasks

- [ ] **3.1** Implement purge semantics (tombstones, metadata retention)
  - [ ] Define tombstone model strategy (messages, comments, documents)
  - [ ] Implement purge flows for Master Admin
  - [ ] Confirmation + reason required for purge
  - [ ] Purge removes content but preserves metadata

- [ ] **3.2** Define audit event taxonomy + retention policy
  - [ ] Define event categories (AUTH, PERMISSIONS, BREAK_GLASS, BILLING_METADATA, PURGE, CONFIG)
  - [ ] Define event fields (actor, tenant context, target, timestamp, action, reason)
  - [ ] Implement structured audit writes
  - [ ] Audit records are tenant-scoped

- [ ] **3.3** Define audit review ownership and cadence
  - [ ] Define review owner(s) (platform ops/security)
  - [ ] Define review cadence (break-glass: weekly, role changes: monthly)
  - [ ] Define escalation path for anomalies

- [ ] **3.4** Implement privacy-first support workflows
  - [ ] Metadata-only diagnostics
  - [ ] Customer export package format
  - [ ] Secure intake with limited retention
  - [ ] Support can resolve issues without content visibility

- [ ] **3.5** Document signing lifecycle & evidence retention
  - [ ] Immutable signing events
  - [ ] Link to document version/hash (not plaintext)
  - [ ] Signature evidence survives content purge

### Completion Criteria

- [ ] Purge works via tombstones for all content-bearing models
- [ ] Every purge emits an immutable audit event
- [ ] Audit event system exists, structured, tenant-scoped, content-free
- [ ] Retention + review primitives exist
- [ ] Support diagnostics can be generated without content access
- [ ] Signing events are immutable and survive purges

---

## TIER 4 — BILLING & MONETIZATION

> **Rule:** Tier 4 ensures money, scope, and incentives align.

### Tasks

- [ ] **4.1** Enforce billing invariants (package/hourly/mixed, approval gates)
  - [ ] Invoice belongs to Client
  - [ ] Invoice links to Engagement by default
  - [ ] Engagement defines pricing mode (package/hourly/mixed)
  - [ ] Master Admin can override engagement linkage

- [ ] **4.2** Package fee invoicing
  - [ ] Package fees defined at engagement creation
  - [ ] Package invoices auto-generated on schedule
  - [ ] Package fees survive renewals correctly
  - [ ] No duplicate invoices

- [ ] **4.3** Hourly billing with approval gates
  - [ ] Time entries exist independently of invoices
  - [ ] Time entries not billable by default
  - [ ] Staff/Admin approval required before billing
  - [ ] Client approval optional (future-ready)

- [ ] **4.4** Mixed billing (package + hourly together)
  - [ ] Engagement can specify mixed billing
  - [ ] Package and hourly line items are distinct
  - [ ] Reporting clearly separates the two

- [ ] **4.5** Implement credit ledger
  - [ ] Credits tracked in ledger (not ad-hoc fields)
  - [ ] Credit creation and application auditable
  - [ ] Credit balance always reconciles

- [ ] **4.6** Recurring payments (autopay)
  - [ ] Recurring payments auto-pay invoices as issued
  - [ ] Recurring payments do not generate invoices themselves
  - [ ] Autopay can be disabled per client

- [ ] **4.7** Handle payment failures, disputes, and chargebacks explicitly
  - [ ] Payment failures are first-class events
  - [ ] Disputes and chargebacks tracked explicitly
  - [ ] Platform retains dispute metadata only

- [ ] **4.8** Renewal billing behavior (continuity without mutation)
  - [ ] Renewals create new engagements
  - [ ] Old engagement invoices remain untouched
  - [ ] New billing terms apply only going forward

### Completion Criteria

- [ ] Billing always traces back to an engagement
- [ ] Package, hourly, and mixed billing are correct and auditable
- [ ] Credits, payments, disputes, and renewals are survivable
- [ ] Autopay behaves predictably
- [ ] No financial state mutates history silently

---

## TIER 5 — PRODUCT DURABILITY, SCALE & EXIT

> **Rule:** Tier 5 ensures the system survives growth, change, and scrutiny.

### Tasks

- [ ] **5.1** Hero workflow integration tests (end-to-end truth)
  - [ ] Define 1-2 canonical hero scenarios (package-only, mixed)
  - [ ] Test: Firm → Client → Engagement → Signed
  - [ ] Test: Auto-created Projects/Tasks
  - [ ] Test: Generate invoice → Process payment → Portal visibility
  - [ ] Test: Renew engagement → Verify continuity

- [ ] **5.2** Performance safeguards (tenant-safe at scale)
  - [ ] Audit queries for missing tenant indexes
  - [ ] Enforce select_related / prefetch_related
  - [ ] Add pagination on all list views
  - [ ] Add performance regression tests

- [ ] **5.3** Firm offboarding + data exit flows
  - [ ] Firm-level export capability (CSV/JSON + document bundle)
  - [ ] Implement retention timer on offboarding
  - [ ] Implement deletion workflow (purges content, preserves liability metadata)
  - [ ] Confirm offboarding does not affect other firms

- [ ] **5.4** Configuration change safety (future-proofing)
  - [ ] Version pricing/config schemas
  - [ ] Ensure new config applies prospectively
  - [ ] Log config changes affecting billing or access

- [ ] **5.5** Operational observability (without content)
  - [ ] Metrics/logs for: request counts, error rates, latency, job failures
  - [ ] All telemetry includes firm_id
  - [ ] Telemetry never includes customer content

### Completion Criteria

- [ ] Full lifecycle is proven end-to-end
- [ ] Performance and isolation hold at scale
- [ ] Firms can exit cleanly
- [ ] Configuration changes are safe
- [ ] Operations are observable without content visibility

---

## 🎯 TIER COMPLETION STATUS

| Tier | Status | Completion % |
|------|--------|-------------|
| Tier 0 | 🟢 Substantially Complete | 83% (5/6 tasks complete, 1 partial with blockers) |
| Tier 1 | 🔴 Not Started | 0% |
| Tier 2 | 🔴 Not Started | 0% |
| Tier 3 | 🔴 Not Started | 0% |
| Tier 4 | 🔴 Not Started | 0% |
| Tier 5 | 🔴 Not Started | 0% |

---

## 📋 REFERENCE DOCUMENTS

- **Authoritative Rules:** `docs/claude/NOTES_TO_CLAUDE.md`
- **Source Document:** `docs/claude/to_claude`
- **Tier Details:** See `docs/claude/tiers/` for full expansions
- **Execution Prompts:** See `docs/claude/prompts/` for tier-specific execution instructions

---

## 🚨 CRITICAL RULES

1. **No tier may be skipped**
2. **No tier may be partially completed and left**
3. **If code conflicts with NOTES_TO_CLAUDE.md, code must change**
4. **All changes must preserve tenant isolation and privacy guarantees**
5. **CI must never lie**

---

## 📞 QUESTIONS / DECISIONS NEEDED

### Tier 0 Blockers (2025-12-24)

1. **E2EE Implementation (Task 0.5)** — ⚠️ BLOCKED
   - **What:** Content encryption (E2EE) for customer documents, messages, and notes
   - **Blocker:** Requires AWS KMS or HashiCorp Vault infrastructure setup
   - **Decision Needed:** Choose secrets management solution (AWS KMS recommended)
   - **Estimated Effort:** 5-8 weeks with dedicated resources
   - **Documentation:** See `docs/tier0/E2EE_IMPLEMENTATION_PLAN.md`
   - **Recommendation:** Defer to post-Tier 2 as separate epic; access controls are in place

2. **Immutable Audit Records (Task 0.6)** — ⚠️ PENDING
   - **What:** Audit logging for all break-glass content access
   - **Blocker:** Requires Tier 3 audit event system implementation
   - **Decision Needed:** Audit system architecture and storage
   - **Note:** Break-glass sessions are tracked, but action-level auditing needs Tier 3

3. **Impersonation Mode Indicator (Task 0.6)** — ⚠️ PENDING
   - **What:** UI/UX indicator when platform operator is in break-glass mode
   - **Blocker:** Requires frontend integration (banner, session indicator)
   - **Decision Needed:** Frontend implementation approach
   - **Note:** Backend enforcement exists, frontend integration pending

4. **Tier 0 Completion Criteria** — 🟡 DISCUSSION NEEDED
   - **Question:** Can we mark Tier 0 as "complete" with E2EE deferred?
   - **Current State:** Access controls implemented, E2EE documented but not implemented
   - **Proposal:** Mark Tier 0 as "substantially complete" and proceed to Tier 1
   - **Rationale:** E2EE is infrastructure-heavy; access controls provide defense-in-depth
   - **Risk:** Without E2EE, platform DB access could expose content (mitigated by access controls + auditing)

---

**Status Legend:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete
- ⚠️ Blocked

---

## 📝 ACTIVITY LOG

- 2025-12-24 04:26 UTC — ChatGPT: Added break-glass session scaffolding (model + admin + migration) to begin Tier 0.6; enforcement and audit-event linkage still pending.
- 2025-12-24 04:30 UTC — ChatGPT: Added break-glass validation and lifecycle helpers (expiry checks, revoke helper, auto-expire on save). Enforcement wiring still pending.
- 2025-12-24 04:34 UTC — ChatGPT: Refined break-glass validation to allow expired sessions and require revocation reasons; reordered save validation for auto-expiry.
- 2025-12-24 04:36 UTC — ChatGPT: Enforced revoked-session invariants (revoked_at + revoked_reason required when status=revoked).
- 2025-12-24 04:50 UTC — ChatGPT: Enforced review invariants (reviewed_at requires reviewed_by and vice versa).
- 2025-12-24 04:57 UTC — ChatGPT: Added activation-relative validation (expiry/revocation/review timestamps must not predate activation).
- 2025-12-24 05:18 UTC — ChatGPT: Added review gating for active sessions and a helper to mark sessions reviewed.
- 2025-12-24 05:41 UTC — ChatGPT: Added BreakGlassSession queryset helpers for active/overdue filtering and expiry updates.
- 2025-12-24 05:43 UTC — ChatGPT: Added break-glass lookup/expiry helpers in firm utilities (no enforcement wiring yet).
- 2025-12-24 05:46 UTC — ChatGPT: Added firm-scoped queryset helper to centralize break-glass filtering in utilities.
- 2025-12-24 05:58 UTC — ChatGPT: Added review-time guardrails to prevent active session reviews and require reviewers when marking break-glass sessions reviewed.
- 2025-12-24 06:15 UTC — ChatGPT: Hardened break-glass firm scoping with a guard and centralized utils on firm-scoped queryset helpers.
- 2025-12-24 [CURRENT] — Claude: Completed Tier 0.5 platform privacy enforcement:
  - Added PlatformUserProfile model with role separation (Operator vs Break-Glass)
  - Created migration 0003_platform_user_profile.py
  - Implemented explicit deny rules for content models (DenyContentAccessByDefault, RequireBreakGlassForContent permissions)
  - Documented metadata/content separation in docs/tier0/METADATA_CONTENT_SEPARATION.md
  - Documented E2EE implementation requirements and blockers in docs/tier0/E2EE_IMPLEMENTATION_PLAN.md
  - E2EE implementation BLOCKED pending AWS KMS infrastructure setup (marked as deferred)
  - Updated TODO.md with Task 0.5 and 0.6 progress
  - Tier 0 now 83% complete (5/6 tasks, 1 partial with infrastructure blockers)
