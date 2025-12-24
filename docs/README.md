# Documentation Index

This directory contains the authoritative documentation set for ConsultantPro. Use this index to find the right source of truth and avoid duplicating information across files.

## Getting Started

- **Project overview & setup:** [`../README.md`](../README.md)
- **API usage & examples:** [`../API_USAGE.md`](../API_USAGE.md)
- **Deployment & operations:** [`../DEPLOYMENT.md`](../DEPLOYMENT.md)

## Architecture & Governance

- **Authoritative rules (must-follow):** [`claude/NOTES_TO_CLAUDE.md`](claude/NOTES_TO_CLAUDE.md)
- **Tier prompts & execution:** [`claude/prompts/`](claude/prompts/)
- **Tier details:** [`claude/tiers/`](claude/tiers/)
- **Tier backlog:** [`../TODO.md`](../TODO.md)
- **Architecture refactor plan:** [`../ARCHITECTURE_REFACTOR_PLAN.md`](../ARCHITECTURE_REFACTOR_PLAN.md)
- **Backend enhancements log:** [`../BACKEND_ENHANCEMENTS.md`](../BACKEND_ENHANCEMENTS.md)

## Operational References

- **Docker Compose setup:** [`../docker-compose.yml`](../docker-compose.yml)
- **Docker image build:** [`../Dockerfile`](../Dockerfile)
- **Migration helpers:** [`../migrate.sh`](../migrate.sh), [`../setup-migrations.sh`](../setup-migrations.sh)

## Documentation Standards

- **Single source of truth:** Avoid duplicating procedural steps. Link to the canonical file instead.
- **Accuracy first:** Update docs in the same change set as the code they describe.
- **Consistency:** Use the same terminology as the codebase ("firm", "client", "portal user").
- **Security-aware:** Never document real secrets or production credentials.

## Missing or Out-of-Date Docs?

If a workflow is unclear, update the most relevant file and add a link here so it remains discoverable.
