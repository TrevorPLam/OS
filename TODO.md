# ConsultantPro - Task List

**Last Updated:** January 1, 2026 (Updated to reflect completed features)

---

## High Priority Tasks

### Critical Blockers (MISSING Features - Need Migrations)

- [x] **MISSING-7** API Layer Completion - All underlying models now have migrations ✅
- [x] **MISSING-8** Snippets System - Migration created: snippets/0001_initial.py (345 lines, 3 models) ✅
- [x] **MISSING-9** User Profile Customization - Migration verified: firm/0012_user_profiles.py exists ✅
- [x] **MISSING-10** Lead Scoring Automation - Models verified in crm/0006 migration (ScoringRule, ScoreAdjustment) ✅
- [x] **MISSING-11** SMS Integration - Migration created: sms/0001_initial.py (790 lines, 6 models) ✅
- [x] **MISSING-12** Calendar Sync (Google/Outlook) - Migration verified: calendar/0002_calendar_sync.py (CalendarConnection with OAuth) ✅

**Status:** ✅ All migrations complete - Platform is now deployable
- All 8 modules now have initial migrations (snippets, sms, pricing, delivery, knowledge, onboarding, orchestration, support)
- All Django system check errors fixed (20 duplicate index names, 1 related_name clash)
- All foreign key references resolved (Contact, EngagementLine models added)
- All indexes properly named

**Effort Completed:** System check fixes + 18 migration files created

---

## Medium Priority Tasks Progress

**Status:** 5 of 14 Integration & Enterprise features completed (36%)
- ✅ SMS service integration (Full Twilio integration with 6 models)
- ✅ Calendar sync OAuth models (Partial - models exist, full sync in progress)
- ✅ RBAC/ABAC policy system (12 module visibility classes, 5 portal scope classes)
- ✅ General automation/workflow engine (Orchestration module with retry/DLQ)
- ✅ API versioning strategy (v1 API with versioning and deprecation policies)

**Remaining High-Value Items:**
- SSO/OAuth authentication (Google/Microsoft)
- SAML support for enterprise SSO
- Multi-Factor Authentication (MFA)
- QuickBooks Online integration
- Xero accounting integration
- E-signature integration (DocuSign/HelloSign)
- Materialized views for reporting performance
- Document co-authoring with real-time collaboration (Very High Complexity)

**Deferred Items:**
- Slack API integration (placeholder implemented)
- E-signature workflow (placeholder implemented)

---

## Medium Priority Tasks

### Integration & External Dependencies

- [ ] Slack API integration (`src/modules/core/notifications.py`) - **Deferred** (placeholder implemented)
- [x] **SMS service integration** - ✅ **COMPLETED** (sms/0001_initial.py: 6 models, 790 lines; full Twilio integration in src/modules/sms/)
- [ ] E-signature workflow (`src/modules/clients/views.py`) - **Deferred**
- [x] **Email/calendar sync integration (Google/Outlook)** - ✅ **PARTIALLY COMPLETED** (OAuth models exist in calendar/oauth_models.py; CalendarConnection model with OAuth credentials)
- [ ] Document co-authoring with real-time collaboration - **Very High Complexity** (32-48 hours)

### Enterprise Features

- [ ] Implement SSO/OAuth (Google/Microsoft) authentication
- [ ] Add SAML support for enterprise SSO
- [ ] Implement Multi-Factor Authentication (MFA)
- [x] **Build RBAC/ABAC policy system with object-level permissions** - ✅ **COMPLETED** (src/modules/auth/role_permissions.py: 12 module visibility classes, 5 portal scope classes; firm/models.py: 6 staff roles with least-privilege defaults - see TODO_COMPLETED.md DOC-27.1)
- [ ] Add QuickBooks Online integration
- [ ] Add Xero accounting integration
- [ ] Implement e-signature integration (DocuSign/HelloSign)
- [x] **Build general automation/workflow engine with rule builder** - ✅ **COMPLETED** (Orchestration module: src/modules/orchestration/ - OrchestrationDefinition, OrchestrationExecution, StepExecution models with retry/DLQ)
- [x] **Add API versioning strategy and backward compatibility** - ✅ **COMPLETED** (Dec 2025: /api/v1/ prefix, API_VERSIONING_POLICY.md, API_DEPRECATION_POLICY.md - see TODO_COMPLETED.md ASSESS-I5.1)
- [ ] Implement materialized views for reporting performance

---

## Low Priority Tasks

### Platform Transformation

- [ ] Build unified event bus for cross-module automation
- [ ] Implement SCIM provisioning for automated user management
- [ ] Add audit review UI with query/filter/export capabilities
- [ ] Build integration marketplace scaffolding
- [ ] Implement records management system with immutability
- [ ] Add operational observability without content access
- [ ] Build custom dashboard builder with widget system
- [ ] Implement ERP connectors for enterprise customers
- [ ] Add AI-powered lead scoring and sales automation
- [ ] Build comprehensive PSA operations suite (Planning/Analytics)

---

## Notes

- **Focus:** Complete High Priority blockers first (MISSING features migrations)
- **Next Steps:** Resolve missing migrations and model references before deploying new features
- **Completed Work:** See [TODO_COMPLETED.md](./TODO_COMPLETED.md) for historical reference

---

## Reference Documentation

- [System Invariants](spec/SYSTEM_INVARIANTS.md)
- [Platform Capabilities Inventory](docs/03-reference/platform-capabilities.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Implementation Assessment](docs/ARCHIVE/roadmap-legacy-2025-12-30/IMPLEMENTATION_ASSESSMENT.md)
