# ARCHITECTURE.md — System Architecture
Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Dependencies: CODEBASECONSTITUTION.md; DOMAIN_MODEL.md; REPO_MAP.md

## Overview

ConsultantPro is a multi-tenant SaaS platform built as a Django modular monolith with clear module boundaries and privacy-first architecture.

## Architecture Principles

1. **Multi-Tenant Isolation** - Hard boundaries between firms enforced at database and application layers
2. **Privacy by Default** - Platform staff cannot access customer content without audited break-glass access
3. **Modular Monolith** - Bounded contexts per domain, testable in isolation
4. **API-First** - RESTful API with OpenAPI documentation
5. **Secure Defaults** - Security built-in, not bolted-on

## System Components

### Backend (Django 4.2 LTS)

**Core Framework:**
- Django 4.2 LTS (Python web framework)
- Django REST Framework (API layer)
- PostgreSQL 15 (primary database with RLS support)
- Gunicorn (WSGI server for production)

**Authentication & Authorization:**
- JWT tokens (django-rest-framework-simplejwt)
- OAuth/SAML (django-allauth with Google/Microsoft providers)
- MFA (django-otp with TOTP support)
- LDAP/Active Directory integration (ldap3)

**Module Organization (src/modules/):**

**Tier 0 - Foundation:**
- `firm/` - Multi-tenant workspace/firm management, RLS enforcement
- `auth/` - Authentication, authorization, user management

**Core Business Domains:**
- `crm/` - Customer relationship management (leads, prospects, proposals)
- `clients/` - Client management and portal
- `projects/` - Project and task management
- `finance/` - Billing, invoicing, payment processing
- `documents/` - Document management with versioning

**Engines & Automation:**
- `pricing/` - Pricing engine with versioned rulesets
- `delivery/` - Delivery templates and workflow DAGs
- `recurrence/` - Recurrence engine for recurring events
- `orchestration/` - Multi-step workflow orchestration
- `automation/` - Marketing automation (triggers, actions, visual builder)

**Communications & Integration:**
- `communications/` - Messages, conversations, threads
- `email_ingestion/` - Email ingestion, mapping, triage
- `calendar/` - Calendar, scheduling, booking links
- `sms/` - SMS messaging (Twilio)
- `webhooks/` - Webhook platform for external integrations

**Supporting Modules:**
- `core/` - Shared infrastructure (audit, purge, governance)
- `marketing/` - Marketing automation primitives
- `support/` - Support/ticketing with SLA tracking
- `onboarding/` - Client onboarding workflows
- `knowledge/` - Knowledge system (SOPs, training)
- `jobs/` - Background job queue and DLQ
- `snippets/` - Quick text insertion
- `accounting_integrations/` - QuickBooks, Xero
- `esignature/` - DocuSign integration
- `ad_sync/` - Active Directory synchronization

### Frontend (React + TypeScript)

- React 18 with TypeScript
- Vite build tool
- React Query for data fetching
- React Flow for visual workflow builder
- Component library: TBD (likely Tailwind CSS + Headless UI)

### Database Layer

**PostgreSQL 15:**
- Row-Level Security (RLS) for tenant isolation
- Multi-tenancy via `firm_id` foreign keys
- Audit logging tables (immutable logs)
- JSON fields for flexible metadata

**RLS Policy Pattern:**
```sql
CREATE POLICY tenant_isolation ON table_name
  USING (firm_id = current_setting('app.current_firm_id')::integer);
```

### Integration Layer

**Payment Processing:**
- Stripe (credit cards, ACH, subscriptions)
- Square (point-of-sale, payments)

**E-Signature:**
- DocuSign (envelopes, templates, webhooks)

**Accounting:**
- QuickBooks Online (invoices, expenses, sync)
- Xero (invoices, contacts, bank feeds)

**Communications:**
- Twilio (SMS, two-way messaging, campaigns)
- Email (SMTP/IMAP for ingestion)

**Identity:**
- Google OAuth (authentication)
- Microsoft OAuth (authentication)
- Active Directory/LDAP (user sync, authentication)

### Observability

**Logging:**
- Structured JSON logging (python-json-logger)
- Sentry for error tracking and performance monitoring

**Monitoring:**
- Health check endpoint: `/health/`
- Readiness check endpoint: `/ready/`
- OpenAPI documentation: `/api/docs/`

## Data Flow

### Request Flow
1. Client → NGINX/Load Balancer
2. Gunicorn → Django
3. Middleware stack (CORS, Auth, Firm context)
4. View/ViewSet (permission checks)
5. Serializer (validation)
6. Business logic (service layer)
7. Database (with RLS)
8. Response serialization
9. Client

### Multi-Tenant Context
- JWT token contains `firm_id` claim
- Middleware sets `firm_id` in database session
- RLS policies enforce at database level
- Application layer filters by firm for redundancy

### Audit Trail
- Sensitive operations log to audit tables
- Metadata only (no content) for privacy
- Immutable logs (append-only)
- Includes: who, what, when, result

## Security Architecture

### Authentication Flow
1. User provides credentials
2. Verify against database or OAuth provider
3. Optionally verify MFA code
4. Issue JWT access + refresh tokens
5. Client includes access token in Authorization header

### Authorization Layers
1. **Authentication** - Valid JWT token required
2. **Firm Membership** - User belongs to firm
3. **Role Permissions** - User has required role/permissions
4. **Object Permissions** - User can access specific object
5. **RLS** - Database enforces tenant isolation

### Break-Glass Access
- Platform operators have metadata-only access by default
- Break-glass access requires: reason, time limit, approval
- All break-glass actions audited with alert notifications
- Automatic expiration and review process

## Deployment Architecture

### Development
- Docker Compose for local development
- PostgreSQL container
- Django development server
- Vite dev server with HMR

### Production (Recommended)
- Container orchestration (Kubernetes, ECS, or similar)
- Managed PostgreSQL (RDS, Cloud SQL, or similar)
- Static files on S3/CloudFront
- Gunicorn with multiple workers
- NGINX as reverse proxy
- Sentry for error tracking
- Automated backups and disaster recovery

## API Design

### Versioning
- URL-based versioning: `/api/v1/`, `/api/v2/`
- Deprecation notices via headers
- Minimum 6-month deprecation period

### Response Format
```json
{
  "data": { ... },
  "meta": {
    "count": 100,
    "next": "url",
    "previous": "url"
  }
}
```

### Error Format
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input",
    "details": { ... }
  }
}
```

## Future Considerations

- Event sourcing for critical entities
- CQRS for read-heavy operations
- GraphQL for flexible client queries
- WebSocket support for real-time features
- Mobile apps (iOS/Android)
- End-to-end encryption (E2EE) infrastructure
