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
- **[Tier System Reference](03-reference/tier-system.md)** - Architecture governance model
- **[API Reference](03-reference/api-usage.md)** - Complete API documentation
- **[Production Deployment](02-how-to/production-deployment.md)** - Deploy to production
- **[System Invariants](../spec/SYSTEM_INVARIANTS.md)** - Core system rules
- **[Contributing Guide](../CONTRIBUTING.md)** - Development workflow

## Tier-Specific Documentation

Documentation for each tier is organized in directories:
- `docs/tier0/` - Foundational Safety
- `docs/tier1/` - Schema Truth & CI Truth
- `docs/tier2/` - Authorization & Ownership
- `docs/tier3/` - Data Integrity & Privacy
- `docs/tier4/` - Billing & Monetization
- `docs/tier5/` - Durability, Scale & Exit

For a consolidated view, see [Tier System Reference](03-reference/tier-system.md).
