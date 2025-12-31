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

- **[Getting Started Tutorial](01-tutorials/getting-started.md)** - Complete setup guide for new developers
- **[Architecture Overview](04-explanation/architecture-overview.md)** - System design and key concepts
- **[Platform Capabilities Inventory](03-reference/platform-capabilities.md)** - What exists and what's missing
- **[Documentation Best Practices](04-explanation/documentation-best-practices.md)** - How we organize and write docs
- **[Tier System Reference](03-reference/tier-system.md)** - Architecture governance model
- **[API Reference](03-reference/api-usage.md)** - Complete API documentation
- **[Environment Variables](03-reference/environment-variables.md)** - Configuration reference
- **[Management Commands](03-reference/management-commands.md)** - Django commands reference
- **[Production Deployment](02-how-to/production-deployment.md)** - Deploy to production
- **[Firm Admin Guide](06-user-guides/firm-admin-guide.md)** - End-user guide for administrators
- **[Client Portal Guide](06-user-guides/client-portal-guide.md)** - Guide for client portal users
- **[System Invariants](../spec/SYSTEM_INVARIANTS.md)** - Core system rules
- **[Changelog](../CHANGELOG.md)** - Release history and changes
- **[Contributing Guide](../CONTRIBUTING.md)** - Development workflow

## Operational Documentation

- **[Runbooks](runbooks/README.md)** - Operational procedures for common failures, deployments, and incident response
- **[Compliance Documentation](compliance/)** - Compliance verification docs (boundaries, pagination, feature flags)

## Tier-Specific Documentation

Documentation for each tier is organized in directories:
- `docs/tier0/` - Foundational Safety
- `docs/tier1/` - Schema Truth & CI Truth
- `docs/tier2/` - Authorization & Ownership
- `docs/tier3/` - Data Integrity & Privacy
- `docs/tier4/` - Billing & Monetization
- `docs/tier5/` - Durability, Scale & Exit

For a consolidated view, see [Tier System Reference](03-reference/tier-system.md).
