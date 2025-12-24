# Contributing to ConsultantPro

Thanks for your interest in improving ConsultantPro. This guide outlines expectations for code and documentation changes.

## Ground Rules

- **Follow tier governance:** No tier skipping. The rules in `docs/claude/NOTES_TO_CLAUDE.md` are authoritative.
- **Preserve tenant isolation:** Security and privacy are the highest priority.
- **Keep docs accurate:** Update documentation in the same change set as code changes.

## Development Workflow

1. Create a focused branch for your change.
2. Make the smallest change that solves the problem.
3. Run tests and any applicable checks.
4. Update or add documentation as needed.

## Running Tests

```bash
pytest
```

## Documentation Updates

- Use `docs/README.md` as the documentation map.
- Link to a single source of truth instead of duplicating instructions.
- Ensure security-sensitive data is never committed to the repo.

## Pull Requests

- Clearly describe **what** changed and **why**.
- Call out any migrations, configuration updates, or operational impacts.
- Confirm that relevant documentation was updated.
