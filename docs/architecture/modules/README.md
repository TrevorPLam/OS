# Module Documentation

UBOS is organized into domain modules. Each module represents a business domain and contains related functionality.

## Module Structure

Modules are located in `backend/modules/` and follow a consistent structure:
- `models.py` - Database models
- `views.py` - API endpoints
- `serializers.py` - API serialization
- `urls.py` - URL routing
- `admin.py` - Django admin configuration

## Core Modules

### Infrastructure
- **[core](core.md)** - Shared infrastructure, utilities, base classes
- **[firm](firm.md)** - Multi-tenant foundation, workspace management
- **[auth](auth.md)** - Authentication, authorization, MFA, OAuth/SAML

### Business Modules

#### Client Management
- **[clients](clients.md)** - Client management and portal
- **[crm](crm.md)** - CRM, leads, prospects, proposals
- **[onboarding](onboarding.md)** - Client onboarding workflows

#### Project & Delivery
- **[projects](projects.md)** - Project management
- **[delivery](delivery.md)** - Delivery templates and workflows
- **[documents](documents.md)** - Document management
- **[assets](assets.md)** - Asset management

#### Finance
- **[finance](finance.md)** - Billing, invoicing, payments
- **[pricing](pricing.md)** - Pricing engine
- **[accounting_integrations](accounting_integrations.md)** - QuickBooks, Xero integrations

#### Communications
- **[communications](communications.md)** - Messages, conversations
- **[email_ingestion](email_ingestion.md)** - Email processing
- **[sms](sms.md)** - SMS messaging
- **[calendar](calendar.md)** - Calendar and scheduling

#### Automation & Workflows
- **[automation](automation.md)** - Automation workflows, triggers, actions
- **[orchestration](orchestration.md)** - Orchestration engine
- **[recurrence](recurrence.md)** - Recurrence engine

#### Additional Modules
- **[support](support.md)** - Support/ticketing system
- **[marketing](marketing.md)** - Marketing automation
- **[knowledge](knowledge.md)** - Knowledge base, SOPs, playbooks
- **[tracking](tracking.md)** - Time tracking
- **[jobs](jobs.md)** - Background jobs
- **[webhooks](webhooks.md)** - Webhook management
- **[integrations](integrations.md)** - Third-party integrations
- **[ad_sync](ad_sync.md)** - Active Directory sync
- **[esignature](esignature.md)** - E-signature functionality
- **[snippets](snippets.md)** - Code snippets

## Module Documentation Standards

Each module should document:
- Purpose and scope
- Key models and relationships
- API endpoints
- Business logic
- Integration points
- Configuration options

## Module Boundaries

See [`.repo/policy/BOUNDARIES.md`](../../.repo/policy/BOUNDARIES.md) for module boundary rules and import restrictions.

## Related Documentation

- [Architecture Overview](../README.md)
- [Data Models](../data-models/README.md)
- [Design Decisions](../decisions/README.md)
