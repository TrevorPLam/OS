# ConsultantPro - Architectural Refactor Plan

## Executive Summary

This document outlines a fundamental architectural refactor to correctly separate **pre-sale (CRM)** from **post-sale (Clients)** operations, and restructure both Client Portal and Firm Portal to match the intended business logic.

---

## Table of Contents

1. [Current vs. Proposed Architecture](#current-vs-proposed-architecture)
2. [Backend Changes Required](#backend-changes-required)
3. [Frontend Restructuring](#frontend-restructuring)
4. [Client Portal Rebuild](#client-portal-rebuild)
5. [Firm Portal Reorganization](#firm-portal-reorganization)
6. [New Modules Required](#new-modules-required)
7. [Data Flow & Integration](#data-flow--integration)
8. [Implementation Phases](#implementation-phases)
9. [Definition of Done](#definition-of-done)

---

## Current vs. Proposed Architecture

### **CURRENT (Incorrect)**

```
CRM Module:
├── Clients (should not be here)
├── Proposals
└── Contracts

Client Portal:
└── Basic document viewer with placeholders

Navigation:
Dashboard → Clients → Proposals → Contracts → Projects → Time → Invoices → Docs
```

### **PROPOSED (Correct)**

```
CRM Module (Pre-Sale ONLY):
├── Leads (Marketing capture)
├── Prospects (Sales pipeline)
├── Proposals (Pre-sale quotes)
└── Marketing Campaigns

Clients Module (Post-Sale Hub):
├── Client List (searchable CRUD)
├── Per-Client Navigation:
│   ├── → Projects
│   ├── → Documents
│   ├── → Invoices
│   ├── → Contracts/Engagements
│   ├── → Communications
│   └── → Analytics

Client Portal (6 Sections):
├── 1. Dashboard (Analytics)
├── 2. Work (Checklists tied to firm projects)
├── 3. Chat (IM with assigned team, daily reset)
├── 4. Documents (Read-only + Upload folders)
├── 5. Billing (Invoices + Stripe/ACH payment)
└── 6. Engagement (Proposals/Contracts with versioning)

Firm Portal (Reorganized):
├── 1. Dashboard
├── 2. Communications (Email Triage, Chat, Message Board)
├── 3. Scheduling (Outlook/Gmail integrated)
├── 4. CRM (Marketing & Sales ONLY)
├── 5. Clients (Post-sale hub)
├── 6. Work (Projects/Tasks, Time)
├── 7. Documents (DMS)
├── 8. AR (Invoicing, Tracking)
├── 9. AP (Vendor, Payments)
├── 10. Assets
└── 11. Knowledge Center
```

---

## Backend Changes Required

### **1. Separate Clients from CRM**

#### **Current State:**
```python
# modules/crm/models.py
class Client(models.Model):
    company_name = ...
    status = ['lead', 'active', 'inactive', 'archived']  # WRONG - mixes pre/post sale
```

#### **Proposed State:**

**A. CRM Module (Pre-Sale):**
```python
# modules/crm/models.py

class Lead(models.Model):
    """Marketing-captured prospect"""
    company_name = models.CharField(max_length=255)
    source = models.CharField(max_length=100)  # 'website', 'referral', 'campaign'
    status = models.CharField(choices=[
        ('new', 'New Lead'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted to Prospect'),
        ('lost', 'Lost')
    ])
    captured_date = models.DateField()
    assigned_to = models.ForeignKey(User)  # Sales rep
    # Marketing fields
    campaign = models.ForeignKey('Campaign', null=True)
    lead_score = models.IntegerField(default=0)

class Prospect(models.Model):
    """Sales pipeline - active opportunity"""
    lead = models.ForeignKey(Lead, null=True)  # Origin
    company_name = models.CharField(max_length=255)
    pipeline_stage = models.CharField(choices=[
        ('discovery', 'Discovery'),
        ('proposal', 'Proposal Sent'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won - Converting to Client'),
        ('lost', 'Lost')
    ])
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2)
    close_date_estimate = models.DateField()
    assigned_to = models.ForeignKey(User)  # Account executive

class Proposal(models.Model):
    """Pre-sale proposal (STAYS in CRM)"""
    prospect = models.ForeignKey(Prospect)  # CHANGED from Client
    proposal_number = ...
    status = ['draft', 'sent', 'accepted', 'rejected']
    # When accepted → Creates Client + Contract

class Campaign(models.Model):
    """Marketing campaign tracking"""
    name = models.CharField(max_length=255)
    type = models.CharField(choices=[
        ('email', 'Email Campaign'),
        ('webinar', 'Webinar'),
        ('content', 'Content Marketing'),
        ('event', 'Event')
    ])
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    leads_generated = models.IntegerField(default=0)
```

**B. NEW Clients Module (Post-Sale):**
```python
# modules/clients/models.py

class Client(models.Model):
    """Post-sale client (created when Proposal accepted)"""
    # Origin tracking
    source_prospect = models.ForeignKey('crm.Prospect', null=True)
    source_proposal = models.ForeignKey('crm.Proposal', null=True)

    # Company info
    company_name = models.CharField(max_length=255, unique=True)
    primary_contact_name = models.CharField(max_length=255)
    primary_contact_email = models.EmailField()

    # Client status (post-sale only)
    status = models.CharField(choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive - No Active Projects'),
        ('terminated', 'Terminated')
    ])

    # Assigned team
    account_manager = models.ForeignKey(User, related_name='managed_clients')
    assigned_team = models.ManyToManyField(User, related_name='assigned_clients')

    # Portal access
    portal_enabled = models.BooleanField(default=False)
    portal_users = models.ManyToManyField('ClientPortalUser')

    # Metadata
    client_since = models.DateField()  # Date of first engagement
    total_lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active_projects_count = models.IntegerField(default=0)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ClientPortalUser(models.Model):
    """Client-side users with portal access"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(choices=[
        ('admin', 'Client Admin'),
        ('member', 'Client Member'),
        ('viewer', 'View Only')
    ])
    can_upload_documents = models.BooleanField(default=True)
    can_view_billing = models.BooleanField(default=True)
    can_message_team = models.BooleanField(default=True)

class ClientNote(models.Model):
    """Internal notes about client (not visible to client)"""
    client = models.ForeignKey(Client)
    author = models.ForeignKey(User)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ClientEngagement(models.Model):
    """Tracks all engagements/contracts with client"""
    client = models.ForeignKey(Client)
    contract = models.ForeignKey('crm.Contract')
    status = models.CharField(choices=[
        ('current', 'Current Engagement'),
        ('completed', 'Completed'),
        ('renewed', 'Renewed')
    ])
    version = models.IntegerField(default=1)
    parent_engagement = models.ForeignKey('self', null=True)  # For renewals
```

### **2. Update Related Models**

#### **Projects → Link to Clients (not CRM):**
```python
# modules/projects/models.py
class Project(models.Model):
    client = models.ForeignKey('clients.Client')  # CHANGED from crm.Client
    contract = models.ForeignKey('crm.Contract')  # Contract still in CRM
    # ... rest unchanged
```

#### **Documents → Link to Clients:**
```python
# modules/documents/models.py
class Folder(models.Model):
    client = models.ForeignKey('clients.Client')  # CHANGED
    is_client_readable = models.BooleanField(default=False)
    is_client_writable = models.BooleanField(default=False)
```

#### **Invoices → Link to Clients:**
```python
# modules/finance/models.py
class Invoice(models.Model):
    client = models.ForeignKey('clients.Client')  # CHANGED
    project = models.ForeignKey('projects.Project')
```

### **3. Conversion Workflow**

When Proposal is accepted:
```python
# modules/crm/signals.py
@receiver(post_save, sender=Proposal)
def convert_prospect_to_client(sender, instance, **kwargs):
    if instance.status == 'accepted' and not instance.converted_to_client:
        # Create Client from Prospect
        client = Client.objects.create(
            source_prospect=instance.prospect,
            source_proposal=instance,
            company_name=instance.prospect.company_name,
            primary_contact_name=instance.prospect.primary_contact_name,
            primary_contact_email=instance.prospect.primary_contact_email,
            account_manager=instance.created_by,
            client_since=timezone.now().date(),
            status='active'
        )

        # Create Contract
        contract = Contract.objects.create(
            client=client,  # Link to new Client
            proposal=instance,
            # ... populate from proposal
        )

        # Create initial Project if configured
        if instance.auto_create_project:
            project = Project.objects.create(
                client=client,
                contract=contract,
                # ... populate from proposal/contract
            )

        # Enable portal access if configured
        if instance.enable_portal_on_acceptance:
            client.portal_enabled = True
            client.save()
            # Send portal invitation email

        # Mark prospect as won
        instance.prospect.pipeline_stage = 'won'
        instance.prospect.save()

        instance.converted_to_client = True
        instance.save()
```

---

## Frontend Restructuring

### **1. Navigation Reorganization**

#### **Current:**
```tsx
// All flat, no hierarchy
Dashboard → Clients → Proposals → Contracts → Projects → ...
```

#### **Proposed:**
```tsx
// Two-tier navigation with Clients as hub

// Top Level (Always visible)
Dashboard
Communications (Email, Chat, Board)
Scheduling
CRM (Pre-sale pipeline)
Clients ← BECOMES A HUB
Documents (Firm-wide DMS)
Knowledge Center

// When viewing a Client (Sub-navigation)
Client: Acme Corp ←
├── Overview (Analytics)
├── Projects
├── Documents (Client-specific)
├── Invoices
├── Contracts/Engagements
├── Communications (Client messages)
└── Portal Settings
```

### **2. Clients Module as Navigation Hub**

#### **New Clients Page Structure:**

```tsx
// /clients → List view
interface ClientsPage {
  // Searchable table
  columns: ['Company', 'Status', 'Account Manager', 'Active Projects', 'Lifetime Value', 'Actions']

  // Quick actions per client
  actions: [
    'View Overview',
    'Go to Projects',
    'View Documents',
    'View Invoices',
    'Message Client',
    'Portal Settings'
  ]
}

// /clients/:id → Client Hub (replaces detail view)
interface ClientHub {
  layout: 'sidebar-navigation' | 'tab-navigation'

  sections: {
    overview: ClientOverview,      // Analytics dashboard
    projects: ClientProjects,       // All projects for this client
    documents: ClientDocuments,     // Document tree
    invoices: ClientInvoices,       // AR tracking
    engagements: ClientEngagements, // Contracts/proposals
    communications: ClientComms,    // Message history
    settings: ClientSettings        // Portal access, team assignment
  }
}
```

---

## Client Portal Rebuild

### **Current Implementation:**
- Single page with 4 tabs (Documents, Invoices, Messages, Analytics)
- Only documents are functional
- Disconnected from firm data

### **Proposed: 6-Section Portal with Firm Integration**

```tsx
// Client Portal Architecture

interface ClientPortalProps {
  authenticatedClientUser: ClientPortalUser
  client: Client
}

// 1. DASHBOARD
interface DashboardSection {
  widgets: [
    'Active Projects Summary',
    'Pending Tasks Count',
    'Unread Messages',
    'Outstanding Invoices',
    'Recent Documents',
    'Upcoming Milestones'
  ]
  charts: [
    'Project Progress (% complete)',
    'Budget Utilization',
    'Time Tracking Summary'
  ]
}

// 2. WORK (Tied to Firm Projects)
interface WorkSection {
  projects: ClientProject[] // Read from projects.Project filtered by client

  perProject: {
    title: string
    status: string
    progress: number
    checklist: TaskItem[]     // From projects.Task
    attachments: Document[]    // From documents.Document
    comments: Comment[]        // NEW: ClientComment model
    assignedTeam: User[]
  }

  // Client can:
  actions: [
    'View checklist',
    'Download attachments',
    'Add comments (not edit tasks)',
    'Upload requested documents'
  ]
}

// 3. CHAT (Instant Messaging)
interface ChatSection {
  architecture: 'Daily Reset with Logging'

  threadStructure: {
    participants: [ClientPortalUser, ...AssignedTeamMembers]
    dailyThread: {
      date: Date
      messages: Message[]
      resetTime: '00:00 UTC'  // New thread daily
      archivedThread: boolean  // Previous day's chat
    }
  }

  features: [
    'Real-time messaging (WebSocket)',
    'File attachments',
    'Read receipts',
    'Daily thread archive (searchable history)',
    'NOT a ticketing system (informal, sync chat)'
  ]

  backend: 'WebSocket + Redis for real-time'
}

// 4. DOCUMENTS
interface DocumentsSection {
  folders: {
    clientReadFolder: {
      path: `/clients/${client.id}/shared-docs`
      permissions: 'Read + Download only'
      populatedFrom: 'Firm documents with is_client_readable=true'
    }

    clientUploadFolder: {
      path: `/clients/${client.id}/uploads`
      permissions: 'CRUD (Create, Read, Update, Delete)'
      workflow: 'Client uploads → Firm reviews → Move to project/shared'
    }
  }

  integration: 'Directly tied to modules.documents.Document model'
}

// 5. BILLING
interface BillingSection {
  invoices: {
    list: Invoice[]  // From modules.finance.Invoice
    actions: ['View PDF', 'Download', 'View History', 'Pay Now']
  }

  payment: {
    methods: ['Stripe', 'ACH (Plaid Auth)']
    features: [
      'One-time payment',
      'Payment plans',
      'Auto-pay setup',
      'Payment history',
      'Receipts'
    ]
  }

  integration: {
    invoiceData: 'modules.finance.Invoice',
    stripeIntegration: 'Existing webhooks (already built)',
    achIntegration: 'NEW: Plaid Link'
  }
}

// 6. ENGAGEMENT
interface EngagementSection {
  current: {
    activeProposals: Proposal[]      // status='sent' for renewals
    activeContracts: Contract[]      // Current engagements
    upcomingRenewals: Contract[]     // end_date within 90 days
  }

  archived: {
    completedEngagements: ClientEngagement[]
    versionHistory: Contract[]  // All versions with parent links
  }

  actions: {
    viewProposal: 'Read-only unless requires signature',
    signContract: 'E-signature integration (DocuSign/HelloSign)',
    requestRenewal: 'Triggers workflow in firm CRM',
    viewHistory: 'All past engagements with version control'
  }

  integration: {
    proposals: 'modules.crm.Proposal',
    contracts: 'modules.crm.Contract',
    engagements: 'modules.clients.ClientEngagement'
  }
}
```

---

## Firm Portal Reorganization

### **Proposed Navigation Structure:**

```tsx
interface FirmPortalNavigation {
  sections: [
    {
      title: 'Dashboard',
      route: '/',
      icon: '📊'
    },
    {
      title: 'Communications',
      route: '/communications',
      icon: '💬',
      subsections: [
        'Email Triage',     // NEW
        'Team Chat',        // Existing but enhanced
        'Message Board'     // NEW
      ]
    },
    {
      title: 'Scheduling',  // NEW
      route: '/scheduling',
      icon: '📅',
      integrations: ['Outlook', 'Gmail']
    },
    {
      title: 'CRM',
      route: '/crm',
      icon: '🎯',
      subsections: [
        'Leads',           // NEW
        'Prospects',       // NEW (renamed from Clients)
        'Proposals',       // MOVED HERE (pre-sale only)
        'Campaigns'        // NEW
      ]
    },
    {
      title: 'Clients',     // REPOSITIONED
      route: '/clients',
      icon: '👥',
      description: 'Post-sale client hub'
    },
    {
      title: 'Work',
      route: '/work',
      icon: '📋',
      subsections: [
        'Projects',
        'Tasks',
        'Time Tracking'
      ]
    },
    {
      title: 'Documents',
      route: '/documents',
      icon: '📁'
    },
    {
      title: 'AR',
      route: '/ar',
      icon: '💰',
      subsections: [
        'Invoices',
        'Payments Received',
        'Tracking'
      ]
    },
    {
      title: 'AP',
      route: '/ap',
      icon: '💳',
      subsections: [
        'Bills',
        'Vendor Management',
        'Payments'
      ]
    },
    {
      title: 'Assets',
      route: '/assets',
      icon: '💻'
    },
    {
      title: 'Knowledge Center',
      route: '/knowledge',
      icon: '📚'
    }
  ]
}
```

---

## New Modules Required

### **1. Email Triage (NEW)**

```python
# modules/communications/models.py

class EmailAccount(models.Model):
    """Firm email accounts"""
    email = models.EmailField(unique=True)
    provider = models.CharField(choices=[('outlook', 'Outlook'), ('gmail', 'Gmail')])
    oauth_token = models.TextField()  # Encrypted
    is_team_inbox = models.BooleanField(default=False)

class Email(models.Model):
    """Ingested emails"""
    account = models.ForeignKey(EmailAccount)
    message_id = models.CharField(unique=True)
    from_address = models.EmailField()
    to_addresses = models.JSONField()
    subject = models.CharField(max_length=500)
    body_text = models.TextField()
    body_html = models.TextField()
    received_date = models.DateTimeField()

    # Triage fields
    status = models.CharField(choices=[
        ('unassigned', 'Unassigned'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('archived', 'Archived')
    ])
    assigned_to = models.ForeignKey(User, null=True)
    priority = models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    tags = models.ManyToManyField('EmailTag')
    linked_client = models.ForeignKey('clients.Client', null=True)

class EmailTag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7)  # Hex color
```

**Frontend Features:**
- Unified inbox (all firm accounts)
- Assignment routing
- Priority tagging
- Quick responses with templates
- Link to client records

### **2. Scheduling (NEW)**

```python
# modules/scheduling/models.py

class Calendar(models.Model):
    """Calendar accounts"""
    user = models.ForeignKey(User)
    provider = models.CharField(choices=[('outlook', 'Outlook'), ('google', 'Google Calendar')])
    calendar_id = models.CharField()
    oauth_token = models.TextField()
    is_primary = models.BooleanField(default=False)
    sync_enabled = models.BooleanField(default=True)

class Event(models.Model):
    """Calendar events"""
    calendar = models.ForeignKey(Calendar)
    external_id = models.CharField()  # Provider's event ID
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    all_day = models.BooleanField(default=False)

    # Attendees
    organizer = models.ForeignKey(User, related_name='organized_events')
    attendees = models.ManyToManyField(User, related_name='events')

    # Links
    linked_client = models.ForeignKey('clients.Client', null=True)
    linked_project = models.ForeignKey('projects.Project', null=True)

    # Recurrence
    recurrence_rule = models.CharField(max_length=500, blank=True)  # RRULE format
```

**Frontend Features:**
- Multi-calendar view
- Team scheduling
- Client meeting links
- Outlook/Google two-way sync
- Meeting room booking

### **3. Message Board (NEW)**

```python
# modules/communications/models.py

class MessageBoard(models.Model):
    """Firm-wide announcements"""
    author = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(choices=[
        ('announcement', 'Announcement'),
        ('policy', 'Policy Update'),
        ('event', 'Event'),
        ('recognition', 'Team Recognition'),
        ('other', 'Other')
    ])
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class MessageBoardComment(models.Model):
    post = models.ForeignKey(MessageBoard)
    author = models.ForeignKey(User)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Data Flow & Integration

### **Workflow: Prospect → Client**

```
1. LEAD CAPTURE (CRM)
   └─ Lead created (website form, referral, campaign)

2. QUALIFICATION (CRM)
   └─ Lead → Prospect (sales pipeline)

3. PROPOSAL (CRM)
   └─ Prospect → Proposal sent

4. ACCEPTANCE (CRM → Clients transition)
   └─ Proposal accepted
       ├─ Create Client record
       ├─ Create Contract
       ├─ Create initial Project (if configured)
       ├─ Setup Document folders
       ├─ Enable Portal access (if configured)
       └─ Send welcome email

5. ONGOING (Clients)
   └─ Client → Projects → Time Tracking → Invoicing

6. RENEWAL (Clients → CRM cycle)
   └─ Client → Request renewal
       ├─ Create new Proposal (in CRM)
       ├─ If accepted: Create new Contract version
       └─ Link to ClientEngagement history
```

### **Client Portal Data Flow**

```
Client Portal Request → Firm Backend

Dashboard:
  └─ Aggregate data from Projects, Invoices, Documents, Tasks

Work:
  └─ Filter projects.Project by client_id
      └─ Show tasks.Task for those projects
          └─ Client can comment (new ClientComment model)

Chat:
  └─ WebSocket connection
      └─ Messages stored in ClientMessage table
          └─ Daily reset creates new thread
              └─ Old thread archived in ClientChatArchive

Documents:
  ├─ Read Folder: documents.Document WHERE client_id=X AND is_client_readable=true
  └─ Upload Folder: documents.Document WHERE client_id=X AND client_writable=true

Billing:
  └─ finance.Invoice WHERE client_id=X
      └─ Stripe payment links generated on-demand

Engagement:
  ├─ Current: crm.Contract WHERE client_id=X AND status='active'
  └─ History: clients.ClientEngagement with version tree
```

---

## Implementation Phases

### **Phase 1: Backend Restructure (Week 1-2)**

**Day 1-3: Database Migration**
- [ ] Create new `modules/clients/` app
- [ ] Create Lead, Prospect, Campaign models in CRM
- [ ] Create Client, ClientPortalUser, ClientEngagement models in Clients
- [ ] Write data migration script (existing Client → new Client + Prospect)
- [ ] Update foreign keys in Projects, Documents, Finance

**Day 4-5: API Endpoints**
- [ ] Clients API (`/api/clients/`)
- [ ] CRM API refactor (`/api/crm/leads/`, `/api/crm/prospects/`)
- [ ] Conversion workflow endpoint (`/api/crm/proposals/{id}/accept/`)

**Day 6-7: Signals & Workflows**
- [ ] Proposal acceptance → Client creation signal
- [ ] Auto-setup workflows (portal, documents, projects)

### **Phase 2: New Modules (Week 2-3)**

**Day 8-10: Email Triage**
- [ ] Email models (EmailAccount, Email, EmailTag)
- [ ] OAuth integration (Outlook, Gmail)
- [ ] IMAP sync worker
- [ ] Email assignment API
- [ ] Frontend: Email inbox component

**Day 11-12: Scheduling**
- [ ] Calendar models
- [ ] OAuth integration (Outlook, Google Calendar)
- [ ] Two-way sync
- [ ] Frontend: Calendar view

**Day 13-14: Message Board**
- [ ] MessageBoard models
- [ ] API endpoints
- [ ] Frontend: Board component

### **Phase 3: Client Portal Rebuild (Week 3-4)**

**Day 15-17: Portal Backend**
- [ ] ClientPortalUser authentication
- [ ] ClientMessage model (chat)
- [ ] ClientComment model (work section)
- [ ] Payment integration (Stripe + Plaid ACH)

**Day 18-21: Portal Frontend**
- [ ] Dashboard section
- [ ] Work section (project checklists)
- [ ] Chat section (WebSocket)
- [ ] Documents section (read/upload)
- [ ] Billing section (invoices + payment)
- [ ] Engagement section (contracts)

### **Phase 4: Firm Portal Reorganization (Week 4-5)**

**Day 22-24: Navigation Restructure**
- [ ] New CRM pages (Leads, Prospects, Campaigns)
- [ ] New Clients hub (list + detail pages)
- [ ] Update routing
- [ ] Update navigation component

**Day 25-28: Integration & Testing**
- [ ] End-to-end workflow testing
- [ ] Data migration validation
- [ ] Performance testing
- [ ] User acceptance testing

---

## Definition of Done

### **Backend:**
- [ ] CRM contains ONLY pre-sale: Leads, Prospects, Proposals, Campaigns
- [ ] Clients module exists as separate app with post-sale operations
- [ ] All foreign keys updated (Projects, Documents, Finance → Clients)
- [ ] Conversion workflow (Proposal → Client) works end-to-end
- [ ] Email Triage backend with OAuth integration
- [ ] Scheduling backend with calendar sync
- [ ] Message Board backend
- [ ] All migrations run cleanly on fresh database

### **Frontend - Client Portal:**
- [ ] 6 sections implemented and functional:
  - [ ] Dashboard (analytics widgets)
  - [ ] Work (project checklists with comments)
  - [ ] Chat (WebSocket IM with daily reset)
  - [ ] Documents (read folder + upload folder)
  - [ ] Billing (invoices + Stripe/ACH payment)
  - [ ] Engagement (contracts with version control)
- [ ] All sections tied to firm data (no mock data)
- [ ] Responsive design
- [ ] Client authentication working

### **Frontend - Firm Portal:**
- [ ] Navigation reorganized per spec
- [ ] CRM module (pre-sale only): Leads, Prospects, Proposals, Campaigns
- [ ] Clients module as hub with sub-navigation
- [ ] Communications: Email Triage, Team Chat, Message Board
- [ ] Scheduling: Calendar view with Outlook/Gmail sync
- [ ] All existing modules (Projects, Documents, AR, AP, Assets, Knowledge) functional

### **Integration:**
- [ ] Client detail page shows all related: Projects, Documents, Invoices, Contracts
- [ ] Client Portal data syncs in real-time with firm data
- [ ] Email assignments route to correct team members
- [ ] Calendar events link to clients/projects
- [ ] Message board accessible to all team members

### **Documentation:**
- [ ] Updated README with new architecture
- [ ] API documentation for new endpoints
- [ ] Client Portal user guide
- [ ] Firm Portal user guide
- [ ] Data migration guide

---

## Questions for Review

Before proceeding, please confirm:

1. **CRM Scope:** Is the proposed Lead → Prospect → Proposal workflow correct for your pre-sale process?
2. **Client Portal Chat:** Daily reset with archiving - is this the right approach vs. persistent threads?
3. **Email Integration:** Outlook + Gmail only, or other providers (Exchange, IMAP)?
4. **Payment Methods:** Stripe + ACH (Plaid) sufficient, or need other payment gateways?
5. **Scheduling:** Two-way sync or read-only from Outlook/Google?
6. **Priority:** Which phase should be implemented first if phased rollout?

---

## Approval Required

Please review this plan and indicate:
- ✅ **APPROVE** - Proceed with implementation as specified
- 🔄 **REVISE** - Changes needed (specify which sections)
- ⏸️ **PHASE** - Implement in stages (specify priority order)

Once approved, I will begin implementation starting with Phase 1 (Backend Restructure).
