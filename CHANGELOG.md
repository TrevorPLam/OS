# Changelog

All notable changes to ConsultantPro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Dependency Management** (2026-01-03)
  - **DEP-CLEANUP-1, DEP-CLEANUP-2, DEP-CLEANUP-3**: Moved development dependencies to requirements-dev.txt
    - Moved testing tools (pytest, pytest-django, pytest-cov, coverage, factory-boy, faker) to requirements-dev.txt
    - Moved code quality tools (ruff, black) to requirements-dev.txt
    - Moved security scanning tools (safety, import-linter) to requirements-dev.txt
    - Updated CI/CD pipeline to install requirements-dev.txt for testing, linting, and security scanning jobs
    - Production Docker image now ~150-180MB smaller (no testing/dev tools in production)
    - BREAKING CHANGE: Development environments must install both requirements.txt AND requirements-dev.txt
      ```bash
      pip install -r requirements.txt -r requirements-dev.txt
      ```
  
  - **SEC-5**: Pin frontend dependency versions
    - Replaced caret (^) versions with exact versions in package.json
    - All dependencies now use exact versions from package-lock.json
    - Ensures reproducible builds across all environments
    - package-lock.json already committed to repository
    - Update process documented in SECURITY.md

---

## [0.7.0] - 2026-01-03

### Added

- **Pipeline & Deal Management - UI, Analytics & Automation** (2026-01-02)
  - **DEAL-3: Pipeline Visualization UI**
    - Kanban board with drag-and-drop stage transitions
    - Deal cards showing value, probability, weighted value, close date, and owner
    - Pipeline selector, search functionality, and stale deal filtering
    - Real-time metrics dashboard (total value, weighted value, deal count, avg deal size)
    - Visual stale deal indicators with warning badges
    - Responsive design for mobile, tablet, and desktop
    - Frontend routes: `/crm/deals`
    - Components: `Deals.tsx`, `Deals.css`
  
  - **DEAL-4: Forecasting & Analytics Dashboard**
    - Win/loss performance tracking with counts, values, and win rate calculation
    - Monthly revenue projections with interactive bar charts
    - Performance metrics (average deal size, sales cycle duration)
    - Pipeline distribution by stage with probability percentages
    - Top 5 reasons for lost deals analysis
    - Comprehensive analytics with visual metrics (color-coded: green=won, red=lost, blue=active, purple=rate)
    - Frontend routes: `/crm/deal-analytics`
    - Components: `DealAnalytics.tsx`, `DealAnalytics.css`
  
  - **DEAL-5: Assignment Automation**
    - Round-robin deal assignment algorithm with fair distribution
    - Territory-based, value-based, and source-based routing options
    - Stage automation triggers (assign user, create task, send notification, update field, run webhook)
    - Priority-based rule evaluation with condition matching (value range, source, pipeline/stage filters)
    - Configurable assignment rules with assignee pool management
    - Models: `AssignmentRule`, `StageAutomation`
    - Backend: `assignment_automation.py`
    - Note: Requires database migration to activate
  
  - **DEAL-6: Stale Deal Alerts & Splitting**
    - Automated stale deal detection based on inactivity threshold (default: 30 days)
    - Email reminder system with personalized messages to deal owners
    - Comprehensive stale deal reporting (by owner, pipeline, stage, age distribution)
    - Management command: `send_stale_deal_reminders` with `--dry-run` support
    - Daily cron job script for automated checks (`check_stale_deals.sh`)
    - Deal splitting support via `split_percentage` JSON field
    - New API endpoints:
      - `GET /api/crm/deals/stale_report/` - Comprehensive stale deal analytics
      - `POST /api/crm/deals/check_stale/` - Manually trigger stale check
      - `POST /api/crm/deals/send_stale_reminders/` - Send reminder emails with dry-run option
    - Backend: `deal_rotting_alerts.py`, `send_stale_deal_reminders.py`
  
  - **Documentation:**
    - Comprehensive implementation summary: [WORK_SUMMARY_DEAL_3-6.md](WORK_SUMMARY_DEAL_3-6.md)
    - Setup instructions for email reminders and cron jobs
    - Total implementation: ~2,600 lines across 10 new files and 4 modified files

- **Pipeline & Deal Management - Foundation** (2026-01-02)
  - **DEAL-1 & DEAL-2: Models and API** (previously documented)
  - Configurable sales pipelines with customizable stages (DEAL-1)
  - Deal model with value tracking, probability, and weighted forecasting
  - Deal-to-Project conversion workflow for won deals
  - Deal task management with priority and assignment
  - Stale deal detection based on activity tracking
  - Deal splitting support for multiple owners
  - Stage transition logic with activity logging
  - Comprehensive API endpoints:
    - Pipeline CRUD with analytics endpoint (`/api/crm/pipelines/`)
    - Pipeline stage management (`/api/crm/pipeline-stages/`)
    - Deal CRUD with stage transitions (`/api/crm/deals/`)
    - Deal task management (`/api/crm/deal-tasks/`)
    - Stale deals endpoint (`/api/crm/deals/stale/`)
    - Forecast endpoint with weighted values (`/api/crm/deals/forecast/`)
  - Django admin interfaces with custom actions for pipeline and deal management
  - Database models: Pipeline, PipelineStage, Deal, DealTask
  - Multi-tenant isolation for all pipeline and deal operations
  - Validation rules for stage-pipeline consistency
  - See [TODO.md](TODO.md) for full feature roadmap

- **Sprint 5: Performance & Reporting** (2026-01-01)
  - Materialized views for revenue and utilization reporting
  - Revenue reporting MV (`mv_revenue_by_project_month`) with 20-50x speedup
  - Utilization reporting MVs (`mv_utilization_by_user_week`, `mv_utilization_by_project_month`) with 15-100x speedup
  - Refresh management command (`refresh_materialized_views`) for scheduled daily refresh
  - REST API endpoints for revenue reporting (`/api/finance/revenue-reports/`)
  - Manual refresh, freshness check, and quarterly aggregation endpoints
  - Refresh monitoring with MVRefreshLog model and statistics endpoints
  - Full reporting metadata compliance per `REPORTING_METADATA.md` spec
  - 12 indexes across 3 materialized views for optimal query performance
  - Data age tracking and freshness indicators for all MV queries
  - Storage overhead <5% of base tables (~10MB per firm for 3 years data)
  - See [Sprint 5 Implementation Summary](docs/SPRINT_5_IMPLEMENTATION_SUMMARY.md)
  - See [Sprint 5 Query Analysis](docs/SPRINT_5_QUERY_ANALYSIS.md)

- **Sprint 4: E-Signature Integration** (2026-01-01)
  - DocuSign integration with OAuth 2.0 authentication
  - Envelope creation and send workflow for proposals
  - Webhook-based real-time status tracking with HMAC verification
  - Automatic proposal status updates on signature completion
  - REST API endpoints for connection and envelope management (`/api/v1/esignature/`)
  - Django admin interfaces for monitoring envelopes and webhook events
  - Comprehensive documentation and user guide
  - Database models: DocuSignConnection, Envelope, WebhookEvent
  - Encrypted OAuth token storage with automatic refresh (5-minute buffer)
  - Multi-tenant isolation for all e-signature operations
  - Integration with proposal acceptance workflow
  - See [Sprint 4 Implementation Summary](docs/SPRINT_4_IMPLEMENTATION_SUMMARY.md)
  - See [E-Signature User Guide](docs/esignature-user-guide.md)
  - See [ADR-004: E-Signature Provider Selection](docs/05-decisions/ADR-004-esignature-provider-selection.md)

- **Sprint 3: Accounting Integrations** (2026-01-01)
  - QuickBooks Online integration with OAuth 2.0 authentication
  - Xero integration with OAuth 2.0 authentication
  - Invoice sync - push invoices from ConsultantPro to accounting systems
  - Payment sync - pull payment data from accounting systems to update invoice status
  - Customer/Contact bidirectional sync between systems
  - REST API endpoints for connection management (`/api/v1/accounting/`)
  - Django admin interfaces for monitoring sync status
  - Comprehensive documentation and user guide
  - Database models: AccountingOAuthConnection, InvoiceSyncMapping, CustomerSyncMapping
  - Encrypted OAuth token storage with automatic refresh
  - Multi-tenant isolation for all accounting operations
  - See [Sprint 3 Implementation Summary](docs/SPRINT_3_IMPLEMENTATION_SUMMARY.md)

### Changed - Documentation Updates

- **TODO.md Maintenance Update** (January 1, 2026)
  - Marked 4 completed medium-priority tasks as done:
    - ✅ SMS service integration (full Twilio integration with 6 models)
    - ✅ RBAC/ABAC policy system (role-based permissions complete)
    - ✅ General automation/workflow engine (orchestration module complete)
    - ✅ API versioning strategy (v1 API with versioning and deprecation policies)
  - Marked 1 in-progress medium-priority task:
    - ⚠️ Email/calendar sync integration (OAuth models complete, full integration remaining)
  - Marked 1 completed low-priority task as done:
    - ✅ Operational observability (correlation IDs, metrics collectors, tenant-safe logging)
  - Added progress tracking: 29% completion (4 of 14 medium-priority features), 10% completion (1 of 10 low-priority features)
  - Marked deferred items (Slack API, E-signature workflow) with appropriate status
  - Updated "Last Updated" timestamp to January 1, 2026

### Added - Critical Migrations (MISSING Features)

- ✅ **MISSING-8**: Snippets System migrations created
  - Database migration: snippets/0001_initial.py
  - Models: Snippet, SnippetUsageLog, SnippetFolder (3 models, 345 lines of code)
  - HubSpot-style snippets for quick text insertion with variables
  
- ✅ **MISSING-11**: SMS Integration migrations created
  - Database migration: sms/0001_initial.py
  - Models: SMSPhoneNumber, SMSMessage, SMSConversation, SMSCampaign, SMSTemplate, SMSOptOut (6 models, 790 lines)
  - Two-way SMS conversations, campaigns, templates, and opt-out management
  
- ✅ Created initial migrations for 8 modules:
  - `snippets`: Snippet management system
  - `sms`: SMS messaging and campaigns
  - `pricing`: CPQ pricing engine (RuleSet, Quote, QuoteVersion)
  - `delivery`: Work delivery templates and instantiation
  - `knowledge`: Knowledge base management
  - `onboarding`: Client onboarding workflows
  - `orchestration`: Workflow orchestration engine
  - `support`: Support ticketing and SLA management
  - `recurrence`: Recurrence rules (regenerated from empty initial)

### Fixed - System Check Errors

- ✅ Fixed 20 duplicate index name errors across 13 modules
  - Fixed index naming conflicts in calendar (6 models), clients (4), communications (2), delivery (2), email_ingestion (2), finance (5), jobs (6), knowledge (3), marketing (2), orchestration (4), pricing (3), projects (2), recurrence (2)
  - Fixed related_name clash between finance.PaymentAllocation and projects.ResourceAllocation
  - All Django system checks now pass

### Verified - Existing Migrations

- ✅ **MISSING-9**: User Profile Customization - migration 0012_user_profiles.py verified in firm module
- ✅ **MISSING-10**: Lead Scoring Automation - models verified in crm/0006 migration (ScoringRule, ScoreAdjustment)
- ✅ **MISSING-12**: Calendar Sync (Google/Outlook) - CalendarConnection model verified in calendar/0002_calendar_sync.py

### Documentation

- Updated TODO.md to mark MISSING-8 through MISSING-12 as complete
- Updated CHANGELOG.md with migration completion status

### Platform Progress

- **All 5 critical MISSING feature migrations complete (100%)** ✅
- Platform now deployable: All models have migrations

---

### Added - Medium Workflow & Business Logic Features (2.7-2.10)
- ✅ Document approval workflow (Draft → Review → Approved → Published)
  - State transition methods: submit_for_review(), approve(), reject(), publish(), deprecate(), archive()
  - API endpoints: POST /api/documents/documents/{id}/{submit_for_review,approve,reject,publish}/
  - Audit trail with timestamps and user tracking for each transition
  - 15 comprehensive tests covering full lifecycle
- ✅ Client acceptance gate before invoicing
  - Project acceptance tracking: client_accepted, acceptance_date, accepted_by, acceptance_notes fields
  - Invoice generation gate: can_generate_invoice() blocks final invoicing for completed projects
  - API endpoint: POST /api/projects/projects/{id}/mark_client_accepted/
  - 13 comprehensive tests including invoice generation validation
- ✅ Utilization tracking and reporting
  - Project-level metrics: calculate_utilization_metrics() with billable/non-billable hours, utilization rate, budget variance
  - User-level metrics: calculate_user_utilization() with capacity analysis across projects
  - API endpoints: GET /api/projects/projects/{id}/utilization/, GET /api/projects/projects/team_utilization/
  - 16 comprehensive tests covering project and user metrics
- ✅ Cash application matching (partial/over/under payments)
  - Payment and PaymentAllocation models for tracking customer payments
  - Support for partial payments, overpayments, split allocations, multiple payments per invoice
  - Automatic invoice status updates (sent → partial → paid) with atomic F() expressions
  - API endpoints: POST /api/finance/payments/, POST /api/finance/payment-allocations/
  - Database migration: 0009_payment_payment_allocation.py
  - 17 comprehensive tests covering allocation scenarios

### Documentation
- Added IMPLEMENTATION_SUMMARY_2.7-2.10.md with comprehensive feature documentation
- Updated TODO.md to mark Medium features 2.7-2.10 as complete

### Platform Progress
- **4 out of 10 Medium features complete (40% of Medium tier)** ✅

### Notes
- Platform foundation complete: All 6 tiers finished (100%)
- Constitution compliance: 12/12 tasks complete (100%)
- Assessment remediation: 21/22 tasks complete (95%, 1 low-priority item deferred)
- Doc-driven roadmap: 33/33 active work items complete (100%)

---

## [0.6.0] - 2025-12-31

### Added - Tier 5: Durability, Scale & Exit (100% Complete)
- ✅ Hero workflow integration tests
- ✅ Performance safeguards (tenant-safe at scale)
- ✅ Firm offboarding and data exit flows
- ✅ Configuration change safety
- ✅ Operational observability (without content access)

### Fixed
- Fixed import error in `modules.core.observability` (added `get_correlation_id` alias)

### Documentation
- Updated TODO.md with accurate status (Dec 31, 2025)
- Updated README.md to reflect 100% tier completion
- Updated CHANGELOG.md with Tier 5 completion

### Platform Progress
- **6 out of 6 tiers complete (100% of platform foundation)** ✅
- All critical work from Constitution and Assessment complete
- Platform ready for production deployment

---

## [0.5.0] - 2025-12-26

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

### Platform Progress
- **5 out of 6 tiers complete (83% of platform foundation)**
- Tier 5 (Durability, Scale & Exit) - In Progress

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
| 0.7.0 | 2026-01-03 | Pipeline Management & Enterprise Security | 6/6 (100%) ✅ |
| 0.6.0 | 2025-12-31 | Durability, Scale & Exit | 6/6 (100%) ✅ |
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
