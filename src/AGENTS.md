# AGENTS.md — Backend Source Directory

Last Updated: 2026-01-21
Applies To: All agents working in `/src/`

**IMPORTANT**: See `/BESTPR.md` for comprehensive best practices, patterns, and conventions.

## Purpose

This directory contains the Django backend for ConsultantPro, a multi-tenant SaaS platform for management consulting firms.

## Directory Structure

```
src/
├── api/              # REST API endpoints (public-facing serializers/views)
├── config/           # Django settings, URLs, middleware
├── frontend/         # React + TypeScript frontend (Vite)
├── modules/          # Business domain modules (modular monolith)
├── templates/        # Django templates (error pages)
├── logs/             # Application logs (gitignored)
├── manage.py         # Django management script
├── job_guards.py     # Background job safety decorators
└── permissions.py    # Global permission classes
```

## Architecture: Modular Monolith

This is a **modular monolith**, not microservices. Each module under `modules/` represents a bounded context with:
- Its own models, views, serializers, URLs
- Clear dependencies on other modules (documented in each module's AGENTS.md)
- Shared infrastructure via `modules/core/`

### Module Tiers

**Tier 0 - Foundation (CRITICAL):**
- `firm/` — Multi-tenant boundary. ALL data isolation depends on this.
- `auth/` — Authentication, authorization, MFA

**Core Business:**
- `crm/` — Pre-sale: Lead → Prospect → Proposal workflow
- `clients/` — Post-sale: Client management, portal
- `projects/` — Project execution, tasks, time tracking
- `finance/` — Billing, invoicing, payments
- `documents/` — Document management, versioning

**Engines:**
- `pricing/` — Versioned pricing rulesets
- `delivery/` — Delivery template DAGs
- `recurrence/` — Recurring event generation
- `orchestration/` — Multi-step workflow execution
- `automation/` — Visual workflow builder

**Communications:**
- `email_ingestion/` — Gmail/Outlook ingestion
- `calendar/` — Scheduling, booking links
- `sms/` — Twilio messaging
- `communications/` — Conversations, threads

**Integrations:**
- `accounting_integrations/` — QuickBooks, Xero
- `esignature/` — DocuSign
- `ad_sync/` — Active Directory
- `webhooks/` — Webhook platform
- `integrations/` — Native hub (Salesforce, Slack)

**Supporting:**
- `marketing/` — Tags, segments, templates
- `support/` — Ticketing, SLA
- `onboarding/` — Client onboarding
- `knowledge/` — SOPs, training
- `jobs/` — Background queue, DLQ
- `snippets/` — Quick text insertion
- `tracking/` — Site/event analytics

## Critical Invariants

1. **Firm Isolation**: Every query MUST be scoped to `request.firm`. Use `FirmScopedMixin` or `firm_scoped_queryset()`.

2. **Portal vs Staff**: Portal users (clients) have separate endpoints in `api/portal/`. They MUST NOT access staff endpoints.

3. **No Content Logging**: Customer content MUST NOT appear in logs. Use `modules.core.structured_logging`.

4. **Immutability Rules**: Published RuleSets, QuoteVersions, and DeliveryTemplates are immutable.

## Common Patterns

### Adding a New Model

```python
from modules.firm.utils import FirmScopedManager

class MyModel(models.Model):
    # REQUIRED: Firm foreign key
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="my_models",
    )
    
    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
```

### Adding a New ViewSet

```python
from modules.firm.utils import FirmScopedMixin

class MyViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    model = MyModel
    serializer_class = MySerializer
    # get_queryset() automatically scopes to request.firm
```

## Entry Points

- **Main URLs**: `config/urls.py`
- **Settings**: `config/settings.py`
- **Run server**: `python manage.py runserver`
- **Run tests**: `pytest` or `make test`

## Dependencies

- Django 4.2 LTS
- Django REST Framework
- PostgreSQL 15 (with RLS support)
- See `requirements.txt` for full list
