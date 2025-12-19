# ConsultantPro - Unified Service Platform (USP)

**Phase 1: The Core Skeleton**

Management consulting SaaS platform built with the "Fork-and-Ship" strategy.

---

## Overview

ConsultantPro is the first product in a family of vertical SaaS solutions for professional services. It implements a robust "Quote-to-Cash" workflow for management consulting firms.

### The USP Strategy: "Sequential Product Line"

We are building multiple products for the professional services industry using a **Fork-and-Ship** model:

1. **ConsultantPro** (Phase 1 - Current) - Management Consultants
2. **ArchitectPro** (Phase 2) - Architecture & Engineering Firms
3. **LegalPro** (Phase 3) - Boutique Law Firms

#### Why Fork Instead of Configure?

We reject the "one-size-fits-all" approach. Each vertical gets:
- **Optimized database schema** (no generic EAV or JSON bags)
- **Tailored business logic** (no feature flags)
- **Physical infrastructure isolation** (separate deployments)

This solves the "Complexity vs. Variance" problem while maintaining a shared foundation.

---

## Architecture

### Pattern: Modular Monolith

- **NOT Microservices** - We reject distributed complexity
- **Code organized by domain** - Not by technical layers
- **Strict relational schema** - ACID compliance enforced at DB level
- **Physical isolation** - Each product runs on isolated infrastructure

### Tech Stack (The "Boring Stack")

**Backend:**
- Python 3.11+
- Django 4.2+
- Django REST Framework
- PostgreSQL 15+

**Frontend:**
- React 18+
- TypeScript
- Vite
- TanStack Query (React Query)

**Infrastructure:**
- Docker & Docker Compose
- Standard VPS (AWS Lightsail / DigitalOcean)
- NO Kubernetes

---

## Project Structure

```
/src
  /config                   # Django Settings & WSGI
    settings.py
    urls.py
    wsgi.py
    asgi.py

  /modules                  # Business Domain Modules
    /crm                    # Customer Relationship Management
      models.py             # Client, Proposal, Contract
      admin.py
    /projects               # Project Execution & Time Tracking
      models.py             # Project, Task, TimeEntry
      admin.py
    /finance                # Accounting (AR/AP, P&L)
      models.py             # Invoice, Bill, LedgerEntry
      admin.py
    /documents              # Document Management & Client Portal
      models.py             # Folder, Document, Version
      admin.py
    /assets                 # Asset & Equipment Tracking
      models.py             # Asset, MaintenanceLog
      admin.py

  /api                      # REST API Endpoints
    /crm                    # CRM API
      serializers.py
      views.py
      urls.py
    /projects               # Projects API
    /finance                # Finance API
    /documents              # Documents API
    /assets                 # Assets API

  /frontend                 # React SPA
    /src
      /components
      /pages
      /api
      /hooks
      /types
    package.json
    vite.config.ts

  manage.py                 # Django Management
```

---

## Business Modules

### 1. CRM (Customer Relationship Management)

**Purpose:** Quote-to-Cash workflow

**Models:**
- `Client` - Company entities with contact info
- `Proposal` - Quotes sent to clients
- `Contract` - Signed agreements

**Flow:** Lead → Proposal → Contract

### 2. Projects (Execution & Time Tracking)

**Purpose:** Deliver work and track billable time

**Models:**
- `Project` - Consulting engagements
- `Task` - Kanban-style work items
- `TimeEntry` - Time tracking for billing

**Flow:** Contract → Project → Tasks → Time Entries → Invoice

### 3. Finance (Accounting)

**Purpose:** Invoicing and P&L reporting

**Models:**
- `Invoice` - Accounts Receivable (AR)
- `Bill` - Accounts Payable (AP)
- `LedgerEntry` - Double-entry bookkeeping

**Flow:** Time Entries → Invoice → Payment → Ledger

### 4. Documents (Client Portal)

**Purpose:** Secure document storage and sharing

**Models:**
- `Folder` - Hierarchical organization
- `Document` - S3-backed files
- `Version` - Version control

**Integration:** S3 for storage

### 5. Assets (Equipment Tracking)

**Purpose:** Track company-owned resources

**Models:**
- `Asset` - Equipment, software licenses
- `MaintenanceLog` - Repair and service history

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)

### Quick Start

1. **Clone the repository**

```bash
git clone <repository-url>
cd OS
```

2. **Start the services**

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Django backend (port 8000)

3. **Access the application**

- **Backend API:** http://localhost:8000/api/
- **Django Admin:** http://localhost:8000/admin/

4. **Create a superuser**

```bash
docker-compose exec web python manage.py createsuperuser
```

### Frontend Development

```bash
cd src/frontend
npm install
npm run dev
```

Frontend will run on http://localhost:3000

---

## Development Workflow

### Database Migrations

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

### Django Shell

```bash
docker-compose exec web python manage.py shell
```

### Testing

```bash
docker-compose exec web pytest
```

---

## API Endpoints

### CRM Module
- `GET /api/crm/clients/` - List clients
- `POST /api/crm/clients/` - Create client
- `GET /api/crm/proposals/` - List proposals
- `GET /api/crm/contracts/` - List contracts

### Projects Module
- `GET /api/projects/projects/` - List projects
- `GET /api/projects/tasks/` - List tasks
- `GET /api/projects/time-entries/` - List time entries

### Finance Module
- `GET /api/finance/invoices/` - List invoices
- `GET /api/finance/bills/` - List bills
- `GET /api/finance/ledger-entries/` - List ledger entries

### Documents Module
- `GET /api/documents/folders/` - List folders
- `GET /api/documents/documents/` - List documents

### Assets Module
- `GET /api/assets/assets/` - List assets
- `GET /api/assets/maintenance-logs/` - List maintenance logs

---

## Design Principles

### 1. Strict Relational Schema

- No EAV (Entity-Attribute-Value)
- No generic JSON "bags" for core business data
- All relationships enforced with foreign keys
- Database-level constraints

### 2. MVP Constraint: "Quote-to-Cash"

If a feature doesn't help:
- Get a quote out
- Get money in

**Cut it.**

### 3. Schema Drift is Acceptable

When we fork to create ArchitectPro or LegalPro:
- The Legal fork will have `court_date` columns
- The Consulting fork will NOT have `court_date`
- **This is by design**

### 4. Shared Kernel (Future)

Universal logic will be extracted to `@usp/core-lib`:
- Auth utilities
- S3 wrappers
- Stripe integration
- Email services

Business logic stays in the app.

---

## Roadmap

### Phase 1: ConsultantPro (Current)

**Status:** Core Skeleton Complete

**Next Steps:**
- [ ] Implement authentication
- [ ] Build CRM UI (React)
- [ ] Implement proposal generation
- [ ] Build time tracking UI
- [ ] Implement invoice generation
- [ ] S3 integration for documents
- [ ] Stripe integration for payments

### Phase 2: ArchitectPro (Q2 2024)

**Target:** Architecture & Engineering Firms

**New Features:**
- WIP (Work-in-Progress) billing
- Retainer management
- RFI (Request for Information) workflows
- Blueprint version control

**Approach:** Fork ConsultantPro repository

### Phase 3: LegalPro (Q3 2024)

**Target:** Boutique Law Firms

**New Features:**
- Trust accounting (IOLTA)
- Conflict checking
- Matter management
- Court calendar integration

**Approach:** Fork ConsultantPro repository

---

## Environment Variables

Create a `.env` file in the root directory:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=consultantpro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# AWS S3 (for Documents module)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Stripe (for Finance module)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## Contributing

This is a private commercial project. Contributors must:
1. Follow the Modular Monolith pattern
2. Maintain strict relational schema
3. Respect the "Quote-to-Cash" MVP constraint
4. Write tests for all new features

---

## License

Proprietary - All Rights Reserved

---

## Contact

For questions or support, contact the USP architecture team.
