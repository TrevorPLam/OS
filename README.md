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
    /crm                    # Marketing & Sales (Pre-Sale)
      models.py             # Lead, Prospect, Campaign, Proposal, Contract
      admin.py
      signals.py            # Proposal acceptance → Client creation
    /clients                # Client Management (Post-Sale)
      models.py             # Client, ClientEngagement, ClientPortalUser
      admin.py
      signals.py
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
    /knowledge              # Knowledge Center
      models.py             # Article, Category

  /api                      # REST API Endpoints
    /crm                    # CRM API (Pre-Sale)
      serializers.py
      views.py
      urls.py
    /clients                # Clients API (Post-Sale)
    /projects               # Projects API
    /finance                # Finance API
    /documents              # Documents API
    /assets                 # Assets API

  /frontend                 # React SPA
    /src
      /components
      /pages
        /crm                # CRM pages (Leads, Prospects, Campaigns)
      /api
      /hooks
      /types
    package.json
    vite.config.ts

  manage.py                 # Django Management
```

---

## Business Modules

### 1. CRM (Marketing & Sales - Pre-Sale)

**Purpose:** Lead capture through proposal acceptance

**Models:**
- `Lead` - Marketing-captured prospects (new)
- `Prospect` - Qualified sales opportunities (new)
- `Campaign` - Marketing campaign tracking (new)
- `Proposal` - Quotes for prospects AND client renewals/upsells
- `Contract` - Signed engagement letters

**Flow:** Lead → Prospect → Proposal → **[Acceptance triggers Client creation]**

**Key Features:**
- Lead scoring and qualification
- Sales pipeline management
- Campaign performance tracking
- 3 Proposal types:
  - `prospective_client`: New business (linked to Prospect)
  - `update_client`: Expansion/Upsell (linked to Client)
  - `renewal_client`: Contract renewal (linked to Client)
- Automated client conversion on proposal acceptance

### 2. Clients (Post-Sale Management)

**Purpose:** Manage active client relationships and engagements

**Models:**
- `Client` - Post-sale client records (created from accepted proposals)
- `ClientEngagement` - Engagement history with version tracking
- `ClientPortalUser` - Client portal access and permissions
- `ClientNote` - Internal notes about clients

**Flow:** Proposal Acceptance → Client Creation → Ongoing Engagement

**Key Features:**
- Client hub with unified view of projects, documents, invoices
- Engagement versioning for renewals
- Portal access management
- Source tracking (from which prospect/proposal)

### 3. Projects (Execution & Time Tracking)

**Purpose:** Deliver work and track billable time

**Models:**
- `Project` - Consulting engagements (linked to Clients, not CRM)
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

- **Docker & Docker Compose** (required for backend)
- **Node.js 18+** (for frontend development)
- **Git** (for version control)

### Quick Start (Automated Setup)

**NEW:** Use our automated setup script for first-time setup:

```bash
# 1. Clone the repository
git clone <repository-url>
cd OS

# 2. Run automated setup (creates migrations, initializes database, creates admin user)
./setup-migrations.sh
```

The script will:
- ✅ Start PostgreSQL database
- ✅ Build web container with all dependencies
- ✅ Create database migrations for all 5 modules
- ✅ Apply migrations to database
- ✅ Prompt you to create superuser account

### Manual Setup (Alternative)

If you prefer step-by-step control:

1. **Clone the repository**

```bash
git clone <repository-url>
cd OS
```

2. **Copy environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration (see Environment Variables section below)
```

3. **Start the database**

```bash
docker-compose up -d db
```

4. **Build and run the web container**

```bash
docker-compose build web
docker-compose up web
```

This will:
- Install Python dependencies (including pytest-cov, python-json-logger)
- Auto-create database migrations on first run
- Auto-apply migrations
- Start Django development server

5. **Create a superuser**

```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Access the application**

- **Backend API:** http://localhost:8000/api/
- **API Documentation (Swagger):** http://localhost:8000/api/docs/
- **API Documentation (ReDoc):** http://localhost:8000/api/redoc/
- **Django Admin:** http://localhost:8000/admin/

### Frontend Development

```bash
cd src/frontend
npm install
npm run dev
```

Frontend will run on http://localhost:3000

### Verify Installation

Run these commands to verify everything is working:

```bash
# Check backend health
curl http://localhost:8000/api/

# Run tests with coverage
docker-compose exec web pytest --cov=modules --cov=api

# Check frontend
curl http://localhost:3000
```

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

Run the full test suite with coverage reporting:

```bash
# Run all tests with coverage
docker-compose exec web pytest

# Run specific test modules
docker-compose exec web pytest tests/crm/
docker-compose exec web pytest tests/projects/
docker-compose exec web pytest tests/finance/

# Run with detailed coverage report
docker-compose exec web pytest --cov=modules --cov=api --cov-report=html

# View coverage report (opens in browser)
open src/htmlcov/index.html
```

**Test Coverage Target:** 70% minimum (enforced in CI/CD)

**Available Test Suites:**
- `tests/crm/test_serializers.py` - CRM validation tests
- `tests/projects/test_serializers.py` - Projects validation tests
- `tests/finance/test_serializers.py` - Finance validation tests
- `tests/documents/test_serializers.py` - Documents tests
- `tests/assets/test_serializers.py` - Assets tests

### Continuous Integration

All pull requests automatically run:
- ✅ Code linting (flake8, black, isort)
- ✅ Test suite with coverage
- ✅ Security audit (safety, trufflehog)
- ✅ Docker build verification
- ✅ Frontend build

See `.github/workflows/ci.yml` for full CI/CD configuration.

---

## API Documentation

### Interactive Documentation

- **Swagger UI:** http://localhost:8000/api/docs/ - Try API endpoints directly in the browser
- **ReDoc:** http://localhost:8000/api/redoc/ - Clean, searchable API reference

### Complete API Guide

See **[API_USAGE.md](API_USAGE.md)** for comprehensive documentation including:
- Authentication (JWT tokens)
- Complete endpoint reference for all 5 modules
- Request/response examples
- Error handling
- Rate limiting
- Pagination and filtering
- Best practices

### Quick Reference

| Module | Endpoints | Key Features |
|--------|-----------|--------------|
| **CRM** | `/api/crm/` | Leads, Prospects, Campaigns, Proposals (3 types), Contracts, auto-conversion to Clients |
| **Clients** | `/api/clients/` | Client management, Engagements, Portal users, Notes |
| **Projects** | `/api/projects/` | Projects, Tasks (Kanban), Time Entries (auto-calculate billed amounts) |
| **Finance** | `/api/finance/` | Invoices, Bills, Ledger Entries, Stripe integration with webhook handler |
| **Documents** | `/api/documents/` | Folders (hierarchical), Documents (S3 upload/download with presigned URLs) |
| **Assets** | `/api/assets/` | Assets (depreciation tracking), Maintenance Logs |

### Authentication Example

```bash
# Get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Use token
curl http://localhost:8000/api/crm/clients/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

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

**Status:** ✅ CRM Frontend Complete - Backend Migrations Pending

**Completed Features:**
- ✅ Authentication (JWT with token refresh & blacklist)
- ✅ **NEW: Complete CRM Frontend**
  - ✅ Leads page (capture, scoring, convert to prospect)
  - ✅ Prospects page (sales pipeline, filtering, metrics)
  - ✅ Campaigns page (performance tracking for new business + client engagement)
  - ✅ Proposals page (3 types: new business, expansion, renewal)
- ✅ **NEW: Clients Module Separation**
  - ✅ Post-sale client management separate from CRM
  - ✅ Automated client creation on proposal acceptance
  - ✅ Engagement versioning for renewals
- ✅ **NEW: Reorganized Navigation**
  - ✅ Sidebar layout with 4 sections
  - ✅ CRM & Sales section (pre-sale)
  - ✅ Client Management section (post-sale)
  - ✅ Delivery section (projects, time)
  - ✅ Resources section (documents, assets, knowledge)
- ✅ CRM Backend (Lead, Prospect, Campaign, Proposal models with signals)
- ✅ Clients Backend (Client, ClientEngagement, ClientPortalUser models)
- ✅ Time tracking UI (Kanban board)
- ✅ Invoice generation & management
- ✅ S3 integration for documents (upload/download with presigned URLs)
- ✅ Stripe integration for payments (webhook handler for 5 event types)
- ✅ Comprehensive test suite (70%+ coverage target)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Environment validation on startup
- ✅ Error boundaries & loading states
- ✅ API documentation (Swagger + ReDoc)

**Next Steps:**
- 🔄 Run database migrations for new CRM/Clients structure
- 🔄 Test end-to-end CRM workflow (Lead → Client)
- ⏳ Client Portal enhancement (Work, Chat, Billing sections)

**Deployment Readiness:**
- ✅ NOW Phase: Development blockers resolved
- 🔄 NEXT Phase: Stabilization (5-7 days) - In Progress
- ⏳ LATER Phase: Production hardening (4-5 weeks) - Planned

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete production deployment guide.
See **[TODO.md](TODO.md)** for prioritized task list.

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

### Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values. See **[.env.example](.env.example)** for complete documentation of all variables.

### Required Variables

**Django Core:**
- `DJANGO_SECRET_KEY` - Cryptographically random string (50+ chars)
- `DJANGO_DEBUG` - Set to `False` in production
- `DJANGO_ALLOWED_HOSTS` - Comma-separated domain list

**Database:**
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`

**Production-Only (when DEBUG=False):**
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

### Environment Validation

The application automatically validates environment variables on startup:
- ✅ Checks all required variables are present
- ✅ Detects insecure default values in production
- ✅ Validates `SECRET_KEY` strength
- ✅ Validates `ALLOWED_HOSTS` configuration
- ❌ **Blocks startup** if critical issues detected

See `src/config/env_validator.py` for validation logic.

### Generate Secure SECRET_KEY

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
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
