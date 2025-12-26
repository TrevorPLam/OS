# Platform Capabilities Inventory

**Last Updated:** December 25, 2025

This document provides a comprehensive inventory of ConsultantPro's capabilities, mapping what exists in the current codebase and identifying missing components relative to a full-featured professional services automation (PSA) platform.

## Purpose

This reference document serves to:
- Document implemented features and their locations in the codebase
- Identify gaps between current implementation and target capabilities
- Guide roadmap prioritization and development planning
- Provide context for architectural decisions

## Table of Contents

1. [Current Implementation Summary](#current-implementation-summary)
2. [Platform Foundations](#platform-foundations)
3. [CRM Components](#crm-components)
4. [Client Qualification & Fee Calculator](#client-qualification--fee-calculator)
5. [Project / Work Management](#project--work-management)
6. [Document Management](#document-management)
7. [AP/AR Components](#apar-components)
8. [PSA / Practice Operations](#psa--practice-operations)
9. [End-to-End Workflow](#end-to-end-workflow)

---

## Current Implementation Summary

### What the Codebase Already Has

ConsultantPro currently includes the following core capabilities:

#### 1. Multi-Tenant Firm Boundary & Safety Primitives
**Location:** `src/modules/firm/*`

- ✅ **Firm Model:** Multi-tenant boundary with strict isolation
- ✅ **FirmMembership:** User-to-firm relationships with role flags
- ✅ **Audit System:** Event logging with metadata-only tracking (`audit.py`)
- ✅ **Permissions:** Coarse capability flags and break-glass hooks (`permissions.py`)
- ✅ **Middleware:** Firm context resolution and validation (`middleware.py`)

**Documentation:** [Tier 0: Foundational Safety](../tier0/PORTAL_CONTAINMENT.md)

#### 2. Authentication (Basic)
**Location:** `src/modules/auth/*`

- ✅ **JWT Authentication:** Login/logout via DRF SimpleJWT
- ✅ **User Registration:** New user account creation
- ✅ **Password Management:** Change password functionality
- ✅ **Token Refresh:** JWT token refresh mechanism

**Documentation:** [API Usage Guide](./api-usage.md#authentication)

#### 3. Core Privacy/Security Utilities
**Location:** `src/modules/core/`

- ✅ **Field-Level Encryption:** `encryption.py` - Encrypt sensitive fields at rest
- ✅ **Purge/Tombstone Scaffolding:** `purge.py` - Content deletion with metadata retention
- ✅ **Firm-Scoped Managers:** Automatic tenant filtering on querysets

**Documentation:** [Tier 3: Data Integrity & Privacy](../tier3/PRIVACY_FIRST_SUPPORT.md)

#### 4. CRM (Pre-Sale) CRUD Models
**Location:** `src/modules/crm/*`

- ✅ **Lead:** Initial contact/inquiry tracking
- ✅ **Prospect:** Qualified leads
- ✅ **Campaign:** Marketing campaign management
- ✅ **Proposal:** Pricing proposals for prospects
- ✅ **Contract:** Signed agreements with terms
- ✅ **Automation via Signals:** Basic workflow automation (`signals.py`)

**Documentation:** [Architecture Overview - Data Model](../04-explanation/architecture-overview.md#data-model)

#### 5. Client/Post-Sale Module
**Location:** `src/modules/clients/*`, `src/api/portal/*`

- ✅ **Client:** Post-sale client entity
- ✅ **ClientEngagement:** Client engagement tracking
- ✅ **ClientPortalUser:** Portal access for clients
- ✅ **ClientNote:** Notes on client interactions
- ✅ **Portal Endpoints:** Client-facing API endpoints
  - ✅ Chat threads/messages (`ClientChatThread`, `ClientMessage`)
  - ✅ Invoice visibility in portal
  - ✅ Contract/proposal visibility in portal

**Documentation:** [Portal Authorization Architecture](../tier2/PORTAL_AUTHORIZATION_ARCHITECTURE.md)

#### 6. Project Management (PM) Basics
**Location:** `src/modules/projects/*`

- ✅ **Project:** Core project entity
- ✅ **Task:** Task tracking within projects
- ✅ **TimeEntry:** Time tracking for tasks/projects
- ✅ **State Invariants:** Basic validation rules (`signals.py`)
- ✅ **UI Pages:** Projects, Kanban, Time Tracking (`src/frontend/src/pages/`)

**Documentation:** [Architecture Overview - Data Model](../04-explanation/architecture-overview.md#data-model)

#### 7. Document Management (DMS) Basics
**Location:** `src/modules/documents/*`

- ✅ **Folder:** Hierarchical folder structure
- ✅ **Document:** Document metadata and storage
- ✅ **DocumentVersion:** Version history tracking
- ✅ **S3 Presigned URLs:** Secure file upload/download (`services.py`)
- ✅ **Encryption:** S3 pointer and fingerprint encryption

**Documentation:** [Tier 3: Document Signing Lifecycle](../tier3/DOCUMENT_SIGNING_LIFECYCLE.md)

#### 8. Finance Basics
**Location:** `src/modules/finance/*`, `src/api/finance/webhooks.py`

- ✅ **Invoice:** AR invoicing
- ✅ **Bill:** AP bill tracking
- ✅ **LedgerEntry:** Financial ledger
- ✅ **CreditLedgerEntry:** Credits and payments tracking
- ✅ **Payment Failure Objects:** `PaymentFailure`, `PaymentDispute`, `PaymentChargeback`
- ✅ **Stripe Webhook Handler:** Payment processor integration (`webhooks.py`)
- ✅ **Billing Commands:** Invoice generation workflows (`management/commands/`)

**Documentation:** 
- [Credit Ledger System](../tier4/CREDIT_LEDGER_SYSTEM.md)
- [Payment Failure Handling](../tier4/PAYMENT_FAILURE_HANDLING.md)
- [Billing Invariants](../tier4/BILLING_INVARIANTS_AND_ARCHITECTURE.md)

#### 9. Asset Management
**Location:** `src/modules/assets/*`

- ✅ **Asset:** Basic asset tracking
- ✅ **AssetCategory:** Asset categorization

---

## Platform Foundations

Cross-cutting components that support all modules.

### 1. Identity, Access, and Governance

#### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **Firm Membership + Coarse Permissions:** Boolean capability flags on `FirmMembership` model
  - Location: `src/modules/firm/models.py`
- ✅ **Platform Privacy Enforcement:** Metadata-only access patterns with break-glass hooks
  - Location: `src/modules/firm/permissions.py`
- ✅ **Audit Event System:** Immutable audit logging
  - Location: `src/modules/firm/audit.py`
  - Documentation: [Audit Event System](../tier3/AUDIT_EVENT_SYSTEM.md)

#### Missing Components

**Authentication & Identity:**
- ❌ **SSO/OAuth Providers:** Google, Microsoft, enterprise auth
- ❌ **SAML Support:** Enterprise single sign-on
- ❌ **SCIM Provisioning:** Automated user provisioning
- ❌ **Multi-Factor Authentication (MFA):** Additional security layer
- ❌ **Session/Device Policies:** Device trust and session management

**Authorization & Access Control:**
- ❌ **True RBAC/ABAC Policy System:** 
  - Object-level permissions (granular resource access)
  - Permission sets/roles as first-class objects
  - Role inheritance and composition
  - Per-module permission scopes
- ❌ **Environment-Level Policy:** Dev/stage/prod enforcement rules
- ❌ **Security Policy Configuration:** Centralized policy management
- ❌ **Administrative Governance UI/API:** Self-service access management

**Audit & Compliance:**
- ❌ **Audit Review Features:**
  - Query and filtering capabilities
  - Export and retention management
  - Immutable evidence workflows
  - Note: Logger exists but operational review surfaces do not

**Impact:** Without advanced IAM, the platform cannot support enterprise customers requiring SSO, granular permissions, or compliance-grade audit trails.

### 2. Integration Fabric

#### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **REST CRUD Endpoints:** DRF routers for all modules
  - Location: `src/api/*`, `src/modules/*/urls.py`
  - Documentation: [API Usage Guide](./api-usage.md)
- ✅ **Stripe Webhook Handler:** Payment processor events
  - Location: `src/api/finance/webhooks.py`

#### Missing Components

**Integration Framework:**
- ❌ **General Integration Framework:**
  - Connector abstraction layer
  - Sync job scheduling and execution
  - Retry logic with exponential backoff
  - Idempotency guarantees
  - Integration logs and observability
  - Reconciliation tooling for drift detection

**Webhook Platform:**
- ❌ **Webhooks as Platform Feature:**
  - Subscribe/dispatch mechanism
  - Event catalog and schema registry
  - Webhook delivery guarantees
  - Retry and dead-letter queue
  - Beyond Stripe (general-purpose)

**API Infrastructure:**
- ❌ **Bulk APIs:** Batch operations for efficiency
- ❌ **API Versioning Strategy:** Backward compatibility management
- ❌ **Rate Limiting:** Advanced rate limiting (currently basic)
- ❌ **API Keys/Service Accounts:** Machine-to-machine authentication
- ❌ **Tenant-Scoped Integration Credentials:** Secure credential vaulting

**Native Connectors:**
- ❌ **Email/Calendar Integration:** Sync and activity capture
- ❌ **Accounting Integration:** QuickBooks Online, Xero
- ❌ **E-Signature Integration:** DocuSign, HelloSign
- ❌ **Storage Integration:** Google Drive, Dropbox, Box
- ❌ **Marketplace Scaffolding:** Third-party connector ecosystem

**Impact:** Without an integration fabric, firms must manually enter data from other systems, reducing efficiency and increasing errors.

### 3. Automation Engine

#### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **Module-Local Automation via Django Signals:**
  - CRM: Proposal → Contract workflows (`src/modules/crm/signals.py`)
  - Projects: State transition validation (`src/modules/projects/signals.py`)
- ✅ **Scheduled/Command Workflows:**
  - Finance: Invoice generation (`src/modules/finance/management/commands/`)

#### Missing Components

**Workflow Engine:**
- ❌ **Rule/Event-Driven Automation as Product:**
  - Condition definitions (when X happens, if Y is true)
  - Trigger catalog (events that start workflows)
  - Action definitions (what to do)
  - Routing and approval workflows
  - Visual workflow builder UI

**Runtime & Observability:**
- ❌ **Unified Event Bus/Workflow Runtime:**
  - Centralized event processing
  - Workflow execution logs
  - Retry logic and compensation
  - Dead-letter queue semantics
  - Performance monitoring

**Enforcement:**
- ❌ **Bypass Prevention Mechanisms:**
  - Hard gates blocking downstream actions
  - Upstream state validation
  - Preventing "shadow processes" (manual workarounds)

**Impact:** Without a workflow engine, business processes remain ad-hoc, requiring manual intervention and allowing inconsistent execution.

### 4. Reporting/Analytics

#### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **Frontend Dashboard:** Client-side metrics computation
  - Location: `src/frontend/src/api/dashboard.ts`
  - Note: Calls multiple endpoints and aggregates client-side

#### Missing Components

**Server-Side Reporting:**
- ❌ **Operational Dashboards:**
  - Pipeline conversion/progress reporting
  - Workload/resource visibility
  - Portfolio rollups and summaries

**Data Layer:**
- ❌ **Reporting Data Model:**
  - Materialized views for performance
  - Pre-aggregated metrics
  - Historical trend tracking

**Access & Distribution:**
- ❌ **Permissions for Reporting:** Who can see what reports
- ❌ **Export Functionality:** PDF, Excel, CSV export
- ❌ **Scheduled Reporting:** Automated report delivery

**Impact:** Without server-side reporting, users must manually compile data, and dashboards are slow when querying large datasets.

---

## CRM Components

Professional services-oriented customer relationship management.

### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **Pre-Sale Object Set:**
  - Lead, Prospect, Campaign, Proposal, Contract
  - Location: `src/modules/crm/models.py`
- ✅ **Basic Workflow Automation:**
  - Proposal → Contract creation
  - Location: `src/modules/crm/signals.py`

### Missing Components

#### 1. Account & Contact Graph
**Status:** ❌ Not Implemented

**Missing:**
- **Account/Company Entity:** Canonical company/organization model
- **Contact Entity:** Individual contacts (separate from User)
- **Relationship Graph:** Multi-relationship reality
  - One person, multiple roles across multiple accounts
  - Account hierarchies (parent/subsidiary)
  - Contact-to-account relationship history

**Impact:** Cannot accurately represent complex B2B relationships or track individuals across multiple client organizations.

#### 2. Activities Timeline
**Status:** ❌ Not Implemented

**Missing:**
- **Activity Types:** Emails, calls, meetings, tasks, notes
- **Timeline Model:** Chronological activity feed
- **Associations:** Link activities to accounts, contacts, deals
- **Capture Mechanisms:** Email integration, manual entry, automated logging

**Impact:** Sales and client history is fragmented; no single source of truth for client interactions.

#### 3. Pipeline & Stage Governance
**Status:** ⚠️ Partial (static stages only)

**Present:**
- Basic Lead and Prospect stages (implied in models)

**Missing:**
- **Configurable Pipeline System:**
  - Custom pipeline definitions
  - Stage definitions with metadata
  - Required fields per stage
  - Close criteria and validation
  - Guardrails preventing invalid transitions
- **Stage-Specific Automation:** Triggers tied to stage changes
- **Pipeline Reporting:** Conversion rates, velocity, forecasting

**Impact:** Teams cannot customize sales process to their methodology; no enforcement of sales best practices.

#### 4. Sales/Marketing Automation
**Status:** ⚠️ Minimal (static lead scoring only)

**Present:**
- Lead scoring field exists (but not computed)

**Missing:**
- **Sequences & Follow-Ups:** Automated email/task sequences
- **Scoring Rules:** Dynamic lead/account scoring based on behavior
- **Nurture Journeys:** Multi-touch campaigns with branching logic
- **Campaign Analytics:** ROI tracking, attribution modeling

**Impact:** Marketing and sales teams must manually follow up; no automated nurture or qualification.

#### 5. Professional Services Add-Ons
**Status:** ❌ Not Implemented

**Missing:**
- **Email/Calendar Sync:**
  - Two-way sync with Gmail, Outlook
  - Email-to-record capture (log emails to leads/contacts)
  - Meeting scheduling and tracking

- **CRM → Project Handoff:**
  - Explicitly marked as TODO in `src/modules/crm/signals.py`:
    - "TODO: create initial project skeleton"
    - "TODO: set up billing schedule"
  - No automated onboarding workflow

- **E-Sign Integration:**
  - Send proposals/contracts for signature
  - Track signature status
  - Store signed documents as compliance artifacts

- **Rich Portal Touchpoints:**
  - CRM timeline visible to clients (where appropriate)
  - Proposal acceptance via portal
  - Client-visible project roadmap

**Impact:** Handoff from sales to delivery is manual and error-prone; no seamless client experience from proposal to project start.

---

## Client Qualification & Fee Calculator

Intake, qualification, and pricing/quoting (CPQ) system.

### Present (Small Fragments)

**Current Capabilities:**
- ⚠️ **Proposal Entity:** Includes pricing fields
  - Location: `src/modules/crm/models.py`
  - Note: Not a calculator/CPQ system, just a static proposal

### Missing Components

#### 1. Intake Capture System
**Status:** ❌ Not Implemented

**Missing:**
- **Public Intake Forms:**
  - Customizable form builder
  - Required field validation
  - Document request workflows (upload requirements)
- **Source Tracking:** UTM parameters, referral tracking
- **Scheduling Confirmations:** Book initial consultation
- **Automated Routing:** Assign to appropriate team member

**Impact:** All leads must be manually entered; no self-service inquiry process.

#### 2. Qualification Logic
**Status:** ❌ Not Implemented

**Missing:**
- **Enforceable Gates:**
  - Bad-fit rules (auto-disqualify based on criteria)
  - Routing/approval workflows
  - Cannot bypass intake (no backdoor to create clients)
- **Qualification Scoring:** Systematic fit assessment
- **Disqualification Tracking:** Reason codes, follow-up nurture

**Impact:** No systematic way to filter bad-fit prospects; wasted sales effort on unqualified leads.

#### 3. Pricing/Quoting Engine (CPQ)
**Status:** ❌ Not Implemented

**Missing:**
- **Multiple Pricing Models:**
  - Fixed fee (flat rate)
  - Time & Materials (hourly with caps)
  - Value-based (outcome-based pricing)
  - Retainer (recurring)
  - Mixed (combination pricing)

- **Pricing Components:**
  - Line items with quantities
  - Discount rules (volume, promotional)
  - Tax calculation
  - Approval thresholds (discount limits)

- **Proposal Generation:**
  - Templates with variable substitution
  - PDF generation
  - E-signature ready
  - Version history

- **CPQ for Complex Bids:**
  - Multi-phase engagements
  - Optional add-ons
  - Conditional pricing (if X, then Y)

**Impact:** All pricing is manual and unstructured; no guided selling or pricing consistency.

#### 4. End-to-End SSOT Linkage
**Status:** ⚠️ Partial (contracts referenced by projects)

**Present:**
- Projects can reference contracts (implicit linkage)

**Missing:**
- **Pricing Truth Object:** Single source for "what was sold"
  - Links intake → qualification → pricing → contract → engagement → delivery
  - Immutable record of agreed scope and price
  - Variance tracking (scope creep, change orders)
- **Demand → Delivery → Resourcing → Financials Flow:**
  - Proposal pricing → project budget
  - Project plan → resource allocation
  - Time tracking → billing
  - Actuals vs. estimate reporting

**Impact:** No single source of truth for "what was sold vs. what was delivered"; scope disputes and margin leakage.

---

## Project / Work Management

Execution and tracking of client work.

### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **Core Execution Objects:**
  - Project, Task, TimeEntry
  - Location: `src/modules/projects/models.py`
- ✅ **Basic State Transitions/Metrics:**
  - Logging via signals
  - Location: `src/modules/projects/signals.py`
- ✅ **UI Pages:**
  - Projects list, Kanban board, Time Tracking
  - Location: `src/frontend/src/pages/`

### Missing Components

#### 1. Work Object Model Depth
**Status:** ⚠️ Partial

**Present:**
- `ClientEngagement` exists in `src/modules/clients/models.py`

**Missing:**
- **Engagement as First-Class Object:**
  - Between Client and Project (currently not designed around it)
  - Engagement-level SOWs, budgets, approvals
  - Multi-project engagements

- **Templates/Recurrence:**
  - Project templates (SOPs, checklists)
  - Recurring projects (monthly retainer work)
  - Template versioning

- **SOP/Checklist Execution:**
  - Checklist items as tasks
  - Completion verification
  - Quality gates

- **Dependencies:**
  - Task dependencies (Task A blocks Task B)
  - Milestone tracking
  - Critical path calculation

- **Handoff Semantics:**
  - Formal handoff between team members
  - Acceptance/approval gates
  - Deliverable sign-off

**Impact:** Projects are flat lists of tasks; no structure for complex multi-phase engagements or repeatable processes.

#### 2. Communication-in-Context
**Status:** ⚠️ Partial (portal chat exists)

**Present:**
- Portal chat: `ClientChatThread`, `ClientMessage`
  - Location: `src/modules/clients/models.py`

**Missing:**
- **Email-to-Task Capture:** Create tasks from email
- **Decision Log:** Track key decisions with context
- **Structured Workflow Truth:**
  - Comments threaded to tasks/projects
  - @mentions and notifications
  - Approval/rejection workflows
  - File attachments in context

**Impact:** Decisions and discussions happen outside the system (email, Slack); no audit trail of "why we did X."

#### 3. Reporting Views
**Status:** ❌ Not Implemented

**Missing:**
- **Gantt/Roadmaps:** Visual timeline of projects
- **Workload/Resource Allocation:** Who's working on what, capacity planning
- **Portfolio Views:** All projects at a glance, health indicators
- **Burndown/Velocity Charts:** Agile-style progress tracking

**Impact:** No high-level view of work in progress; managers cannot see bottlenecks or over-allocation.

---

## Document Management

Secure storage, versioning, and collaboration on documents.

### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **Folder/Document/Version Structure:**
  - Location: `src/modules/documents/models.py`
- ✅ **S3 Presigned URL Service:**
  - Secure upload/download
  - Location: `src/modules/documents/services.py`
- ✅ **Encryption:**
  - S3 pointers and fingerprints encrypted
  - Uses `src/modules/core/encryption`

### Missing Components

#### 1. Real-Time Collaboration
**Status:** ❌ Not Implemented

**Missing:**
- **Real-Time Co-Authoring:**
  - Multiple users editing simultaneously
  - Operational transformation or CRDT for conflict resolution
  - Live cursor presence

- **Asynchronous Check-In/Check-Out:**
  - Lock document for editing
  - Check out / check in workflow
  - Conflict resolution on concurrent edits

- **Mode Switching:**
  - Toggle between real-time and check-in/check-out
  - Without integrity loss or version conflicts

**Impact:** Teams cannot collaborate on documents within the platform; must use external tools (Google Docs, Office 365).

#### 2. Document Workflow Automation
**Status:** ❌ Not Implemented

**Missing:**
- **Review → Approval → Publish Pipeline:**
  - Draft → In Review → Approved → Published states
  - Auditable routing (who approved when)
  - Decision history (approval/rejection reasons)
  - Notification on state changes

- **Workflow Configuration:**
  - Custom approval chains
  - Parallel vs. serial approvals
  - Conditional routing rules

**Impact:** Document approval is manual and ad-hoc; no audit trail of who approved what.

#### 3. External Collaboration UX
**Status:** ❌ Not Implemented

**Missing:**
- **Secure Sharing Links:**
  - Granular permissions (view, comment, edit)
  - Expiration dates
  - Watermarking (for sensitive docs)
  - Access logging (who viewed when)

- **Client Upload Requests:**
  - Request specific documents from clients
  - Track completion status
  - Validation rules (file type, size)

**Impact:** Sharing documents with clients or external parties requires email or insecure file transfers.

#### 4. Compliance Posture Features
**Status:** ⚠️ Partial (encryption exists, compliance features do not)

**Present:**
- Field-level encryption for sensitive data

**Missing:**
- **Retention Schedules:**
  - Policy-driven retention (keep for X years)
  - Auto-deletion on schedule
  - Legal hold overrides

- **Legal Holds:**
  - Suspend auto-deletion for litigation
  - Immutable hold tracking

- **Records Management:**
  - Declare documents as records
  - Immutable once declared
  - Retention policy enforcement

- **Access Reporting:**
  - "Who accessed what when" reports
  - Note: General audit exists, but DMS-specific compliance surfaces do not

**Impact:** Cannot demonstrate compliance with data retention or access regulations (e.g., GDPR, SOX).

---

## AP/AR Components

Accounts Payable and Accounts Receivable with exception handling.

### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **AR: Invoice + Payment Exceptions:**
  - Invoice model
  - Payment failure, chargeback, dispute models
  - Stripe webhook handling
  - Location: `src/modules/finance/models.py`, `src/api/finance/webhooks.py`

- ✅ **AP: Bill:**
  - Basic bill model
  - Location: `src/modules/finance/models.py`

- ✅ **Billing Workflow Scaffolding:**
  - Some automation exists
  - Location: `src/modules/finance/billing.py`

### Missing Components

#### 1. AP Capture & Validation Pipeline
**Status:** ❌ Not Implemented

**Current State:**
- Bill model exists but no workflow

**Missing:**
- **State Machine:** Received → Validated → Approved → Scheduled → Cleared
- **Capture Mechanisms:**
  - Email-to-AP (forward bills to system)
  - OCR extraction (scan invoices)
  - Manual entry form

- **Validation/Dedupe:**
  - Duplicate detection (same vendor, amount, date)
  - Validation rules (PO matching, budget checks)
  - Exception flagging

- **Approval Routing:**
  - Hierarchical approvals (manager → director → CFO)
  - Approval thresholds (auto-approve under $X)
  - Project-owner confirmation (did we receive the work?)

**Impact:** Bills are manually entered and approved outside the system; no audit trail or process enforcement.

#### 2. AP Approval Routing Tied to PM
**Status:** ❌ Not Implemented

**Missing:**
- **Project-Owner Confirmation:**
  - Bill references a project
  - Project owner must confirm receipt of goods/services
  - Before payment is scheduled

- **Engagement Ownership Integration:**
  - Link AP approvals to engagement ownership
  - Prevent payment without delivery confirmation

**Impact:** Paying for work not received; no accountability loop between delivery and payment.

#### 3. AR Contract-Aware Billing Triggers
**Status:** ⚠️ Partial (invoice generation exists, triggers incomplete)

**Present:**
- Invoice model and manual/command-driven generation

**Missing:**
- **Milestone-Driven Invoicing:**
  - Trigger invoice on project milestone completion
  - Automated invoice generation on milestone dates

- **WIP-Driven Invoicing:**
  - Accrue work-in-progress
  - Invoice on schedule (monthly) or threshold

- **Delivery/Acceptance Gating:**
  - Client must accept deliverable before invoice
  - Prevent invoicing for disputed work

- **Dispute Handling Beyond Chargebacks:**
  - Client disputes invoice (not just payment processor chargebacks)
  - Dispute resolution workflow
  - Credit memo issuance

**Impact:** Billing is manual and not tied to project milestones; disputes are handled outside the system.

#### 4. Collections & Cash Application
**Status:** ❌ Not Implemented

**Missing:**
- **Dunning Workflows:**
  - Automated reminder emails
  - Escalation sequences (friendly → firm → collection agency)
  - Configurable schedules

- **Payment Matching:**
  - Partial payments (less than invoice)
  - Over-payments (more than invoice)
  - Under-payments (short payment)
  - Batch payments (one check for multiple invoices)

- **Cash Application Audit Trail:**
  - Log how payment was applied
  - Adjustments and corrections
  - Reconciliation with bank statements

**Impact:** Collections are manual; no systematic follow-up on overdue invoices. Cash application is error-prone.

#### 5. Anti-Shadow-Spreadsheet Guardrails
**Status:** ❌ Not Implemented

**Missing:**
- **Integration Failure Handling:**
  - Detect when Stripe webhook fails
  - Retry logic with alerting
  - Manual reconciliation queue

- **Reconciliation Tooling:**
  - Compare system records to bank statements
  - Flag discrepancies
  - Audit trail of reconciliation

- **Operational Dashboards:**
  - "What is stuck and why"
  - Aging reports (30/60/90 days overdue)
  - Exception queue (failed payments, disputes, mismatches)

**Impact:** Finance teams maintain shadow spreadsheets because they don't trust the system; defeats purpose of integrated platform.

---

## PSA / Practice Operations

Resource planning, utilization, and profitability management.

### Present (Partial Implementation)

**Current Capabilities:**
- ✅ **Time Tracking:** TimeEntry model
  - Location: `src/modules/projects/models.py`
- ✅ **Basic Billing Objects:** Invoice, Bill, Ledger
  - Location: `src/modules/finance/models.py`

### Missing Components

#### 1. Resource Planning & Utilization
**Status:** ❌ Not Implemented

**Missing:**
- **Capacity Forecasting:**
  - Available hours per person
  - Committed hours (project allocations)
  - Pipeline hours (proposed work)

- **Staffing Models:**
  - Assign people to projects (with percentage allocation)
  - Skill-based matching (right person for the job)
  - Bench management (unallocated staff)

- **Utilization Targets:**
  - Target billable percentage per role
  - Actual vs. target tracking
  - Utilization reports

- **Workload Balancing:**
  - Identify over-allocated staff
  - Identify under-allocated staff
  - Rebalancing workflows

**Impact:** No visibility into who's overworked or underutilized; staffing decisions are reactive, not proactive.

#### 2. Expense Tracking & Approvals
**Status:** ❌ Not Implemented

**Missing:**
- **Expense Reports:**
  - Employee expense submission
  - Receipt upload
  - Expense categories (travel, meals, supplies)

- **Approval Workflows:**
  - Manager approval
  - Reimbursement processing
  - Billable vs. non-billable expenses

- **Client Billing:**
  - Pass-through expenses to clients
  - Markup rules
  - Expense invoicing

**Impact:** Expense reimbursement is manual and outside the system; no linking of expenses to projects for billing.

#### 3. Profitability Reporting
**Status:** ❌ Not Implemented

**Missing:**
- **Margin Analysis:**
  - Revenue vs. cost per client/engagement/project
  - Gross margin, net margin
  - Margin trends over time

- **Realization Analysis:**
  - Billed hours vs. total hours (write-offs)
  - Collection rate (billed vs. collected)
  - Realization percentage

- **WIP Reporting:**
  - Work-in-progress by project
  - Aging of WIP (how long since billed?)
  - WIP write-off analysis

**Impact:** No insight into which clients/projects are profitable; cannot make data-driven decisions on pricing or resource allocation.

#### 4. Retainers & WIP Accounting
**Status:** ⚠️ Partial (CreditLedgerEntry exists)

**Present:**
- Credit ledger for tracking credits/payments
  - Location: `src/modules/finance/models.py`
  - Documentation: [Credit Ledger System](../tier4/CREDIT_LEDGER_SYSTEM.md)

**Missing:**
- **Retainer Behaviors:**
  - Prepaid hours (burn down as work is done)
  - Retainer auto-renewal
  - Unused retainer handling (rollover, expire, refund)

- **WIP Accounting:**
  - Accrue unbilled time/expenses
  - WIP aging (flag old unbilled work)
  - WIP-to-invoice workflows

- **T&M Reconciliation:**
  - Compare time tracked to time billed
  - Approval of billable hours
  - Write-off reasons

**Impact:** Retainer and WIP accounting is manual; no systematic tracking of prepaid hours or unbilled work.

#### 5. Accounting Integrations
**Status:** ❌ Not Implemented

**Missing:**
- **QuickBooks Online (QBO) Integration:**
  - Sync invoices, bills, payments
  - Chart of accounts mapping
  - Customer/vendor sync

- **Xero Integration:** Same as QBO

- **General Ledger Sync:**
  - Push transactions to external accounting system
  - Reconciliation between systems

- **ERP Connectors:** For enterprise customers

**Impact:** Accountants must manually enter data into accounting systems; double-entry and reconciliation burden.

---

## End-to-End Workflow

How the platform supports a complete client lifecycle.

### What's Currently Wired

**Implemented Connections:**
- ✅ **CRM → Contract Creation:**
  - Proposals can activate Contracts
  - Signals acknowledge next steps (but don't implement them)
  - Location: `src/modules/crm/signals.py`
  - Note: TODOs exist for project skeleton and billing schedule

- ✅ **Portal Exposure:**
  - Portal endpoints expose projects, invoices, messages
  - Location: `src/api/portal/urls.py`
  - Documentation: [Portal Authorization Architecture](../tier2/PORTAL_AUTHORIZATION_ARCHITECTURE.md)

### Missing to Meet End-to-End Flow

#### 1. Closed Won → Engagement Creation
**Status:** ⚠️ Partially Wired (TODOs in code)

**Present:**
- Contract model exists
- Signals acknowledge intent

**Missing:**
- **Onboarding Project (Templated):**
  - Auto-create project from template
  - Checklist of onboarding tasks
  - Assign project owner
  - Governance gates (e.g., can't start billable work until onboarding complete)

- **Engagement Object:**
  - Link Contract → Engagement → Projects
  - Engagement-level budgets and approvals

**Impact:** Handoff from sales to delivery is manual; no automated onboarding kickoff.

#### 2. Document Lifecycle Workflow
**Status:** ❌ Not Implemented

**Missing:**
- **Create/Ingest → Co-Author/Review → Approve → Publish/Share:**
  - State machine for documents
  - Approval routing
  - Full action history (who did what when)
  - Client-facing publish (make visible in portal)

**Impact:** Document approval is informal; no audit trail for compliance.

#### 3. Service Delivery → Invoicing
**Status:** ⚠️ Partial (manual invoicing exists)

**Present:**
- Invoice model and manual creation

**Missing:**
- **Milestone-Triggered Invoicing:**
  - Project milestone complete → auto-generate invoice
  - Deliverable accepted → invoice
  - Recurring services → scheduled invoice

- **WIP/Acceptance Gating:**
  - Client acceptance before invoice
  - Dispute workflow if not accepted

**Impact:** Billing is manual and not tied to project milestones; invoicing lags delivery.

#### 4. Collections & Cash Application
**Status:** ❌ Not Implemented

**Missing:**
- **Dunning Workflow:**
  - Automated reminders
  - Escalation sequences
  - Collection agency handoff

- **Cash Application Workflow:**
  - Match payment to invoice(s)
  - Handle partial/over/under payments
  - Audit trail of application

**Impact:** Collections are manual; no systematic follow-up on overdue invoices.

#### 5. AP Running in Parallel
**Status:** ❌ Not Implemented

**Missing:**
- **Governed Exception-First Pipeline:**
  - Bill received → validation → approval → payment
  - Approvals tied to delivery ownership (PM confirms receipt)
  - Exception handling (disputes, mismatches, duplicates)

**Impact:** AP is manual and outside the system; no connection between paying vendors and receiving work.

---

## Summary & Roadmap Implications

### What Works Well Today

ConsultantPro has **solid foundations** for a multi-tenant PSA platform:
- ✅ **Security & Privacy:** Firm isolation, break-glass, audit logging
- ✅ **Core Modules:** CRM (pre-sale), Projects, Finance, Documents, Clients
- ✅ **API Infrastructure:** REST endpoints, JWT auth, Swagger docs
- ✅ **Multi-Tenant Architecture:** Firm-scoped querysets, portal containment

### Major Gaps

To reach feature parity with leading PSA platforms, ConsultantPro needs:

1. **Identity & Access Management (IAM):** SSO, MFA, RBAC, audit review surfaces
2. **Integration Fabric:** Webhooks, connectors (email, accounting, e-sign), sync jobs
3. **Automation Engine:** Workflow builder, event-driven triggers, approval routing
4. **Advanced CRM:** Account/contact graph, activities timeline, pipeline governance, sales automation
5. **CPQ System:** Intake forms, qualification, pricing engine, proposal generation
6. **Project Management Depth:** Templates, dependencies, milestones, resource allocation, Gantt charts
7. **Document Collaboration:** Co-authoring, workflow automation, external sharing, compliance features
8. **AP/AR Excellence:** Capture pipelines, approval routing, dunning, cash application, reconciliation
9. **PSA Operations:** Resource planning, utilization, profitability, retainer/WIP accounting, ERP integrations
10. **Reporting & Analytics:** Server-side dashboards, materialized views, scheduled reports

### Roadmap Priorities

See [TODO.md](../../TODO.md) for current prioritization. High-level sequence:

1. **Complete Tier 4:** Finish billing & monetization (in progress)
2. **Complete Tier 5:** Durability, scale, exit flows
3. **Post-Tier 5 (High Priority):** IAM, Integration Fabric, Automation Engine
4. **Medium Priority:** CRM depth, PM depth, Reporting
5. **Lower Priority:** Advanced AP/AR, PSA ops, Document collaboration

---

## Related Documentation

- **[Architecture Overview](../04-explanation/architecture-overview.md)** - High-level system design
- **[Tier System Reference](./tier-system.md)** - Current implementation tiers
- **[TODO.md](../../TODO.md)** - Current work and roadmap
- **[API Usage Guide](./api-usage.md)** - API documentation
- **[System Invariants](../../spec/SYSTEM_INVARIANTS.md)** - Core system rules

---

**Document Status:** ✅ Complete and Current (December 25, 2025)
