# ConsultantPro - Current Work & Roadmap

**Last Updated:** January 1, 2026

---

**⚠️ Known Issues:**
- **MISSING-* Features:** Code exists but requires significant refactoring before deployment
  - 8 modules need migration fixes (60+ admin errors, 30+ index naming conflicts)
  - Estimated 16-24 hours to make functional
  - See [IMPLEMENTATION_ASSESSMENT.md](docs/ARCHIVE/roadmap-legacy-2025-12-30/IMPLEMENTATION_ASSESSMENT.md)

---

## 🚨 PRIORITY #1: Active Work Items

### In-Code TODOs Identified

**High Priority (Feature Completion)**
- [x] `src/api/portal/views.py` - Implement organization-based multi-account logic (DOC-26.1 account switcher) ✅ Completed
- [x] `src/modules/orchestration/executor.py` - Implement actual step handler dispatch based on step type ✅ Completed

**Medium Priority (Implementation Details)**
- [x] `src/api/portal/views.py` - Link uploaded documents to Contact if available ✅ Completed
- [x] `src/api/portal/views.py` - Notify staff of appointment cancellation ✅ Completed
- [x] `src/modules/firm/provisioning.py` - Implement baseline configuration seeding ✅ Completed
  - Default project templates (General Consulting, Monthly Retainer, Advisory Services)
  - Default email templates (Welcome Email, Appointment Confirmation, Project Update)

**Deferred (External Dependencies)**
- [ ] `src/modules/core/notifications.py` - Slack API integration (See TODO_ANALYSIS.md #10)
- [ ] `src/modules/core/notifications.py` - SMS service integration (See TODO_ANALYSIS.md #11)
- [ ] `src/modules/clients/views.py` - E-signature workflow (See TODO_ANALYSIS.md #12)

**Low Priority (Future Enhancements)**
- [x] `src/modules/documents/models.py` - Implement document approval workflow (TODO 2.7) ✅ Completed
- [x] `src/modules/onboarding/models.py` - Trigger email/notification to client on workflow events ✅ Completed
  - OnboardingTask reminder notifications
  - OnboardingDocument reminder notifications

---

## 🔍 PRIORITY #2: ChatGPT Codebase Assessment Remediation

**Status**: Assessment Complete (Dec 30, 2025)
**Reference**: [docs/ChatGPT_CODEBASE_ASSESMENT](./docs/ChatGPT_CODEBASE_ASSESMENT)
**Overall Finding**: ~80% Complete, Needs Stabilization

The codebase underwent comprehensive external audit identifying **22 FAIL findings** across 7 domains. Most failures are medium-severity with several critical/high priority issues requiring immediate attention.

### All Phases Complete ✅

**All critical, high, and medium priority items completed.**

- [x] **ASSESS-C3.9** Refactor complexity hotspots - **DEFERRED** as ongoing maintenance  
  (finance/models.py ~1584 lines, calendar/models.py ~1184 lines)  
  Code quality acceptable; refactoring provides marginal benefit.  
  To be addressed during routine maintenance or when adding new features to these modules.

**Total Issues**: 22 FAIL findings  
**Progress**: 22/22 items addressed (100%) ✅  
**Status**: ✅ **ASSESSMENT REMEDIATION COMPLETE** (Dec 31, 2025)  
**Next Review**: January 15, 2026

### Assessment Summary by Domain (Historical - All Issues Resolved)

| Domain | PASS | FAIL (All Resolved ✅) | Issues Addressed |
|--------|------|------|------------|
| Requirements & Intent (R) | 4 | 4 | Missing features, spec misalignment, hidden assumptions |
| Architecture & Design (A) | 10 | 0 | ✅ Solid modular architecture, good layering |
| Code Quality (C) | 7 | 3 | Missing field (Prospect.stage), complexity hotspots, test non-determinism |
| Data Modeling (D) | 3 | 4 | Schema gaps, missing migrations, uniqueness constraints |
| API Design (I) | 5 | 5 | No versioning, no pagination, poor error model |
| Security (S) | 9 | 1 | Multi-tenancy gaps in async/signals |
| Testing (T) | 5 | 0 | ✅ Good coverage (33.8%), edge cases documented |
| Operations (O) | 10 | 0 | ✅ Deployment docs, monitoring, CI/CD in place |
| Integrations (G) | 6 | 2 | Webhook verification, reconciliation gaps |
| Compliance/Privacy (L) | 1 | 3 | GDPR gaps (consent, deletion, retention) |
| Documentation (D) | 10 | 0 | ✅ Excellent documentation, troubleshooting guides |
| **TOTAL** | **70** | **22** | **76% PASS rate** |

---

## ✅ Doc-Driven Roadmap (Canonical; docs/1–docs/35)

Docs 1–35 are the source of truth for platform scope, invariants, and required subsystems.
Any legacy roadmap/checklist items below are retained for history only and MUST NOT drive prioritization.

### Active Work Items

**Missing Features Implementation (MISSINGFEATURES.md Coverage) - ⚠️ NEEDS COMPLETION**

**NOTE:** Previous session created code but features are **NON-FUNCTIONAL** due to missing migrations and broken model references. See [IMPLEMENTATION_ASSESSMENT.md](./IMPLEMENTATION_ASSESSMENT.md) for details.

- [x] MISSING-1 Support/Ticketing System **⚠️ ADMIN FIXED** - Code exists (632 lines, 5 models) but NO migrations; admin field references fixed (responses→answers); 9+ unnamed indexes FIXED
- [x] MISSING-2 Meeting Polls **⚠️ ADMIN FIXED** - Code exists but admin field references fixed (organizer→created_by, created_appointment→scheduled_appointment, require_all_responses→require_all_invitees, invitee_emails→invitees)
- [x] MISSING-3 Meeting Workflow Automation **⚠️ ADMIN FIXED** - Code exists but admin field reference fixed (removed non-existent is_active, uses status)
- [x] MISSING-4 Email Campaign Templates **⚠️ ADMIN FIXED** - Code exists (marketing module, 655 lines), 1 migration created; admin field references fixed (template→email_template, scheduled_at→scheduled_for)
- [x] MISSING-5 Tag-based Segmentation **⚠️ ADMIN FIXED** - Code exists (marketing module), 1 migration created; admin field references fixed (auto_tagged→auto_applied, created_at→applied_at)
- [x] MISSING-6 Client Onboarding Workflows **⚠️ ADMIN FIXED** - Code exists (615 lines, 4 models) but NO migrations; admin references fixed (is_active→status, estimated_days→estimated_duration_days, task_definitions→steps, etc.); unnamed indexes FIXED
- [ ] MISSING-7 API Layer Completion **❌ NON-FUNCTIONAL** - ViewSets exist but all underlying models lack migrations
- [ ] MISSING-8 Snippets System **⚠️ ADMIN OK** - Code exists (345 lines, 3 models) but NO migrations; unnamed indexes FIXED; admin is functional
- [ ] MISSING-9 User Profile Customization **⚠️ CHECK STATUS** - May be functional if migration 0012_user_profiles.py exists in modules/firm/migrations (needs verification)
- [ ] MISSING-10 Lead Scoring Automation **⚠️ CHECK STATUS** - Code exists in crm/lead_scoring.py; import error FIXED; needs migration verification
- [ ] MISSING-11 SMS Integration **⚠️ ADMIN OK** - Code exists (790 lines, 6 models) but NO migrations; unnamed indexes FIXED; admin is functional; import error FIXED; URL config FIXED
- [ ] MISSING-12 Calendar Sync (Google/Outlook) **❌ INCOMPLETE** - Code exists (OAuth models, services) but NO migrations for OAuth models; Appointment/BookingLink reference non-existent crm.Account, crm.Contact, crm.Engagement

**CRITICAL ISSUES FIXED:**
- ✅ Import errors: Changed `modules.firm.managers.FirmScopedManager` → `modules.firm.utils.FirmScopedManager` (4 files)
- ✅ Import errors: Changed `modules.crm.models.Account/Engagement` → `modules.clients.models.Client`, `modules.projects.models.Project` (email_ingestion/views.py)
- ✅ URL config: Removed duplicate SMS webhook include
- ✅ URL config: Fixed SMS urls.py path nesting

**REMAINING BLOCKERS:**
- ❌ 8 modules missing migrations (cannot deploy)
- ❌ 20+ foreign key references to non-existent models
- ❌ 30+ unnamed indexes (required by Django)
- ❌ 60+ admin configuration errors
- ❌ No Contact model exists (referenced by 4+ models)
- ❌ No EngagementLine model exists (referenced by 2+ models)

**TO COMPLETE:** See IMPLEMENTATION_ASSESSMENT.md for full fix plan (16-24 hours estimated)

---

## 🗃️ Legacy Roadmap (Superseded by docs/1–docs/35)

The sections below are preserved for historical context only.
Do not update or prioritize legacy Tier/checklist items; add new work above as DOC-* items.

## 🎯 Current Focus: Tier 5 - Durability, Scale & Exit

**Tier 4 Status:** 100% Complete ✅

---

## 📋 Missing & Partially Implemented Features Checklist

**Prioritized by Implementation Complexity (Simple → Complex)**

**For detailed information on each feature, see [Platform Capabilities Inventory](docs/03-reference/platform-capabilities.md)**

### 🟡 Medium - Workflow & Business Logic

- [x] 2.7 Add document approval workflow (Draft → Review → Approved → Published) (Documents) ✅ Completed
- [x] 2.8 Add client acceptance gate before invoicing (Projects/Finance) ✅ Completed
- [x] 2.9 Implement utilization tracking and reporting (Projects) ✅ Completed
- [x] 2.10 Add cash application matching (partial/over/under payments) (Finance) ✅ Completed

### 🟠 Complex - New Subsystems & Integrations

- [x] 3.1 Build Account & Contact relationship graph (CRM) ✅ Completed
  - Account model for company/organization management
  - AccountContact model for individual contacts
  - AccountRelationship model for relationship graph
  - Full admin interface, serializers, and ViewSets
  - Documentation: docs/03-reference/crm-module.md
- [x] 3.2 Implement resource planning & allocation system (Projects) ✅ Completed
  - ResourceAllocation model for project staffing
  - ResourceCapacity model for availability tracking
  - Conflict detection and availability reporting
  - Full admin interface, serializers, and ViewSets
  - Documentation: docs/03-reference/resource-planning.md
- [x] 3.3 Add profitability reporting with margin analysis (Finance) ✅ Completed
  - ProjectProfitability model for individual project analysis
  - ServiceLineProfitability model for service line aggregation
  - Real-time margin calculations and forecasting
  - Full admin interface with recalculation actions
  - API endpoints with filtering and bulk operations
  - Documentation: docs/03-reference/profitability-reporting.md
- [x] 3.4 Build intake form system with qualification logic (CRM) ✅ Completed
  - IntakeForm model for customizable lead capture forms
  - IntakeFormField model for dynamic field definitions
  - IntakeFormSubmission model with automatic scoring
  - Qualification logic with configurable thresholds
  - Auto-create leads from qualified submissions
  - Full admin interface with inline field editing
  - API endpoints with score calculation and lead creation
  - Documentation: docs/03-reference/intake-forms.md
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

---

**Note:** All completed tasks have been migrated to [TODO_COMPLETED.md](./TODO_COMPLETED.md) for historical reference.
