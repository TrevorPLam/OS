# Changelog

All notable changes to ConsultantPro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Priority #1: Active Work Items
- ✅ Organization-based multi-account logic in portal views (DOC-26.1 account switcher)
- ✅ Step handler dispatch implementation in orchestration executor
- ✅ Link uploaded documents to Contact if available in portal views
- ✅ Staff notification on appointment cancellation in portal views

### Added - Priority #2: Assessment Remediation
- ✅ ASSESS-G18.5: Stripe reconciliation service with daily cron support
  - Cross-checks Invoice status vs Stripe API
  - Flags mismatches for manual review
  - Management command: `python manage.py reconcile_stripe`
- ✅ ASSESS-G18.5b: S3 reconciliation service
  - Verifies document Version records match S3 objects
  - Detects missing files
  - Management command: `python manage.py reconcile_s3`
- ✅ ASSESS-D4.6: Test/prod environment alignment (Postgres enforcement in conftest.py)

### Platform Progress
- **5 out of 6 tiers complete (83% of platform foundation)**
- Tier 5 (Durability, Scale & Exit) - In Progress

---

## [0.5.0] - 2025-12-26

### Added - Tier 4: Billing & Monetization (100% Complete)
- Package fee invoicing with auto-generation and duplicate prevention
- Recurring payments/autopay workflow with Stripe integration
- Payment failure tracking, dispute management, and chargeback handling
- Renewal billing behavior with version control
- Mixed billing reporting (package vs hourly revenue breakdown)
- Credit ledger system with immutable audit trail
- Time entry approval gates preventing unauthorized billing
- Billing invariants enforcing engagement linkage

### Added - Tier 0: Foundational Safety (100% Complete)
- Break-glass audit integration with immutable logging
- Break-glass session revocation audit events
- Complete audit trail for all break-glass access

### Documentation
- Comprehensive Tier 4 deployment guides:
  - `docs/tier4/PACKAGE_INVOICE_DEPLOYMENT.md`
  - `docs/tier4/AUTOPAY_STATUS.md`
  - `docs/tier4/PAYMENT_FAILURE_STATUS.md`
- Updated tier system documentation
- Session archives created for historical documentation

---

## [0.4.0] - 2025-12-25

### Added - Tier 3: Data Integrity & Privacy (100% Complete)
- Immutable audit event system with full taxonomy
- Purge/tombstone system for content deletion with metadata retention
- Audit review ownership and cadence documentation
- Privacy-first support workflows
- Document signing lifecycle with evidence retention

### Added - Tier 1: Schema Truth & CI Truth (100% Complete)
- Comprehensive safety test suite in `tests/safety/`
- All database migrations applied and verified
- Backend boots without crashes
- CI pipeline honesty (no exit-zero patterns)

### Added - Tier 2: Authorization & Ownership (100% Complete)
- Organization model for cross-client collaboration (opt-in)
- Portal authorization with defense-in-depth
- Explicit permissions on all 33 ViewSets
- Tenant context for all async job signals
- Firm-scoped querysets audit (zero unsafe patterns)

### Documentation
- `docs/tier3/AUDIT_EVENT_SYSTEM.md`
- `docs/tier3/AUDIT_REVIEW_OWNERSHIP.md`
- `docs/tier3/PRIVACY_FIRST_SUPPORT.md`
- `docs/tier3/DOCUMENT_SIGNING_LIFECYCLE.md`
- `docs/tier2/PORTAL_AUTHORIZATION_ARCHITECTURE.md`
- `docs/tier2/ORGANIZATION_CROSS_CLIENT_ACCESS.md`
- `docs/tier2/ASYNC_JOB_TENANT_CONTEXT.md`
- `docs/tier2/FIRM_SCOPED_QUERYSETS_AUDIT.md`
- `docs/tier2/VIEWSET_PERMISSION_AUDIT.md`
- `docs/tier1/TIER1_PROGRESS_SUMMARY.md`

---

## [0.3.0] - 2025-12-24

### Added - Core Feature Implementations
- Lead scoring with calculation logic (CRM)
- Pipeline stages with validation (CRM)
- Activity timeline model with comprehensive tracking (CRM)
- Task dependencies with blocking relationships (Projects)
- Milestone tracking with completion status (Projects)
- Expense tracking with billable flag (Projects/Finance)
- Retainer balance tracking (Finance)
- WIP (Work in Progress) tracking (Finance)
- Document retention policy fields (Documents)
- Legal hold mechanism for documents (Documents)

### Documentation
- Platform capabilities inventory updated with all 10 simple features
- Feature verification completed and documented

---

## [0.2.0] - 2025-12-24

### Added - Foundation
- Platform privacy enforcement with role separation
- Metadata/content separation architecture
- E2EE implementation plan (blocked on infrastructure)
- User model abstraction (AUTH_USER_MODEL everywhere)
- CI pipeline improvements (removed --exit-zero patterns)

### Documentation
- `docs/tier0/METADATA_CONTENT_SEPARATION.md`
- `docs/tier0/E2EE_IMPLEMENTATION_PLAN.md`
- `docs/tier0/PORTAL_CONTAINMENT.md`

---

## [0.1.0] - Initial Release

### Added - Core Platform
- Multi-tenant architecture with firm-level isolation
- JWT authentication
- CRM module (Lead, Prospect, Campaign, Proposal, Contract)
- Clients module (Client, ClientEngagement, ClientPortalUser)
- Projects module (Project, Task, TimeEntry)
- Finance module (Invoice, Bill, LedgerEntry)
- Documents module (Folder, Document, DocumentVersion)
- Assets module (Asset, AssetCategory)
- REST API with DRF
- PostgreSQL database
- Docker Compose setup
- React frontend with TypeScript

### Documentation
- Getting Started tutorial
- Architecture overview
- API usage guide
- Production deployment guide
- Tier system reference
- Contributing guide
- Security policy

---

## Version History Summary

| Version | Date | Focus | Tiers Complete |
|---------|------|-------|----------------|
| 0.5.0 | 2025-12-26 | Billing & Monetization | 5/6 (83%) |
| 0.4.0 | 2025-12-25 | Data Integrity & Privacy | 4/6 (67%) |
| 0.3.0 | 2025-12-24 | Core Features | 3/6 (50%) |
| 0.2.0 | 2025-12-24 | Platform Privacy | 2/6 (33%) |
| 0.1.0 | Initial | Foundation | 1/6 (17%) |

---

## Detailed Change History

For detailed commit-level changes, see:
- **Git History:** `git log --oneline`
- **GitHub Releases:** https://github.com/TrevorPLam/OS/releases
- **Pull Requests:** https://github.com/TrevorPLam/OS/pulls?q=is%3Apr

For archived session summaries and detailed progress notes, see:
- `docs/05-decisions/session-archives/`
