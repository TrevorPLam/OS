# Contributing to ConsultantPro

Thanks for your interest in improving ConsultantPro. This guide outlines expectations for code and documentation changes.

Last Updated: 2026-01-16

## Ground Rules

- **Follow tier governance:** No tier skipping. See ARCHITECTURE.md for tier definitions and rules.
- **Preserve tenant isolation:** Security and privacy are the highest priority. Use `FirmScopedManager`/`FirmScopedMixin` instead of raw `Model.objects.*` for firm data, and wrap background/CLI DB work in `firm_db_session(firm)` so `app.current_firm_id` is set for RLS (see `docs/SECURITY_RLS.md`).
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

## Query Efficiency Tests

Use the performance marker to guard against N+1 regressions on critical endpoints:

```bash
make test-performance
```

Guidelines:
- Prefer `select_related` for single-valued foreign keys and `prefetch_related` for collections.
- Use `tests.utils.query_assertions.assert_max_queries` to set a **max** query budget per endpoint test.
- Keep budgets intentionally permissive; adjust if serializer or middleware changes legitimately add queries.
- Add comments explaining the query budget choice and the endpoint it protects.

## Running Type Checks

```bash
make typecheck
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

## Architecture Decision Records (ADRs)

ADRs capture important architectural decisions and their context so humans and agents can understand the reasoning behind changes.

1. Review ADR guidance in `docs/05-decisions/README.md` to confirm the decision warrants an ADR.
2. Copy `docs/05-decisions/ADR-0000-template.md` for new ADRs and fill in every section.
3. Store the new ADR in `docs/05-decisions/` and add it to the ADR index table.

## Pull Requests

- Clearly describe **what** changed and **why**.
- Call out any migrations, configuration updates, or operational impacts.
- Confirm that relevant documentation was updated.
