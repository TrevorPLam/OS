# BESTPR — UBOS Best Practices (Repo-Specific)

**File**: `.repo/policy/BESTPR.md`

## Purpose
Use this guide to ship changes that align with UBOS architecture, workflows, and quality bars. It captures the stack, repo layout, and the checks expected before delivery.

## Repository Map (where to work)
- **backend/modules/** — Domain modules with firm-scoped multi-tenancy (clients, crm, finance, projects, documents, etc.). Each module contains models, views, serializers, urls, and migrations.
- **backend/api/** — API endpoints organized by domain (clients, crm, finance, documents, projects, portal, webhooks).
- **backend/config/** — Django settings, middleware, health checks, permissions, and core configuration.
- **frontend/src/** — React application source (components, pages, hooks, contexts, API clients, tracking).
- **frontend/src/api/** — API client functions organized by domain, using TanStack React Query.
- **frontend/src/components/** — Reusable React components (Layout, ErrorBoundary, CommandCenter, etc.).
- **frontend/src/pages/** — Page components and their associated styles.
- **frontend/src/contexts/** — React contexts (AuthContext, ImpersonationContext).
- **tests/** — Cross-cutting and integration tests shared across modules.
- **docs/** — Primary documentation source tree (architecture, onboarding, development, runbooks).
- **agents/tasks/** — Task management (TODO.md, BACKLOG.md, ARCHIVE.md) for traceability.
- **scripts/** — Project automation and migration scripts.

## Tech Stack & Core Libraries
- **Backend:** Django 4.2 + Python 3.11, PostgreSQL 15, Django REST Framework for APIs.
- **Frontend:** React 18.3 + TypeScript 5.9 + Vite 5.4 for the client app.
- **State & Data Fetching:** TanStack React Query 5.90 for API data management.
- **Forms:** React Hook Form 7.69 for form handling.
- **Routing:** React Router DOM 6.30 for client-side navigation.
- **Data Visualization:** ReactFlow 11.10 for workflow/flow diagrams.
- **Testing:** pytest (backend), Vitest + Playwright (frontend), Testing Library for React components.
- **Formatting & Linting:** ruff + black + mypy (backend), ESLint + Prettier + tsc (frontend).
- **Observability:** Sentry for error tracking (backend and frontend).

## Delivery Workflow (what to run)
1. **Local checks before PR:**
   - `make lint` — Run all linters (backend + frontend)
   - `make typecheck` — Type checking (backend mypy, frontend tsc)
   - `make test` — Run test suites (pytest + vitest)
   - `make verify` — Full local CI suite (light checks by default)
   - `make verify SKIP_HEAVY=0` — Full suite including tests, build, and OpenAPI validation
2. **When touching APIs:** Regenerate and commit OpenAPI schema (`make -C backend openapi`).
3. **When touching docs:** Keep documentation in the organized `/docs` structure and update canonical root guides as needed.

## Repo-Specific Coding Practices
### Backend (Django)
- Prefer Django REST Framework viewsets for CRUD operations. Use `FirmScopedMixin` for all model viewsets to enforce multi-tenancy.
- Keep domain logic in `backend/modules/` with clear module boundaries. Each module should be self-contained (models, views, serializers, urls, migrations).
- Use serializers for request/response validation and transformation. Keep API-specific serializers in `backend/api/` when they differ from module serializers.
- Place shared utilities and middleware in `backend/config/` (permissions, pagination, throttling, health checks).
- Use type hints where practical (mypy is relaxed but preferred for new code).
- All models must be firm-scoped (inherit from FirmScopedMixin or use firm filtering).

Example:
```python
class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
```

### Frontend (React + TypeScript)
- Prefer existing component patterns in `frontend/src/components/` before introducing new abstractions.
- Use TanStack React Query for all API data fetching. Keep API client functions in `frontend/src/api/` organized by domain.
- Use React Hook Form for form handling with TypeScript types.
- Keep page components in `frontend/src/pages/` with co-located CSS files.
- Use React contexts (`frontend/src/contexts/`) for global state (auth, impersonation).
- Prefer functional components with TypeScript. Use React.FC for component type annotations.

Example:
```typescript
export const KnowledgeCenter: React.FC = () => {
  const { data } = useQuery({ queryKey: ['knowledge'] });
  return <div>...</div>;
};
```

### Shared / Cross-Cutting
- Keep integration and cross-module tests in `tests/` directory.
- Use OpenAPI schema (`backend/openapi.yaml`) as the contract between frontend and backend.
- Follow firm-scoped multi-tenancy patterns consistently across all modules.
- Reference `docs/ARCHITECTURE.md` for system design decisions.

## Documentation Expectations
- Follow the documentation structure in `/docs`:
  - `docs/ARCHITECTURE.md` — System architecture and design decisions
  - `docs/ONBOARDING.md` — Getting started guide
  - `docs/DEVELOPMENT.md` — Development workflow and commands
  - `docs/RUNBOOK.md` — Operational procedures
- Root-level guides like `README.md` and `AGENTS.md` should contain high-level navigation or onboarding details.
- When adding new modules or significant features, update relevant architecture documentation.

## Governance Alignment
- Follow the project governance rules in `.repo/policy/CONSTITUTION.md` for PR review, task traceability, verification evidence, and documentation rigor.
- Apply operating principles from `.repo/policy/PRINCIPLES.md` for day-to-day development practices.
- Quality gates in `.repo/policy/QUALITY_GATES.md` define merge requirements and verification checks.
- Security rules in `.repo/policy/SECURITY_BASELINE.md` define security checks, HITL triggers, and forbidden patterns.
- HITL process in `.repo/policy/HITL.md` defines how human-required actions are tracked and managed.
- Module boundaries in `.repo/policy/BOUNDARIES.md` define import rules and enforcement (Principle 13: Respect Boundaries).
- All changes must be traceable to tasks in `agents/tasks/` (Article 5: Strict Traceability, Principle 25).
- Completed tasks must be archived to `agents/tasks/ARCHIVE.md` after PR merge.
- For risky changes (logins, money flows, user data, security), route to HITL per Article 6 & 8, Principle 10, SECURITY_BASELINE.md triggers, and HITL.md process.
- PRs must include filepaths, verification evidence, and rollback plans per Principles 6, 12, and 17.
- All quality gates must pass before merge (hard gates) or have approved waivers (waiverable gates).
- Never commit secrets (SECURITY_BASELINE.md: absolute prohibition).

---
**Canonical reference:** This document is the single source of truth for repo-specific best practices. Link to it from all AGENTS.md files and governance docs.
