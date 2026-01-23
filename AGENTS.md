# AI Contribution Guide

**File**: `AGENTS.md`

> **Governance**: All agents must follow `.repo/policy/CONSTITUTION.md` - immutable rules for this repository.
> **Principles**: See `.repo/policy/PRINCIPLES.md` for operating principles that guide daily development.
> **Quality Gates**: See `.repo/policy/QUALITY_GATES.md` for merge rules and verification requirements.
> **Security**: See `.repo/policy/SECURITY_BASELINE.md` for security rules and HITL triggers.
> **HITL**: See `.repo/policy/HITL.md` for Human-In-The-Loop process and item management.
> **Boundaries**: See `.repo/policy/BOUNDARIES.md` for module boundary enforcement.
> **Best Practices**: See `.repo/policy/BESTPR.md` for repo-specific coding practices, structure, and delivery workflow.

## Commands

Run from repo root:
- `make setup` - Install backend/frontend dependencies
- `make lint` - Run linters (ruff + black for backend, eslint for frontend)
- `make test` - Run test suites (pytest + vitest)
- `make verify` - Local CI suite (light checks by default)
- `make verify SKIP_HEAVY=0` - Full suite (tests/build/OpenAPI)
- `make ci` - Alias for `make verify` (used by CI)

Backend-specific:
- `make -C backend migrate` - Run Django migrations
- `make -C backend openapi` - Generate OpenAPI schema

Frontend-specific:
- `make -C frontend test` - Run Vitest unit tests
- `make -C frontend e2e` - Run Playwright E2E tests

## Tech Stack

- **Backend**: Django 4.2, Python 3.11, PostgreSQL 15
- **Frontend**: React 18.3, TypeScript 5.9, Vite 5.4
- **Testing**: pytest (backend), Vitest + Playwright (frontend)
- **Linting**: ruff + black + mypy (backend), ESLint + tsc (frontend)

## Project Structure

See `.repo/policy/BESTPR.md` for detailed repository map. Quick reference:

```
backend/          # Django API and services
  modules/        # Domain modules (firm-scoped multi-tenancy)
  api/            # API endpoints
  config/         # Django settings, middleware
frontend/         # Vite/React client
  src/            # React components, pages, hooks
tests/            # Cross-cutting and integration tests
docs/             # Architecture, onboarding, runbooks
agents/tasks/     # Task management (TODO/BACKLOG/ARCHIVE)
```

## Code Style

### Backend (Django)
- Use Django REST Framework viewsets for CRUD operations
- All models are firm-scoped (inherit from FirmScopedMixin)
- Use type hints where practical (mypy is relaxed but preferred)

Example:
```python
class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
```

### Frontend (React)
- Use functional components with TypeScript
- Use React Query for data fetching
- Follow React Hook Form patterns for forms

Example:
```typescript
export const KnowledgeCenter: React.FC = () => {
  const { data } = useQuery({ queryKey: ['knowledge'] });
  return <div>...</div>;
};
```

## Testing

- Backend: Add tests in `tests/` or module-specific test files
- Frontend: Unit tests with Vitest, E2E with Playwright
- Always add/update tests for behavioral changes
- Ensure `make ci` passes before submitting

## Git Workflow

- Create branch for changes
- Keep changes minimal and focused (Article 4: incremental delivery, Principle 3: one change type per PR)
- Link changes to task in `agents/tasks/TODO.md` or `BACKLOG.md` (Article 5: traceability, Principle 25)
- Run `make verify` before opening PR (Article 2: verification evidence, Principle 6: evidence over vibes)
- Include filepaths in PR descriptions (Principle: global rule)
- Explain what, why, filepaths, verification, risks, rollback in PR (Principle 17: PR narration)
- Never commit secrets or `.env` files
- Archive completed tasks after PR merge (Article 5: strict traceability)

## Boundaries

See `.repo/policy/BOUNDARIES.md` for module boundary rules and `.repo/policy/SECURITY_BASELINE.md` for security prohibitions.

**NEVER:**
- Modify files in `migrations/` (auto-generated)
- Change public APIs without updating tests and docs (see Article 2: verification required)
- Refactor unrelated code (see Article 4: incremental delivery)
- Commit secrets, `.env`, or sensitive data (SECURITY_BASELINE.md: absolute prohibition)
- Skip running `make lint` before proposing changes
- Proceed with uncertain changes (see Article 3: mark UNKNOWN, route to HITL per `.repo/policy/HITL.md`)
- Make risky changes without HITL approval (see Article 6 & 8: safety first, `.repo/policy/HITL.md` for process)
- Cross module boundaries without justification (see BOUNDARIES.md, Principle 13)

**ALWAYS:**
- Run `make lint` before submitting
- Update tests for behavioral changes (Article 2: verification evidence, Principle 6)
- Keep changes focused on the task at hand (Article 4: incremental, Principle 3)
- Reference `docs/ARCHITECTURE.md` for system design (Principle 8: read repo first)
- Link changes to explicit tasks in `agents/tasks/` (Article 5: traceability, Principle 25)
- Archive completed tasks to `agents/tasks/ARCHIVE.md` (Article 5)
- Update docs when code behavior changes (Principle 19: docs age with code)
- Update examples when code changes (Principle 20: examples are contracts)
