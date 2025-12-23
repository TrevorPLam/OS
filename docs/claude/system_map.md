# ConsultantPro System Map
**Date:** December 23, 2025
**Version:** 1.0 (Phase 1 Skeleton)

---

## System Overview

**ConsultantPro** is a Quote-to-Cash management platform for management consulting firms, built as a modular Django monolith with React frontend.

**Purpose:** Manage entire consulting lifecycle from lead capture → proposal → contract → project delivery → invoicing → client retention

**Architecture Pattern:** Modular Monolith (not microservices)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USERS                                │
│  ┌────────────────┐        ┌──────────────────────┐        │
│  │  Firm Team     │        │  Client Portal Users │        │
│  │  (Internal)    │        │  (External Clients)  │        │
│  └────────┬───────┘        └──────────┬───────────┘        │
└───────────┼────────────────────────────┼───────────────────┘
            │                            │
            │                            │
┌───────────▼────────────────────────────▼───────────────────┐
│                    FRONTEND LAYER                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React 18 + TypeScript 5.3 + Vite 5.0                │  │
│  │  - TanStack Query (data fetching)                     │  │
│  │  - React Router (navigation)                          │  │
│  │  - Context API (auth state)                           │  │
│  └──────────────────┬───────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────┘
                      │ HTTP/REST (JSON)
                      │ JWT Bearer Token Auth
┌─────────────────────▼──────────────────────────────────────┐
│                    API LAYER                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Django REST Framework 3.14                           │  │
│  │  - JWT Authentication (SimpleJWT)                     │  │
│  │  - Rate Limiting (100/min, 1000/hr)                   │  │
│  │  - CORS Middleware                                    │  │
│  │  - OpenAPI/Swagger Docs (drf-spectacular)            │  │
│  └──────────────────┬───────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │    CRM     │ │  Clients   │ │  Projects  │            │
│  │  (Pre-sale)│ │ (Post-sale)│ │  (Delivery)│            │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘            │
│        │              │              │                     │
│  ┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐            │
│  │  Finance   │ │ Documents  │ │   Assets   │            │
│  │  (Billing) │ │  (Storage) │ │ (Tracking) │            │
│  └────────────┘ └────────────┘ └────────────┘            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Core Services: Email Notifications, Signals         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬──────────────────────────────────────┘
                      │ Django ORM
┌─────────────────────▼──────────────────────────────────────┐
│                   DATA LAYER                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PostgreSQL 15 (ACID-compliant)                       │  │
│  │  - 23 tables across 7 modules                         │  │
│  │  - 46 strategic indexes                               │  │
│  │  - Foreign key relationships (41 FKs)                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 EXTERNAL SERVICES                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   AWS S3     │  │    Stripe    │  │  Email (SMTP)    │  │
│  │  (Documents) │  │  (Payments)  │  │ (Notifications)  │  │
│  │  ⚠️ Empty    │  │  ⚠️ Empty    │  │ ❌ Not Configured│  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Map

### Pre-Sale → Post-Sale Data Flow

```
┌─────────────────────┐
│  1. CRM (Pre-Sale)  │
├─────────────────────┤
│ • Lead              │ ← Marketing captures leads
│ • Prospect          │ ← Qualified leads → prospects
│ • Campaign          │ ← Campaign tracking
│ • Proposal          │ ← Send quote to prospect
│ • Contract          │ ← Signed agreement
└──────────┬──────────┘
           │
           │ Proposal Accepted
           │ (Conversion Point)
           ▼
┌─────────────────────┐
│ 2. Clients (Active) │
├─────────────────────┤
│ • Client            │ ← Created from accepted proposal
│ • ClientPortalUser  │ ← Portal access provisioned
│ • ClientNote        │ ← Internal team notes
│ • ClientEngagement  │ ← Engagement versioning
│ • ClientComment     │ ← Two-way task communication
│ • ClientChatThread  │ ← Daily chat threads
│ • ClientMessage     │ ← Chat messages
└──────────┬──────────┘
           │
           │ Client has active contracts
           │
           ▼
┌─────────────────────────────────────────────────────┐
│  Parallel Delivery Tracks                           │
├──────────────────┬──────────────────┬───────────────┤
│                  │                  │               │
│  3. Projects     │  4. Documents    │  5. Finance   │
│  ┌───────────┐   │  ┌───────────┐   │  ┌────────┐  │
│  │ Project   │   │  │ Folder    │   │  │Invoice │  │
│  │ Task      │   │  │ Document  │   │  │Bill    │  │
│  │ TimeEntry │   │  │ Version   │   │  │Ledger  │  │
│  └───────────┘   │  └───────────┘   │  └────────┘  │
│                  │                  │               │
│  Execution       │  Collaboration   │  Billing      │
└──────────────────┴──────────────────┴───────────────┘

┌─────────────────────┐
│  6. Assets (Firm)   │
├─────────────────────┤
│ • Asset             │ ← Company-owned equipment
│ • MaintenanceLog    │ ← Asset maintenance tracking
└─────────────────────┘
```

---

## Data Model Relationships

### Core Entity Relationships
```
Lead ──┐
       ├──> Prospect ──> Proposal ──┐
       │                            │
Campaign                            ├──> Contract ──┐
                                    │               │
                                    ▼               ▼
                                  Client <────── ClientEngagement
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
            Project             Document            Invoice
                │                   │                   │
                ├── Task            ├── Folder          ├── TimeEntry
                └── TimeEntry       └── Version         └── Bill


Client Portal Data Access:
User ──> ClientPortalUser ──> Client ──> [All client data auto-filtered]
```

### Foreign Key Cascade Rules
| Relationship | On Delete | Rationale |
|--------------|-----------|-----------|
| Client → Prospect | SET_NULL | Preserve prospect history even if client deleted |
| Project → Client | CASCADE | Project can't exist without client |
| Task → Project | CASCADE | Task can't exist without project |
| Invoice → Client | CASCADE | Invoice belongs to client |
| Document → Folder | CASCADE | Document belongs to folder |
| TimeEntry → Invoice | SET_NULL | Preserve time entry even if invoice deleted |
| ClientMessage → Thread | CASCADE | Message can't exist without thread |

---

## API Endpoint Map

### Base URL: `/api/`

```
/api/
├── auth/
│   ├── login/                    POST   - JWT token creation
│   ├── logout/                   POST   - Token blacklist
│   └── refresh/                  POST   - Refresh access token
│
├── crm/
│   ├── leads/                    LIST   - All leads
│   │   ├── {id}/                 DETAIL - Single lead
│   │   └── convert/              ACTION - Convert to prospect
│   ├── prospects/                LIST   - All prospects
│   │   ├── {id}/                 DETAIL - Single prospect
│   │   └── convert/              ACTION - Convert to client
│   ├── campaigns/                LIST   - All campaigns
│   ├── proposals/                LIST   - All proposals
│   │   └── {id}/
│   │       └── accept/           ACTION - Accept proposal → create client
│   └── contracts/                LIST   - All contracts
│       └── {id}/download/        ACTION - Download PDF
│
├── clients/
│   ├── clients/                  LIST   - All clients (firm view)
│   │   ├── {id}/                 DETAIL - Single client
│   │   └── portal-users/         ACTION - Manage portal access
│   ├── portal-users/             LIST   - All portal users
│   ├── notes/                    LIST   - Internal notes
│   ├── engagements/              LIST   - Engagement history
│   │
│   │  ═══ CLIENT PORTAL ENDPOINTS (auto-filtered by client) ═══
│   ├── projects/                 LIST   - Client's projects
│   │   └── {id}/tasks/           ACTION - Tasks for project
│   ├── comments/                 LIST   - Client's task comments
│   │   ├── POST                  CREATE - Add comment to task
│   │   └── {id}/mark-read/       ACTION - Mark comment as read
│   ├── invoices/                 LIST   - Client's invoices
│   │   └── {id}/payment-link/    ACTION - Generate Stripe payment link
│   ├── chat-threads/             LIST   - Client's chat threads
│   │   └── active/               ACTION - Get/create today's thread
│   ├── messages/                 LIST   - Messages in thread
│   │   ├── POST                  CREATE - Send message
│   │   └── unread/               ACTION - Get unread count
│   ├── proposals/                LIST   - Client's proposals
│   │   └── {id}/accept/          ACTION - Accept proposal (e-signature placeholder)
│   ├── contracts/                LIST   - Client's contracts
│   │   └── {id}/download/        ACTION - Download contract PDF
│   └── engagement-history/       LIST   - Engagement timeline
│
├── projects/
│   ├── projects/                 LIST   - All projects (firm view)
│   │   └── {id}/tasks/           ACTION - Tasks for project
│   ├── tasks/                    LIST   - All tasks
│   └── time-entries/             LIST   - All time entries
│       ├── POST                  CREATE - Log time
│       └── {id}/                 DETAIL - Single time entry
│
├── finance/
│   ├── invoices/                 LIST   - All invoices
│   │   ├── {id}/send/            ACTION - Send to client
│   │   └── {id}/record-payment/  ACTION - Record payment
│   ├── bills/                    LIST   - All bills
│   │   └── {id}/approve/         ACTION - Approve payment
│   └── ledger-entries/           LIST   - General ledger
│
├── documents/
│   ├── folders/                  LIST   - All folders
│   │   └── {id}/subfolders/      ACTION - Get subfolders
│   ├── documents/                LIST   - All documents
│   │   ├── POST                  CREATE - Upload document (to S3)
│   │   └── {id}/
│   │       ├── download/         ACTION - Get signed S3 URL
│   │       └── versions/         ACTION - Get version history
│   └── versions/                 LIST   - All versions
│
├── assets/
│   ├── assets/                   LIST   - All assets
│   │   └── {id}/maintenance/     ACTION - Maintenance logs
│   └── maintenance-logs/         LIST   - All maintenance
│
└── docs/                         GET    - OpenAPI/Swagger UI (drf-spectacular)
```

---

## Authentication & Authorization Flow

### JWT Authentication Flow
```
1. User Login
   POST /api/auth/login/
   { "username": "...", "password": "..." }
   ↓
   Response: { "access": "...", "refresh": "..." }
   Access token lifetime: 1 hour
   Refresh token lifetime: 7 days

2. Authenticated Requests
   GET /api/clients/projects/
   Headers: { "Authorization": "Bearer <access_token>" }
   ↓
   Django validates JWT signature
   ↓
   DRF extracts user from token
   ↓
   View auto-filters by ClientPortalUser.client

3. Token Refresh
   POST /api/auth/refresh/
   { "refresh": "..." }
   ↓
   Response: { "access": "..." }
   Old refresh token blacklisted (if ROTATE_REFRESH_TOKENS=True)
```

### Client Portal Auto-Filtering
```python
# Example: ClientProjectViewSet
class ClientProjectViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        portal_user = ClientPortalUser.objects.get(user=self.request.user)
        return Project.objects.filter(client=portal_user.client)
```

**Security:** All Client Portal endpoints filter by authenticated user's client. Client A cannot see Client B's data.

---

## Technology Stack Map

### Backend
```
Python 3.11
  └── Django 4.2.8
      ├── Django REST Framework 3.14.0
      │   ├── SimpleJWT 5.3.1 (auth)
      │   ├── drf-spectacular 0.27.0 (docs)
      │   └── django-filter 23.5 (filtering)
      ├── django-cors-headers 4.3.1
      ├── psycopg2-binary 2.9.9 (PostgreSQL driver)
      ├── boto3 1.34.11 (AWS SDK)
      └── stripe 7.9.0 (Payments)

  Testing:
    ├── pytest 7.4.3
    ├── pytest-django 4.7.0
    ├── pytest-cov 4.1.0
    └── factory-boy 3.3.0

  Production:
    └── gunicorn 21.2.0
```

### Frontend
```
Node.js 22.21.1
  └── React 18.2.0
      ├── React Router 6.20.0
      ├── TypeScript 5.3.3
      ├── Vite 5.0.7 (build tool)
      ├── TanStack Query 5.14.0 (data fetching)
      ├── Axios 1.6.2 (HTTP client)
      └── React Hook Form 7.49.0
```

### Infrastructure
```
Docker Compose
  ├── PostgreSQL 15-alpine
  │   ├── Port: 5432
  │   └── Volume: postgres_data
  └── Django Web
      ├── Port: 8000
      ├── Volumes: ./src, static_volume, media_volume
      └── Depends on: db (health check)

CI/CD:
  └── GitHub Actions
      ├── Lint (flake8, black, isort)
      ├── Test Backend (pytest)
      ├── Build Frontend (npm build)
      ├── Security Scan (safety, trufflehog)
      └── Docker Build
```

---

## Data Flow Examples

### Example 1: New Client Onboarding
```
1. Marketing captures Lead
   POST /api/crm/leads/
   { company_name: "Acme Corp", source: "website", ... }

2. Sales qualifies → Prospect
   POST /api/crm/prospects/
   { lead: 123, estimated_value: 50000, ... }

3. Sales creates Proposal
   POST /api/crm/proposals/
   { prospect: 456, total_value: 50000, ... }

4. Client accepts Proposal
   POST /api/crm/proposals/456/accept/
   → Signal: proposal_accepted
   → Creates Client
   → Creates ClientPortalUser
   → Sends welcome email

5. Sales creates Contract
   POST /api/crm/contracts/
   { client: 789, proposal: 456, ... }

6. PM creates Project
   POST /api/projects/projects/
   { client: 789, contract: 101, ... }
```

### Example 2: Client Portal - Task Comment
```
1. Client views project tasks
   GET /api/clients/projects/123/tasks/
   → Auto-filtered by portal_user.client

2. Client adds comment
   POST /api/clients/comments/
   { task: 456, comment: "Please update deliverable" }
   → auto-sets client from portal_user.client

3. Signal: client_comment_created
   → EmailNotification.send_task_comment_to_team()

4. Firm team marks as read
   POST /api/clients/comments/789/mark-read/
   → Sets is_read_by_firm = True, read_by = current_user
```

### Example 3: Time Entry → Invoice
```
1. Consultant logs time
   POST /api/projects/time-entries/
   { project: 123, task: 456, hours: 2.5, hourly_rate: 200 }
   → Auto-calculates billed_amount = 500.00

2. Finance creates invoice
   POST /api/finance/invoices/
   { client: 789, project: 123, line_items: [...] }
   → Links TimeEntry.invoice = invoice_id

3. Client views invoice in portal
   GET /api/clients/invoices/101/
   → Shows $500 for 2.5 hours

4. Client makes payment
   GET /api/clients/invoices/101/payment-link/
   → Returns Stripe payment link

5. Stripe webhook (future)
   POST /api/webhooks/stripe/
   → Updates Invoice.status = 'paid'
```

---

## Integration Map

### Current Integrations
| Service | Status | Purpose | Configuration |
|---------|--------|---------|---------------|
| **PostgreSQL 15** | ✅ Active | Primary database | docker-compose.yml |
| **AWS S3** | ⚠️ Configured | Document storage | boto3 installed, keys empty |
| **Stripe** | ⚠️ Configured | Payment processing | stripe installed, keys empty |
| **SMTP** | ❌ Not configured | Email notifications | No settings defined |

### Missing Integrations
- Calendar sync (Google Calendar, Outlook)
- CRM imports (Salesforce, HubSpot)
- Accounting exports (QuickBooks, Xero)
- E-signature (DocuSign, HelloSign)
- Real-time messaging (WebSockets, Pusher)
- Error tracking (Sentry)
- Monitoring (Datadog, New Relic)

---

## Deployment Map

### Current: Development (Docker Compose)
```
developer@localhost
  ↓
docker-compose up
  ↓
┌─────────────────┐      ┌─────────────────┐
│  PostgreSQL     │      │  Django Web     │
│  Port: 5432     │←─────│  Port: 8000     │
│  (Health check) │      │  (Auto-migrate) │
└─────────────────┘      └─────────────────┘

Frontend (separate process):
  cd src/frontend && npm run dev
  Port: 3000 (Vite dev server)
```

### Recommended: Production (AWS)
```
Internet
  ↓
Cloudflare CDN (static assets)
  ↓
Route 53 (DNS)
  ↓
Application Load Balancer (ALB)
  ├── Health checks: /api/health/
  └── SSL termination
      ↓
ECS Fargate (Django containers) ×N
  ├── Auto-scaling: CPU > 70%
  ├── Environment: Secrets Manager
  └── Logging: CloudWatch
      ↓
RDS PostgreSQL Multi-AZ
  ├── Automated backups (7 days)
  ├── Read replicas (optional)
  └── Encryption at rest

S3 Buckets:
  ├── documents-prod (versioning enabled)
  └── static-assets-prod (CloudFront CDN)

Monitoring:
  ├── CloudWatch (metrics, logs)
  ├── Sentry (error tracking)
  └── Datadog (APM)
```

---

## Performance Characteristics

### Current (Estimated)
| Metric | Value | Notes |
|--------|-------|-------|
| **API Response Time** | ~100-300ms | No caching, simple queries |
| **Database Queries per Request** | 3-8 | Potential N+1 issues |
| **Max Concurrent Users** | ~100 | Single Django container |
| **Database Size** | ~1GB/year | 100 clients, moderate usage |
| **S3 Storage** | ~10GB/year | Assuming 100MB/client |

### Bottlenecks
1. **Chat polling** - 5-second refresh = 720 requests/hour/client
2. **No caching** - Every request hits database
3. **Single container** - No horizontal scaling
4. **No CDN** - Static assets served from Django

---

## Security Architecture

### Authentication Layers
```
Layer 1: JWT Bearer Token
  ├── Access token (1 hour)
  └── Refresh token (7 days, rotated, blacklisted)

Layer 2: DRF Permissions
  ├── IsAuthenticated (default)
  └── Custom permissions (e.g., CanViewBilling)

Layer 3: Auto-Filtering
  └── Client Portal: filter by portal_user.client

Layer 4: Django ORM
  └── Parameterized queries (SQL injection prevention)
```

### Rate Limiting
```
Burst: 100 requests/minute
Sustained: 1000 requests/hour

Special rates:
  ├── anon: 20/hour
  ├── payment: 10/minute
  └── upload: 30/hour
```

### Security Headers (Production)
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: (to be defined)
```

---

## Monitoring & Observability

### Current State: ❌ **NOT CONFIGURED**

### Recommended Setup
```
Logging:
  ├── Application logs → CloudWatch
  ├── Django logs → Rotating file handlers
  │   ├── django.log (general, 10MB, 10 backups)
  │   ├── errors.log (errors only)
  │   └── security.log (auth events)
  └── Access logs → ALB

Metrics:
  ├── APM: Datadog / New Relic
  ├── Database: CloudWatch RDS metrics
  └── Infrastructure: CloudWatch EC2/ECS

Error Tracking:
  └── Sentry (Python + JavaScript)

Alerts:
  ├── Error rate > 1%
  ├── Response time > 1s (p99)
  ├── Database CPU > 80%
  └── Disk usage > 90%
```

---

## Disaster Recovery

### Current State: ❌ **NOT DEFINED**

### Recommended Strategy
```
Backups:
  ├── PostgreSQL: Automated daily snapshots (7-day retention)
  ├── S3: Versioning enabled, cross-region replication
  └── Code: GitHub (multiple copies)

Recovery Time Objective (RTO): 4 hours
Recovery Point Objective (RPO): 24 hours

Disaster Scenarios:
  1. Database corruption → Restore from latest snapshot
  2. AWS region outage → Failover to secondary region
  3. Accidental data deletion → Restore from backup
  4. Security breach → Rotate secrets, audit logs, notify clients
```

---

## Conclusion

ConsultantPro is a **well-architected modular monolith** with clear separation of concerns, comprehensive data model, and modern tech stack. The system covers the full Quote-to-Cash lifecycle with 7 business modules and 23 models.

**Production Readiness: 6/10**
- ✅ Solid architecture
- ✅ Comprehensive features
- ⚠️ Critical blockers (auth, TypeScript)
- ❌ Minimal tests
- ❌ No production deployment plan

**Next Steps:**
1. Fix critical blockers
2. Add test coverage
3. Set up production infrastructure
4. Configure monitoring
5. Deploy to staging

**Time to Production:** ~60 days with 1-2 engineers

---

**Legend:**
- ✅ Complete / Working
- ⚠️ Partial / Configured but needs work
- ❌ Missing / Not configured
