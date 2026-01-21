# AGENTS.md — Documentation Directory

Last Updated: 2026-01-21
Applies To: All agents working in `/docs/`

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.

## Purpose

This directory contains all documentation for the ConsultantPro platform:
- User guides and tutorials
- Technical reference documentation
- Architecture Decision Records (ADRs)
- Runbooks for operations
- API documentation
- Compliance and security docs

## Structure

```
docs/
├── 01-tutorials/          # Step-by-step guides
├── 02-how-to/             # Task-oriented guides
├── 03-reference/          # Technical reference
├── 04-explanation/        # Conceptual explanations
├── 05-decisions/          # Architecture decisions
├── 06-user-guides/        # End-user documentation
├── 07-api-client/         # API client documentation
├── adr/                   # Architecture Decision Records
├── compliance/            # Compliance documentation
├── implementation/        # Implementation guides
├── integrations/          # Integration documentation
├── research/              # Research and investigations
├── runbooks/              # Operational runbooks
├── scripts/               # Documentation scripts and tools
└── specs/                 # Technical specifications (non-binding)
```

## Documentation Standards

### Format
- Use Markdown for all documentation
- Follow the [Diátaxis](https://diataxis.fr/) framework for organization
- Include frontmatter with metadata when appropriate

### Writing Style
- Clear, concise, and scannable
- Use examples and code snippets
- Include diagrams when helpful
- Keep docs up-to-date with code changes

### Validation
- Run `make docs-check` to validate documentation quality
- Check for broken links: `docs/scripts/check_markdown_links.py`
- Verify completeness: `docs/scripts/check_docs_completeness.py`

## Runbooks

Operational runbooks are stored in `runbooks/`:
- `DEPLOYMENT.md` — Deployment procedures
- `ROLLBACK.md` — Rollback procedures
- `INCIDENT_RESPONSE.md` — Incident response
- `BACKUP_RESTORE.md` — Backup and restore
- `SCALING.md` — Scaling procedures
- `FAILED_JOBS.md` — Failed job handling

## Scripts

Documentation automation scripts in `scripts/`:
- `check_docs_completeness.py` — Verify docs coverage
- `check_markdown_links.py` — Check for broken links
- `validate_docs_structure.py` — Validate structure
- `check_openapi_tier_a.py` — API documentation checks

## Specs (Non-Binding)

The `specs/` directory contains:
- Technical specifications (non-authoritative)
- Design proposals (pending approval)
- Research notes

**IMPORTANT**: Specs are NOT binding until converted to tasks in `TODO.md`.

## Reference

- **Governance**: See `/CODEBASECONSTITUTION.md`
- **Best Practices**: See `/BESTPR.md`
- **API Docs**: See `03-reference/` and `07-api-client/`
