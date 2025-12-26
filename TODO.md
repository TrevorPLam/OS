# ConsultantPro - Current Work & Roadmap

**Last Updated:** December 26, 2025

---

## 🎯 Current Focus: Tier 5 - Durability, Scale & Exit

**Tier 4 Status:** 100% Complete ✅

### Recently Completed (Tier 4)

- [x] **4.1** Enforce billing invariants ✅
- [x] **4.2** Package fee invoicing (Complete - see docs/tier4/PACKAGE_INVOICE_DEPLOYMENT.md) ✅
- [x] **4.3** Hourly billing with approval gates ✅
- [x] **4.4** Mixed billing reporting ✅
- [x] **4.5** Credit ledger ✅
- [x] **4.6** Recurring payments/autopay workflow (Complete - see docs/tier4/AUTOPAY_STATUS.md) ✅
- [x] **4.7** Payment failures, disputes, and chargebacks (Complete - see docs/tier4/PAYMENT_FAILURE_STATUS.md) ✅
- [x] **4.8** Renewal billing behavior ✅

---

## 🟢 Completed Tiers

### Tier 4: Billing & Monetization (100% Complete) ✅
- [x] 4.1: Enforce billing invariants
- [x] 4.2: Package fee invoicing
- [x] 4.3: Hourly billing with approval gates
- [x] 4.4: Mixed billing reporting
- [x] 4.5: Credit ledger
- [x] 4.6: Recurring payments/autopay workflow
- [x] 4.7: Payment failures, disputes, and chargebacks
- [x] 4.8: Renewal billing behavior

### Tier 0: Foundational Safety (100% Complete) ✅
- [x] Firm/Workspace tenancy
- [x] Firm context resolution
- [x] Firm + client scoping everywhere
- [x] Portal containment
- [x] Platform privacy enforcement (E2EE deferred - infrastructure dependency)
- [x] Break-glass audit records (fully integrated with Tier 3 audit system)

### Tier 1: Schema Truth & CI Truth (100% Complete) ✅
- [x] Fix deterministic backend crashes
- [x] Commit all missing migrations
- [x] Make CI honest
- [x] Add minimum safety test set

### Tier 2: Authorization & Ownership (100% Complete) ✅
- [x] Standardize permissions across all ViewSets
- [x] Replace direct User imports with AUTH_USER_MODEL
- [x] Add firm + client context to all async jobs
- [x] Firm-scoped querysets (zero global access)
- [x] Portal authorization (client-scoped, explicit allowlist)
- [x] Cross-client access within Organizations

### Tier 3: Data Integrity & Privacy (100% Complete) ✅
- [x] Purge semantics (tombstones, metadata retention)
- [x] Audit event taxonomy + retention policy
- [x] Audit review ownership and cadence
- [x] Privacy-first support workflows
- [x] Document signing lifecycle & evidence retention

---

## 🔜 Next: Tier 5 - Durability, Scale & Exit

### Upcoming Tasks (Not Yet Started)

- [x] **5.1** Hero workflow integration tests
- [x] **5.2** Performance safeguards (tenant-safe at scale)
- [x] **5.3** Firm offboarding + data exit flows
- [x] **5.4** Configuration change safety
- [x] **5.5** Operational observability (without content)

---

## 📋 Missing & Partially Implemented Features Checklist

**Prioritized by Implementation Complexity (Simple → Complex)**

**For detailed information on each feature, see [Platform Capabilities Inventory](docs/03-reference/platform-capabilities.md)**

### ✅ Simple - Core Model Enhancements (Quick Wins)

- [ ] 1.1 Add computed lead scoring field with basic calculation logic (CRM)
- [ ] 1.2 Add configurable pipeline stages with validation (CRM)
- [ ] 1.3 Add task dependencies field and basic dependency checking (Projects)
- [ ] 1.4 Add milestone tracking fields to projects (Projects)
- [ ] 1.5 Add expense tracking model with billable flag (Finance/Projects)
- [ ] 1.6 Add retainer balance tracking to client model (Finance)
- [ ] 1.7 Add document retention policy fields (Documents)
- [ ] 1.8 Add legal hold flag to documents (Documents)
- [ ] 1.9 Add WIP (Work in Progress) tracking fields (Finance)
- [ ] 1.10 Add activity type enum and activity timeline model (CRM)

### 🟡 Medium - Workflow & Business Logic

- [ ] 2.1 Implement Contract → Project creation workflow (CRM → Projects)
- [ ] 2.2 Add project template system with cloning (Projects)
- [ ] 2.3 Implement milestone-triggered invoice generation (Finance)
- [ ] 2.4 Add basic approval workflow for expenses (Finance)
- [ ] 2.5 Add AP bill state machine (Received → Validated → Approved → Paid) (Finance)
- [ ] 2.6 Implement dunning workflow for overdue invoices (Finance)
- [ ] 2.7 Add document approval workflow (Draft → Review → Approved → Published) (Documents)
- [ ] 2.8 Add client acceptance gate before invoicing (Projects/Finance)
- [ ] 2.9 Implement utilization tracking and reporting (Projects)
- [ ] 2.10 Add cash application matching (partial/over/under payments) (Finance)

### 🟠 Complex - New Subsystems & Integrations

- [ ] 3.1 Build Account & Contact relationship graph (CRM)
- [ ] 3.2 Implement resource planning & allocation system (Projects)
- [ ] 3.3 Add profitability reporting with margin analysis (Finance)
- [ ] 3.4 Build intake form system with qualification logic (CRM)
- [ ] 3.5 Implement CPQ (Configure-Price-Quote) engine (CRM)
- [ ] 3.6 Add Gantt chart/timeline view for projects (Projects)
- [ ] 3.7 Build general webhook platform (Integration)
- [ ] 3.8 Add email/calendar sync integration (Integration)
- [ ] 3.9 Implement document co-authoring with real-time collaboration (Documents)
- [ ] 3.10 Add secure external document sharing with permissions (Documents)

### 🔴 Advanced - Enterprise Features

- [ ] 4.1 Implement SSO/OAuth (Google/Microsoft) authentication (IAM)
- [ ] 4.2 Add SAML support for enterprise SSO (IAM)
- [ ] 4.3 Implement Multi-Factor Authentication (MFA) (IAM)
- [ ] 4.4 Build RBAC/ABAC policy system with object-level permissions (IAM)
- [ ] 4.5 Add QuickBooks Online integration (Integration)
- [ ] 4.6 Add Xero accounting integration (Integration)
- [ ] 4.7 Implement e-signature integration (DocuSign/HelloSign) (Integration)
- [ ] 4.8 Build general automation/workflow engine with rule builder (Automation)
- [ ] 4.9 Add API versioning strategy and backward compatibility (API)
- [ ] 4.10 Implement materialized views for reporting performance (Reporting)

### 🎯 Strategic - Platform Transformation

- [ ] 5.1 Build unified event bus for cross-module automation (Platform)
- [ ] 5.2 Implement SCIM provisioning for automated user management (IAM)
- [ ] 5.3 Add audit review UI with query/filter/export capabilities (Compliance)
- [ ] 5.4 Build integration marketplace scaffolding (Platform)
- [ ] 5.5 Implement records management system with immutability (Compliance)
- [ ] 5.6 Add operational observability without content access (Platform)
- [ ] 5.7 Build custom dashboard builder with widget system (Reporting)
- [ ] 5.8 Implement ERP connectors for enterprise customers (Integration)
- [ ] 5.9 Add AI-powered lead scoring and sales automation (CRM)
- [ ] 5.10 Build comprehensive PSA operations suite (Planning/Analytics)

---

### 📝 Implementation Notes

**Execution Strategy:**
1. Start with Simple features (1.1-1.10) - Low risk, immediate value
2. Progress to Medium features (2.1-2.10) - Build on existing foundations
3. Tackle Complex features (3.1-3.10) - New capabilities, higher ROI
4. Consider Advanced features (4.1-4.10) - Enterprise requirements
5. Plan Strategic features (5.1-5.10) - Long-term platform evolution

**Current Focus:** Complete Tier 5 first, then begin Simple checklist items.

---

## 📋 Legacy Roadmap Summary

### High Priority (Post-Tier 5)

1. **Identity & Access Management**
   - SSO/OAuth (Google/Microsoft), SAML, MFA, Advanced RBAC

2. **Integration Framework**
   - Webhook platform, Email/calendar sync, Accounting integrations, E-signature

3. **Automation Engine**
   - Rule-based workflows, Event-driven triggers, Approval routing

### Medium Priority

4. **CRM Enhancements** - Activities timeline, Pipeline governance, Lead scoring
5. **Project Management** - Dependencies, Resource allocation, Gantt charts
6. **Document Management** - Version control, Workflow automation, External collaboration

### Lower Priority

7. **Reporting & Analytics** - Custom dashboards, Materialized views, Export scheduling
8. **AP/AR Automation** - Bill capture, Collections & dunning, Cash application
9. **Practice Operations** - Resource planning, Utilization tracking, Profitability analysis

---

## ⚠️ Current Blockers

None - All tier work proceeding normally.

---

## 🚨 Critical Rules

1. **No tier may be skipped** - Complete each tier in order
2. **No tier may be partially completed** - Finish all tasks before moving on
3. **All changes preserve tenant isolation** - Security is non-negotiable
4. **CI must never lie** - Test failures must fail the build

---

## 📖 Reference

- **Tier Details:** [Tier System Reference](docs/03-reference/tier-system.md)
- **Activity Log:** [Activity Log](docs/03-reference/activity-log.md)
- **System Invariants:** [System Invariants](spec/SYSTEM_INVARIANTS.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
