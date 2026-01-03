# Documentation Map

Use this guide to find the right documentation quickly. We follow the [Diátaxis framework](https://diataxis.fr/) to keep docs focused and useful.

| You are trying to... | Go to |
| --- | --- |
| I'm new / learn the system | `docs/01-tutorials/` |
| I need to do X | `docs/02-how-to/` |
| I need exact values / contracts | `docs/03-reference/` |
| I need to understand architecture/security | `docs/04-explanation/` |
| Why did we choose this? | `docs/05-decisions/` (ADRs) |
| I'm a customer / firm admin | `docs/06-user-guides/` |

## Key Documentation

### 🚀 Quick Start
- **[Setup Guide](SETUP.md)** - Development environment setup (Python, PostgreSQL, Docker)
- **[Documentation Index](DOCS_INDEX.md)** - Navigate all documentation
- **[Getting Started Tutorial](01-tutorials/getting-started.md)** - Complete setup guide for new developers
- **[Contributing Guide](../CONTRIBUTING.md)** - Development workflow
- **[Definition of Done](03-reference/policies/definition-of-done.md)** - PR checklist and quality gates

### 🏗️ Architecture & Design
- **[Architecture Overview](ARCHITECTURE.md)** - Complete system architecture (multi-tenant SaaS)
- **[Domain Model](DOMAIN_MODEL.md)** - Core entities and relationships
- **[Platform Pillars](PILLARS.md)** - Feature areas and capabilities
- **[Repository Map](REPO_MAP.md)** - Directory-by-directory codebase explanation
- **[Tier System Reference](03-reference/tier-system.md)** - Architecture governance model
- **[Boundary Rules](04-explanation/security/boundary-rules.md)** - Architectural boundary enforcement
- **[Threat Model](04-explanation/security/threat-model.md)** - Security threat analysis

### 🤖 AI & Governance
- **[READMEAI.md](../READMEAI.md)** - AI agent operating instructions
- **[Coding Constitution](../CODEBASECONSTITUTION.md)** - Repository governance and standards
- **[Code Audit](../CODE_AUDIT.md)** - Code audit pipeline
- **[Documentation Governance](../DOCS_ROOT.md)** - Documentation standards and structure
- **[Detailed Constitution](codingconstitution.md)** - Extended governance reference
- **[Starter Constitution](CODEBASECONSTITUTION_STARTER.md)** - Starter template reference

### API Documentation
- **[API Endpoints](ENDPOINTS.md)** - API reference and OpenAPI documentation
- **[API Reference](03-reference/api-usage.md)** - Complete API documentation
- **[API Versioning Policy](03-reference/policies/api-versioning.md)** - API version lifecycle and support
- **[API Deprecation Policy](03-reference/policies/api-deprecation.md)** - Deprecation process and guidelines

### Operations & Deployment
- **[Operations Guide](OPERATIONS.md)** - Setup, environment variables, running the application
- **[Production Deployment](02-how-to/production-deployment.md)** - Deploy to production
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Runbooks](runbooks/README.md)** - Operational procedures

### Compliance & Privacy
- **[Security Baseline](SECURITY_BASELINE.md)** - Security requirements and standards
- **[Permissions Model](PERMISSIONS.md)** - Authorization and permission system
- **[GDPR Data Export](04-explanation/implementations/gdpr-data-export.md)** - Right to access and data portability
- **[Data Retention](04-explanation/implementations/data-retention.md)** - Automated data retention policies
- **[Security Compliance](SECURITY_COMPLIANCE.md)** - Security compliance documentation

### Reference Materials
- **[Platform Capabilities Inventory](03-reference/platform-capabilities.md)** - What exists and what's missing
- **[Environment Variables](03-reference/environment-variables.md)** - Configuration reference
- **[Management Commands](03-reference/management-commands.md)** - Django commands reference
- **[Hidden Assumptions](03-reference/assumptions.md)** - Key assumptions and design decisions
- **[Glossary](GLOSSARY.md)** - Terminology definitions
- **[Style Guide](STYLE_GUIDE.md)** - Documentation and code style standards

### User Guides
- **[Firm Admin Guide](06-user-guides/firm-admin-guide.md)** - End-user guide for administrators
- **[Client Portal Guide](06-user-guides/client-portal-guide.md)** - Guide for client portal users

### Implementation Tracking
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Completed assessment issues and progress
- **[Documentation Analysis](DOCUMENTATION_ANALYSIS.md)** - Documentation consolidation plan

### System Specifications
- **[System Invariants](../spec/SYSTEM_INVARIANTS.md)** - Core system rules
- **[System Spec Alignment](SYSTEM_SPEC_ALIGNMENT.md)** - Spec alignment documentation

### Other Resources
- **[Changelog](../CHANGELOG.md)** - Release history and changes
- **[Documentation Best Practices](04-explanation/documentation-best-practices.md)** - How we organize and write docs

## Documentation by Topic

### Security
- **[Threat Model](04-explanation/security/threat-model.md)** - STRIDE analysis and threat scenarios
- **[Boundary Rules](04-explanation/security/boundary-rules.md)** - Architectural boundary enforcement
- **[Security Compliance](SECURITY_COMPLIANCE.md)** - Security compliance documentation
- **[ASSESS-S6.2 Findings](../ASSESS-S6.2-FINDINGS.md)** - Multi-tenancy security audit

### API & Integration
- **[API Versioning Policy](03-reference/policies/api-versioning.md)** - Version lifecycle and support
- **[API Deprecation Policy](03-reference/policies/api-deprecation.md)** - Deprecation guidelines
- **[API Reference](03-reference/api-usage.md)** - Complete API documentation
- **[API Endpoint Authorization](API_ENDPOINT_AUTHORIZATION_MAPPING.md)** - Authorization mapping

### Compliance & Privacy
- **[GDPR Data Export](GDPR_DATA_EXPORT_IMPLEMENTATION.md)** - Right to access implementation
- **[Data Retention](DATA_RETENTION_IMPLEMENTATION.md)** - Retention policy system
- **[Erasure Implementation](ERASURE_ANONYMIZATION_IMPLEMENTATION.md)** - Data anonymization
- **[Compliance Documentation](compliance/)** - Compliance verification docs

### Operations
- **[Operations Guide](OPERATIONS.md)** - Setup and operations
- **[Runbooks](runbooks/README.md)** - Operational procedures
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### Implementation Documentation
- **[Billing Ledger](BILLING_LEDGER_IMPLEMENTATION.md)** - Billing ledger implementation
- **[Calendar Sync](CALENDAR_SYNC_ADMIN_TOOLING.md)** - Calendar sync tooling
- **[Client Portal](CLIENT_PORTAL_IA_IMPLEMENTATION.md)** - Client portal implementation
- **[Delivery Templates](DELIVERY_TEMPLATE_IMPLEMENTATION.md)** - Delivery template system
- **[Email Ingestion](EMAIL_INGESTION_RETRY_IMPLEMENTATION.md)** - Email ingestion retry logic
- **[Meeting Workflow](MEETING_WORKFLOW_EXECUTION.md)** - Meeting workflow execution
- **[Orchestration](ORCHESTRATION_COMPENSATION_IMPLEMENTATION.md)** - Orchestration compensation
- **[Pricing](PRICING_IMMUTABILITY_IMPLEMENTATION.md)** - Pricing immutability
- **[Recurrence](RECURRENCE_PAUSE_RESUME_IMPLEMENTATION.md)** - Recurrence pause/resume
- **[Workers & Queues](WORKERS_QUEUES_IMPLEMENTATION.md)** - Background workers and queues
- *[See full list in Implementation Summary](IMPLEMENTATION_SUMMARY.md#files-created)*

## Tier-Specific Documentation

Documentation for each tier is organized in directories:
- `docs/tier0/` - Foundational Safety
- `docs/tier1/` - Schema Truth & CI Truth
- `docs/tier2/` - Authorization & Ownership
- `docs/tier3/` - Data Integrity & Privacy
- `docs/tier4/` - Billing & Monetization
- `docs/tier5/` - Durability, Scale & Exit

For a consolidated view, see [Tier System Reference](03-reference/tier-system.md).
