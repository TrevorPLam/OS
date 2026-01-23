# Architecture

This section documents the system architecture, design decisions, and technical structure of UBOS.

## Overview

UBOS is built as a multi-tenant, domain-driven application with:
- **Django backend** - REST API with firm-scoped multi-tenancy
- **React frontend** - TypeScript-based SPA
- **Domain modules** - Organized by business domain

## Architecture Sections

### [System Architecture](README.md)
High-level architecture overview, technology stack, and system design.

### [Module Documentation](modules/README.md)
Documentation for each domain module:
- Core infrastructure
- Firm management
- CRM and clients
- Projects and delivery
- Finance and billing
- Documents and assets
- Communications and calendar
- Automation and orchestration
- And more...

### [Design Decisions](decisions/README.md)
Architecture Decision Records (ADRs) documenting key technical decisions.

### [Data Models](data-models/README.md)
Database schema, relationships, and data modeling decisions.

## Key Architectural Principles

1. **Multi-Tenancy** - Firm-scoped isolation
2. **Domain-Driven Design** - Modules organized by business domain
3. **API-First** - RESTful API design
4. **Security-First** - Security built into architecture
5. **Scalability** - Designed for growth

## Technology Stack

- **Backend:** Django 4.2, Python 3.11, PostgreSQL 15
- **Frontend:** React 18, TypeScript 5.9, Vite 5.4
- **Testing:** pytest, Vitest, Playwright
- **Infrastructure:** Docker, CI/CD

## Related Documentation

- [Development Guide](../development/README.md) - Development practices
- [Operations](../operations/README.md) - Deployment architecture
- [Security](../security/README.md) - Security architecture
