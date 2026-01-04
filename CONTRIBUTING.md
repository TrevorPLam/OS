# Contributing to ConsultantPro

Thanks for your interest in improving ConsultantPro. This guide outlines expectations for code and documentation changes.

## Ground Rules

- **Follow tier governance:** No tier skipping. See ARCHITECTURE.md for tier definitions and rules.
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

## Dependency Updates

### Frontend Dependencies

1. Check for outdated packages:
   ```bash
   cd src/frontend
   npm run deps:check
   ```
2. Update `package.json` with exact versions (no `^` or `~` ranges).
3. Run `npm install` to refresh `package-lock.json`.
4. Include both `package.json` and `package-lock.json` in the same commit.

## Documentation Updates

- Use `docs/README.md` as the documentation map.
- Follow the [Diátaxis framework](https://diataxis.fr/) for documentation structure.
- Link to a single source of truth instead of duplicating instructions.
- Ensure security-sensitive data is never committed to the repo.

## Pull Requests

- Clearly describe **what** changed and **why**.
- Call out any migrations, configuration updates, or operational impacts.
- Confirm that relevant documentation was updated.
