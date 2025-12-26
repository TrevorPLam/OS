# ConsultantPro - Current Work & Roadmap

**Last Updated:** December 26, 2025

---

## 🎯 Current Focus: Tier 4 - Billing & Monetization

**Progress:** 63% Complete (5/8 complete, 1/8 partial, 2/8 documented)

### Active Tasks

- [ ] **4.2** Package fee invoicing (Documented - Implementation in progress)
- [ ] **4.6** Recurring payments/autopay workflow (Partial - Models ready)
- [ ] **4.7** Handle payment failures, disputes, and chargebacks

### Recently Completed

- [x] **4.1** Enforce billing invariants ✅
- [x] **4.3** Hourly billing with approval gates ✅
- [x] **4.4** Mixed billing reporting ✅
- [x] **4.5** Credit ledger ✅
- [x] **4.8** Renewal billing behavior ✅

---

## 🟢 Completed Tiers

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

- [ ] **5.1** Hero workflow integration tests
- [ ] **5.2** Performance safeguards (tenant-safe at scale)
- [ ] **5.3** Firm offboarding + data exit flows
- [ ] **5.4** Configuration change safety
- [ ] **5.5** Operational observability (without content)

---

## 📋 Platform Capabilities Roadmap

**For a comprehensive inventory of what exists and what's missing, see [Platform Capabilities Inventory](docs/03-reference/platform-capabilities.md)**

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
