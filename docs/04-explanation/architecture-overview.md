# Architecture Overview

This document provides a high-level overview of ConsultantPro's architecture, focusing on the key design decisions and patterns used throughout the system.

## Table of Contents

1. [Multi-Tenant Architecture](#multi-tenant-architecture)
2. [Tier System](#tier-system)
3. [Security Model](#security-model)
4. [Data Model](#data-model)
5. [API Design](#api-design)

## Multi-Tenant Architecture

ConsultantPro is built as a **multi-tenant SaaS platform** with strict tenant isolation at the firm level.

### Key Principles

1. **Firm-Level Isolation** - Each consulting firm is a separate tenant with complete data isolation
2. **Privacy by Default** - Platform operators cannot access customer content without explicit break-glass access
3. **Default-Deny Portal Access** - Client portal users are restricted to their own data only
4. **No Global Queries** - All database queries must be scoped to a firm

### Implementation

- Every model has a `firm` foreign key
- Firm context is resolved from subdomain, session, or token
- Querysets use `FirmScopedManager` to automatically filter by firm
- Middleware validates firm context on every request

**See:** [Tier 0: Foundational Safety](../03-reference/tier-system.md#tier-0-foundational-safety)

## Tier System

ConsultantPro uses a **strict tiered implementation model** to ensure security and privacy are never compromised.

### The Six Tiers

| Tier | Focus | Purpose |
|------|-------|---------|
| **0** | Foundational Safety | Tenant isolation, privacy controls, break-glass |
| **1** | Schema Truth & CI Truth | Database consistency, honest CI/CD |
| **2** | Authorization & Ownership | Access control, permissions |
| **3** | Data Integrity & Privacy | Purge semantics, audit logs |
| **4** | Billing & Monetization | Financial operations |
| **5** | Durability, Scale & Exit | Performance, exit flows |

### Critical Rules

1. **No tier may be skipped** - Each tier builds on the previous
2. **No tier may be partially completed** - Complete all tasks before moving on
3. **All changes preserve tenant isolation** - Security is non-negotiable
4. **CI must never lie** - Test failures must fail the build

**See:** [Tier System Reference](../03-reference/tier-system.md)

## Security Model

### Role-Based Access

**Platform Roles:**
- **Platform Operator** - Metadata-only access, no content visibility
- **Break-Glass Operator** - Temporary, audited content access for emergencies

**Firm Roles:**
- **Firm Master Admin (Owner)** - Full control, can override settings
- **Firm Admin** - Granular permissions management
- **Staff** - Least privilege, permissions enabled explicitly

**Client Roles:**
- **Portal Users** - Client-scoped access only, default-deny

### Permission Model

- All ViewSets have explicit permission classes
- No endpoint allows unauthenticated access
- Portal users are blocked from firm admin endpoints
- Break-glass access requires reason and automatic expiration

**See:** [Tier 2: Authorization & Ownership](../03-reference/tier-system.md#tier-2-authorization--ownership)

## Data Model

### Core Entities

```
Firm (Tenant)
  ├── Users (FirmMembership)
  ├── Clients
  │   ├── ClientEngagements
  │   ├── ClientPortalUsers
  │   └── ClientNotes
  ├── Projects
  │   ├── Tasks
  │   └── TimeEntries
  ├── Documents
  │   └── Versions
  ├── Invoices
  │   ├── CreditLedgerEntries
  │   └── Payments
  └── AuditEvents
```

### Key Relationships

- **CRM Module (Pre-Sale):** Lead → Prospect → Proposal → Contract
- **Clients Module (Post-Sale):** Client → Project → Task → TimeEntry → Invoice
- **Documents Module:** Folder → Document → Version
- **Audit Module:** All critical actions logged with firm context

### Data Integrity

- Foreign keys use `PROTECT` or `CASCADE` appropriately
- Tombstones preserve metadata after content purge
- Audit events are immutable (cannot be edited or deleted)
- Credit ledger entries are immutable

**See:** [System Invariants](../../spec/SYSTEM_INVARIANTS.md)

## API Design

### REST Principles

- RESTful endpoints following standard conventions
- JSON request/response format
- JWT authentication
- Rate limiting (100 req/min burst, 1000 req/hour sustained)

### API Structure

```
/api/
  ├── auth/          # Authentication (login, token refresh)
  ├── crm/           # Pre-sale (leads, prospects, proposals)
  ├── clients/       # Post-sale client management
  │   ├── /portal/   # Client portal endpoints
  │   └── /...       # Firm-facing endpoints
  ├── projects/      # Project management
  ├── finance/       # Invoicing and payments
  ├── documents/     # Document management
  └── assets/        # Asset tracking
```

### Documentation

- **Interactive Docs:** Swagger UI at `/api/docs/`
- **Clean Docs:** ReDoc at `/api/redoc/`
- **Complete Reference:** [API Usage Guide](../03-reference/api-usage.md)

### Rate Limiting

- Standard endpoints: 100 req/min (burst), 1000 req/hour
- Payment endpoints: 10 req/min
- Upload endpoints: 30 req/hour
- Anonymous: 20 req/hour

**See:** [API Usage Guide](../03-reference/api-usage.md)

## Technology Stack

### Backend

- **Framework:** Django 4.2 + Django REST Framework
- **Database:** PostgreSQL 15+
- **Authentication:** JWT (djangorestframework-simplejwt)
- **API Documentation:** drf-spectacular
- **File Storage:** AWS S3
- **Payment Processing:** Stripe

### Frontend

- **Framework:** React + TypeScript
- **Build Tool:** Vite
- **State Management:** React Context/Hooks
- **Routing:** React Router
- **UI Library:** Custom components

### Infrastructure

- **Containerization:** Docker + Docker Compose
- **Web Server:** Nginx (production)
- **App Server:** Gunicorn (production)
- **CI/CD:** GitHub Actions

## Deployment Architecture

### Development

```
Developer Machine
  ├── PostgreSQL (local)
  ├── Django (localhost:8000)
  └── React (localhost:3000)
```

### Production

```
Load Balancer
  ├── Nginx (SSL termination)
  │   └── Gunicorn Workers
  │       └── Django Application
  ├── PostgreSQL (managed service)
  └── S3 (document storage)
```

**See:** [Production Deployment Guide](../02-how-to/production-deployment.md)

## Next Steps

- **For Developers:** Start with [Getting Started Tutorial](../01-tutorials/getting-started.md)
- **For Contributors:** Review [Contributing Guide](../../CONTRIBUTING.md)
- **For Understanding Tiers:** Read [Tier System Reference](../03-reference/tier-system.md)
- **For API Integration:** See [API Usage Guide](../03-reference/api-usage.md)
