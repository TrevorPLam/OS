# DOCS_INDEX.md — Documentation Index

Document Type: Reference
Version: 2.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Canonical
Canonical Status: Canonical

## Start Here

New to this repository? Start with these documents in order:

1. [README.md](../README.md) - Project overview and quick start
2. [READMEAI.md](../READMEAI.md) - AI agent operating instructions
3. [CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) - Repository standards and rules
4. [SETUP.md](SETUP.md) - Development environment setup
5. [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
6. [REPO_MAP.md](REPO_MAP.md) - Repository structure guide
7. [TODO.md](../TODO.md) - Current priorities and roadmap

## By Task

Find documentation by what you're trying to accomplish:

### Getting Started
- **First time setup** → [SETUP.md](SETUP.md)
- **Understanding the project** → [README.md](../README.md)
- **Contributing code** → [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Learning the system** → [01-tutorials/](01-tutorials/)

### Development
- **Implementing a feature** → [TODO.md](../TODO.md) → [CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) → [REPO_MAP.md](REPO_MAP.md)
- **Fixing a bug** → Module tests → API docs at `/api/docs/`
- **Running tests** → [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Understanding decisions** → [05-decisions/](05-decisions/)

### Operations
- **Deploying to production** → [02-how-to/](02-how-to/)
- **Troubleshooting** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Running operations** → [OPERATIONS.md](OPERATIONS.md)
- **Runbooks** → [runbooks/](runbooks/)

### Audits & Quality
- **Running code audits** → [../CODE_AUDIT.md](../CODE_AUDIT.md)
- **Security baseline** → [SECURITY_BASELINE.md](SECURITY_BASELINE.md)
- **Definition of done** → [03-reference/policies/definition-of-done.md](03-reference/policies/definition-of-done.md)

### Documentation
- **Understanding docs structure** → [../DOCS_ROOT.md](../DOCS_ROOT.md)
- **Finding any doc** → This file (DOCS_INDEX.md)
- **Repository structure** → [REPO_MAP.md](REPO_MAP.md)

## By Topic

### Architecture & Design
- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete system architecture
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Core entities and relationships
- [PILLARS.md](PILLARS.md) - Feature areas and capabilities
- [BOUNDARY_RULES.md](BOUNDARY_RULES.md) - Boundary enforcement
- [THREAT_MODEL.md](THREAT_MODEL.md) - Security analysis
- [03-reference/site-tracking-architecture.md](03-reference/site-tracking-architecture.md) - Site & event tracking architecture
- [03-reference/site-messages.md](03-reference/site-messages.md) - Site message system and builder contracts
- [03-reference/portal-branding.md](03-reference/portal-branding.md) - Portal branding & custom domains
- [03-reference/event-bus-architecture.md](03-reference/event-bus-architecture.md) - Event bus topology and contracts
- [03-reference/integration-marketplace-architecture.md](03-reference/integration-marketplace-architecture.md) - Marketplace data model and flows
- [04-explanation/audit-review-dashboard.md](04-explanation/audit-review-dashboard.md) - Audit dashboard UX blueprint

### API Documentation
- [ENDPOINTS.md](ENDPOINTS.md) - API reference
- [03-reference/api/](03-reference/api/) - Complete API docs
- [03-reference/policies/api-versioning.md](03-reference/policies/api-versioning.md) - Version lifecycle
- [03-reference/policies/api-deprecation.md](03-reference/policies/api-deprecation.md) - Deprecation process
- API docs at `/api/docs/` (Swagger UI when running)

### Security & Compliance
- [SECURITY_BASELINE.md](SECURITY_BASELINE.md) - Security requirements
- [THREAT_MODEL.md](THREAT_MODEL.md) - Threat analysis
- [BOUNDARY_RULES.md](BOUNDARY_RULES.md) - Security boundaries
- [compliance/](compliance/) - Compliance documentation
- [../SECURITY.md](../SECURITY.md) - Security vulnerability reporting

### Governance & Standards
- [../CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) - Repository constitution (canonical)
- [../READMEAI.md](../READMEAI.md) - AI agent instructions
- [../CODE_AUDIT.md](../CODE_AUDIT.md) - Code audit pipeline
- [../DOCS_ROOT.md](../DOCS_ROOT.md) - Documentation governance
- [codingconstitution.md](codingconstitution.md) - Supporting reference (backward compatibility)
- [05-decisions/](05-decisions/) - Architecture Decision Records

### Operations
- [OPERATIONS.md](OPERATIONS.md) - Setup and running
- [02-how-to/](02-how-to/) - Production deployment guides
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [runbooks/](runbooks/) - Operational procedures

### Development Guides
- [01-tutorials/](01-tutorials/) - Learning-oriented guides
- [02-how-to/](02-how-to/) - Problem-solving guides
- [06-user-guides/](06-user-guides/) - End-user documentation
- [07-api-client/](07-api-client/) - API client guides

### Research & Spikes
- [research/scim-2.0-research.md](research/scim-2.0-research.md) - SCIM provisioning scope and security
- [research/ecommerce-platform-research.md](research/ecommerce-platform-research.md) - E-commerce platform comparison and rollout plan

## By Role

### For Founders/Operators
Start here to understand control and governance:
1. [../READMEAI.md](../READMEAI.md) - AI agent control
2. [../CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) - Repository rules
3. [../TODO.md](../TODO.md) - Current priorities
4. [../CODE_AUDIT.md](../CODE_AUDIT.md) - Audit pipeline
5. [../DOCS_ROOT.md](../DOCS_ROOT.md) - Documentation governance

### For AI Agents
Mandatory reading order:
1. [../READMEAI.md](../READMEAI.md) - Operating instructions
2. [../CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) - Rules and standards
3. [../TODO.md](../TODO.md) - Current priorities
4. This file (DOCS_INDEX.md) - Navigation hub
5. [REPO_MAP.md](REPO_MAP.md) - Repository structure
6. Relevant module documentation for the task

### For Developers
Quick access to development resources:
1. [SETUP.md](SETUP.md) - Environment setup
2. [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
3. [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Domain model
4. [CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow
5. [03-reference/](03-reference/) - Technical reference
6. API docs at `/api/docs/`

## Canonical Docs

These are the single source of truth for their topics:

### Root-Level Canonical Docs
- [../READMEAI.md](../READMEAI.md) - AI agent instructions
- [../CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) - Repository constitution
- [../CODE_AUDIT.md](../CODE_AUDIT.md) - Audit pipeline
- [../DOCS_ROOT.md](../DOCS_ROOT.md) - Documentation governance
- [../TODO.md](../TODO.md) - Task tracking
- [../CHANGELOG.md](../CHANGELOG.md) - Release history

### Docs-Level Canonical Docs
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Domain entities
- [REPO_MAP.md](REPO_MAP.md) - Repository structure
- [SETUP.md](SETUP.md) - Development setup
- [ENDPOINTS.md](ENDPOINTS.md) - API reference
- [SECURITY_BASELINE.md](SECURITY_BASELINE.md) - Security standards
- [OPERATIONS.md](OPERATIONS.md) - Operations guide

### Supporting Reference (not duplicates)
- [CODEBASECONSTITUTION_STARTER.md](CODEBASECONSTITUTION_STARTER.md) - Template reference
- [codingconstitution.md](codingconstitution.md) - Supporting reference copy (see root CODEBASECONSTITUTION.md for canonical)
- [PILLARS.md](PILLARS.md) - Feature categorization
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Issue resolution
- [GLOSSARY.md](GLOSSARY.md) - Terminology

## Documentation Structure

This repository follows the [Diátaxis framework](https://diataxis.fr/) for documentation organization:

- **[01-tutorials/](01-tutorials/)** - Learning-oriented, step-by-step guides
- **[02-how-to/](02-how-to/)** - Problem-oriented, practical guides
- **[03-reference/](03-reference/)** - Information-oriented, technical descriptions
- **[04-explanation/](04-explanation/)** - Understanding-oriented, conceptual guides
- **[05-decisions/](05-decisions/)** - Architecture Decision Records (ADRs)
- **[06-user-guides/](06-user-guides/)** - End-user documentation
- **[07-api-client/](07-api-client/)** - API client documentation

### Additional Categories
- **[compliance/](compliance/)** - Compliance and regulatory docs
- **[implementation/](implementation/)** - Implementation details
- **[integrations/](integrations/)** - Integration guides
- **[research/](research/)** - Research and analysis
- **[runbooks/](runbooks/)** - Operational runbooks
- **[ARCHIVE/](ARCHIVE/)** - Deprecated documentation

## Archive

Deprecated documentation is stored in [ARCHIVE/](ARCHIVE/). Archived docs include:
- Historical analysis documents
- Deprecated implementation summaries
- Legacy roadmaps
- Superseded checklists

All archived docs start with "DEPRECATED" and include replacement references.

## Documentation Standards

All documentation should include:
- Document Type
- Version
- Last Updated
- Owner
- Status
- Canonical Status (for canonical docs)
- Dependencies (if applicable)

See [../CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) for full documentation standards and [../DOCS_ROOT.md](../DOCS_ROOT.md) for documentation governance.
