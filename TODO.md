# ConsultantPro - Task List

**Last Updated:** January 1, 2026

---

## High Priority Tasks

### Critical Blockers (MISSING Features - Need Migrations)

- [ ] **MISSING-7** API Layer Completion - ViewSets exist but all underlying models lack migrations
- [ ] **MISSING-8** Snippets System - Code exists (345 lines, 3 models) but NO migrations
- [ ] **MISSING-9** User Profile Customization - Verify migration 0012_user_profiles.py exists
- [ ] **MISSING-10** Lead Scoring Automation - Code exists in crm/lead_scoring.py; needs migration verification
- [ ] **MISSING-11** SMS Integration - Code exists (790 lines, 6 models) but NO migrations
- [ ] **MISSING-12** Calendar Sync (Google/Outlook) - Code exists but NO migrations for OAuth models; references non-existent crm models

**Status:** 8 modules missing migrations (cannot deploy)
- 20+ foreign key references to non-existent models
- 30+ unnamed indexes (required by Django)
- 60+ admin configuration errors
- No Contact model exists (referenced by 4+ models)
- No EngagementLine model exists (referenced by 2+ models)

**Estimated Effort:** 16-24 hours to make functional

---

## Medium Priority Tasks

### Integration & External Dependencies

- [ ] Slack API integration (`src/modules/core/notifications.py`)
- [ ] SMS service integration (`src/modules/core/notifications.py`)
- [ ] E-signature workflow (`src/modules/clients/views.py`)
- [ ] Email/calendar sync integration (Google/Outlook) - **Very High Complexity** (24-40 hours)
- [ ] Document co-authoring with real-time collaboration - **Very High Complexity** (32-48 hours)

### Enterprise Features

- [ ] Implement SSO/OAuth (Google/Microsoft) authentication
- [ ] Add SAML support for enterprise SSO
- [ ] Implement Multi-Factor Authentication (MFA)
- [ ] Build RBAC/ABAC policy system with object-level permissions
- [ ] Add QuickBooks Online integration
- [ ] Add Xero accounting integration
- [ ] Implement e-signature integration (DocuSign/HelloSign)
- [ ] Build general automation/workflow engine with rule builder
- [ ] Add API versioning strategy and backward compatibility
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
