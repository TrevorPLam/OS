# Data Models

Database schema, relationships, and data modeling documentation.

## Overview

UBOS uses PostgreSQL with Django ORM. This section documents:
- Database schema
- Model relationships
- Data modeling decisions
- Migration history

## Core Models

### Firm/Workspace
- **Firm** - Multi-tenant workspace
- **Workspace** - Firm workspace configuration

### User Management
- **User** - System users
- **Role** - User roles
- **Permission** - Access permissions

### Client Management
- **Client** - Client records
- **Contact** - Client contacts
- **Relationship** - Client relationships

### Project Management
- **Project** - Projects
- **Task** - Project tasks
- **Deliverable** - Project deliverables

### Finance
- **Invoice** - Invoices
- **Payment** - Payments
- **Ledger** - Financial ledger

## Model Relationships

### Multi-Tenancy
- All models are firm-scoped
- Firm isolation enforced at model level
- See `backend/modules/firm/` for firm model

### Relationships
- Client → Projects
- Projects → Tasks
- Projects → Invoices
- And more...

## Database Schema

- **Schema Diagrams** - (To be added)
- **Migration History** - See `backend/modules/*/migrations/`
- **Model Documentation** - See module-specific docs

## Data Modeling Principles

1. **Firm-Scoped** - All models scoped to firm
2. **Normalized** - Follow database normalization
3. **Auditable** - Audit trails where needed
4. **Versioned** - Version control for critical data

## Related Documentation

- [Architecture](../README.md) - System architecture
- [Module Documentation](../modules/README.md) - Module details
- [Development Guide](../../development/README.md) - Development practices
