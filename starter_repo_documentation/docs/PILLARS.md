# PILLARS.md — Core Platform Pillars
Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Dependencies: ARCHITECTURE.md; DOMAIN_MODEL.md

## Platform Pillars

ConsultantPro is organized around core functional pillars that represent major feature areas.

### 1. CRM & Sales

**Purpose:** Manage the full sales lifecycle from lead to customer.

**Key Features:**
- Lead capture and qualification
- Prospect management and nurturing
- Proposal generation and tracking
- Pipeline management and forecasting
- Deal tracking and conversion analytics

**Modules:** `crm/`

---

### 2. Client Management

**Purpose:** Post-sale client relationship management and self-service portal.

**Key Features:**
- Client records and relationships
- Branded client portal (custom domain, white-label)
- Document sharing and collaboration
- Portal messaging and notifications
- Client onboarding workflows

**Modules:** `clients/`, `onboarding/`

---

### 3. Project & Task Management

**Purpose:** Organize work, track progress, manage deliverables.

**Key Features:**
- Projects with milestones and tasks
- Time tracking and resource allocation
- Delivery templates and workflows
- Task dependencies and scheduling
- Progress reporting and analytics

**Modules:** `projects/`, `delivery/`, `orchestration/`

---

### 4. Finance & Billing

**Purpose:** Revenue management, invoicing, and payment processing.

**Key Features:**
- Invoice generation and tracking
- Payment processing (Stripe, Square)
- Recurring billing and subscriptions
- Expense tracking
- Financial reporting
- Accounting integration (QuickBooks, Xero)

**Modules:** `finance/`, `pricing/`, `accounting_integrations/`

---

### 5. Calendar & Scheduling

**Purpose:** Complete Calendly replacement with booking links and availability management.

**Key Features:**
- Event types with custom availability
- Booking links (public and private)
- Buffer times and daily limits
- Team scheduling and round-robin
- Calendar sync (Google, Microsoft)
- Appointment reminders and notifications

**Modules:** `calendar/`

---

### 6. Marketing Automation

**Purpose:** Marketing campaigns, email automation, and lead nurturing.

**Key Features:**
- Visual workflow builder (React Flow)
- Trigger-based automation (form submit, email action, etc.)
- Email campaigns with templates
- Contact segmentation and tagging
- A/B testing and analytics
- Landing pages and forms

**Modules:** `marketing/`, `automation/`

---

### 7. Communications

**Purpose:** Unified communication platform for email, SMS, and portal messages.

**Key Features:**
- Email ingestion and threading
- SMS messaging (Twilio)
- Portal messaging
- Conversation management
- Message templates and snippets
- Communication history and audit

**Modules:** `communications/`, `email_ingestion/`, `sms/`, `snippets/`

---

### 8. Documents & Knowledge

**Purpose:** Document management and organizational knowledge base.

**Key Features:**
- Document upload and versioning
- Folder organization and permissions
- Full-text search
- E-signature integration (DocuSign)
- Knowledge base (SOPs, training, playbooks)
- Document templates

**Modules:** `documents/`, `knowledge/`, `esignature/`

---

### 9. Support & Ticketing

**Purpose:** Customer support with SLA tracking and satisfaction metrics.

**Key Features:**
- Ticket management and routing
- SLA tracking and escalation
- Knowledge base integration
- Customer satisfaction surveys (NPS, CSAT)
- Support analytics and reporting

**Modules:** `support/`

---

### 10. Integrations

**Purpose:** Connect with external tools and services.

**Key Features:**
- Webhook platform for inbound/outbound events
- OAuth connection management
- Payment processing (Stripe, Square)
- Accounting (QuickBooks, Xero)
- E-signature (DocuSign)
- Identity providers (Google, Microsoft, Active Directory)
- SMS (Twilio)

**Modules:** `webhooks/`, `accounting_integrations/`, `esignature/`, `ad_sync/`

---

## Cross-Cutting Concerns

### Multi-Tenancy
- All pillars respect firm boundaries
- RLS enforcement at database level
- Firm context in middleware

### Audit & Compliance
- Sensitive operations logged
- GDPR compliance (data export, deletion)
- Break-glass access auditing

### Background Processing
- Job queue for asynchronous tasks
- Dead letter queue for failed jobs
- Retry logic and error handling

**Modules:** `jobs/`

---

## Pillar Dependencies

```
┌─────────────┐
│   firm/     │  ← Foundation (all depend on this)
│   auth/     │
└─────────────┘
      ↑
      │
┌─────┴─────────────────────────────────────┐
│                                           │
│  Business Pillars                         │
│  (crm, clients, projects, finance, etc.)  │
│                                           │
└───────────────────────────────────────────┘
      ↑
      │
┌─────┴─────────────────┐
│                       │
│  Supporting Services  │
│  (communications,     │
│   documents, etc.)    │
│                       │
└───────────────────────┘
```

## Module Organization

Each pillar may consist of one or more Django modules (apps). Modules follow the standard Django structure with models, views, serializers, URLs, and tests.

See [REPO_MAP.md](REPO_MAP.md) for detailed module structure.
