# Repository Structure Delta Analysis (DOC-17.1)

**Document Status:** Canonical
**Last Updated:** December 29, 2025
**Purpose:** Documents intentional differences between current repo structure and docs/17 blueprint

---

## Executive Summary

The current repository structure differs from the intended monorepo structure defined in docs/17. This document explains these differences, rationale for current organization, and migration path to the intended structure.

**Key Finding:** Current structure is a **monolithic Django application** with frontend embedded. Intended structure is a **true monorepo** with separated apps, domain packages, and engines.

---

## Current Structure

```
/home/user/OS/
├── docs/                    # Documentation (matches intended)
├── spec/                    # System specifications (not in docs/17)
├── scripts/                 # Utility scripts (not in docs/17)
├── src/                     # All application code (differs from intended)
│   ├── api/                 # API layer (DRF ViewSets, serializers)
│   ├── config/              # Django project settings
│   ├── frontend/            # React SPA (client portal + staff app)
│   ├── modules/             # Domain modules (Django apps)
│   │   ├── assets/
│   │   ├── auth/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── crm/
│   │   ├── documents/
│   │   ├── finance/
│   │   ├── firm/
│   │   └── projects/
│   └── logs/
└── tests/                   # Test suite (top-level, not per-package)
    ├── firm/
    ├── projects/
    ├── safety/
    └── ...
```

---

## Intended Structure (per docs/17)

```
/
├── apps/                    # Application layer
│   ├── staff/               # Staff App UI
│   ├── portal/              # Client Portal UI
│   └── api/                 # API service
├── packages/                # Domain packages (bounded contexts)
│   ├── domain-core/         # Entities, state machines (no DB/network)
│   ├── permissions/         # Authorization evaluator
│   ├── pricing-engine/      # Pricing calculations
│   ├── recurrence-engine/   # Recurrence logic
│   ├── orchestration-engine/# Workflow orchestration
│   ├── delivery-templates/  # Template instantiation
│   ├── documents/           # Document management
│   ├── integrations/        # Email/calendar sync
│   ├── billing-ledger/      # Immutable ledger
│   └── shared/              # Types, utilities
├── infrastructure/          # Deployment/ops
│   ├── db/                  # Migrations, provisioning
│   ├── queues/              # Worker configs
│   └── deploy/              # Environment templates
└── docs/                    # Documentation
```

---

## Delta Analysis

### 1. Top-Level Organization

| Aspect | Current | Intended | Delta |
|--------|---------|----------|-------|
| Root structure | `src/`, `tests/`, `docs/`, `spec/`, `scripts/` | `apps/`, `packages/`, `infrastructure/`, `docs/` | Different organization philosophy |
| Application code | All in `src/` | Split into `apps/` and `packages/` | Monolith vs monorepo |
| Frontend location | `src/frontend/` (single SPA) | `apps/staff/` + `apps/portal/` (separate apps) | Staff + Portal bundled together |

### 2. Domain Organization

| Aspect | Current | Intended | Rationale for Current |
|--------|---------|----------|----------------------|
| Domain code | Django modules in `src/modules/` | Pure domain-core in `packages/domain-core/` | Django ORM tightly coupled |
| Engines | Mixed into modules (e.g., pricing in `finance`) | Separate packages (pricing-engine, recurrence-engine) | Not yet extracted |
| Permissions | Mixed in ViewSets + decorators | Dedicated `packages/permissions/` | Authorization scattered |
| Documents | `src/modules/documents/` (Django app) | `packages/documents/` (pure service) | Django File/Storage dependency |

### 3. Boundary Violations (per docs/17 rules)

**Rule:** domain-core MUST NOT depend on DB/ORM/network/UI

| Current Situation | Violation | Impact |
|-------------------|-----------|--------|
| Models in `src/modules/` use Django ORM directly | ✅ YES | Domain logic coupled to Django; hard to test in isolation |
| Business logic in model methods (e.g., `Contract.clean()`) | ⚠️ PARTIAL | Logic is co-located with persistence; violates clean architecture |
| Permissions checks in ViewSets | ⚠️ PARTIAL | Permission logic not reusable outside API layer |

### 4. Infrastructure

| Aspect | Current | Intended | Status |
|--------|---------|----------|--------|
| Database migrations | `src/modules/*/migrations/` | `infrastructure/db/migrations/` | Scattered across Django apps |
| Worker configs | Not visible in structure scan | `infrastructure/queues/` | May exist in deployment configs |
| Deployment | Not visible in structure scan | `infrastructure/deploy/` | May exist outside repo |

### 5. Test Organization

| Aspect | Current | Intended | Rationale |
|--------|---------|----------|-----------|
| Test location | Top-level `tests/` directory | Co-located with packages | Django convention (top-level tests) |
| Test structure | Organized by module (`tests/firm/`, `tests/projects/`) | Package-level test suites | Follows Django patterns |

---

## Intentional Differences (Rationale)

### Why Current Structure Exists

1. **Django Conventions**
   - Django projects traditionally use a monolithic `src/` or project root
   - Apps are Django modules with models/views/admin co-located
   - Migrations are managed by Django's migration framework per-app

2. **Development Velocity**
   - Monolithic structure allows faster iteration early on
   - Less boilerplate for small teams
   - Easier to refactor within single codebase

3. **Frontend Bundling**
   - Staff app and client portal share components (e.g., form libraries)
   - Single build pipeline reduces complexity
   - Route-based code splitting handles separation

4. **ORM Lock-in (Accepted Tradeoff)**
   - Django ORM provides rich querying, migrations, admin
   - Moving to pure domain-core requires repository pattern
   - Current team expertise is Django-native

### When Differences Become Problems

1. **Engine Reusability**: Pricing/recurrence logic can't be called outside Django context
2. **Testing**: Can't test business logic without database
3. **Multi-Team Development**: No clear package boundaries for ownership
4. **Service Extraction**: Can't extract engines as separate services without refactoring

---

## Migration Path to Intended Structure

### Phase 1: Domain Extraction (Preserve Django)
**Goal:** Extract pure business logic while keeping Django

1. Create `packages/domain-core/` with entities (dataclasses/Pydantic)
2. Keep Django models as persistence adapters
3. Move validation logic from model methods to domain-core

**Effort:** 4-6 weeks
**Risk:** Medium (requires careful refactoring)

### Phase 2: Engine Separation
**Goal:** Extract engines as callable services

1. Create `packages/pricing-engine/` with pure functions
2. Create `packages/recurrence-engine/` with deterministic logic
3. Django models become callers of engines

**Effort:** 6-8 weeks
**Risk:** Medium-High (complex domain logic)

### Phase 3: Frontend Split
**Goal:** Separate staff and portal apps

1. Create `apps/staff/` with staff-specific UI
2. Create `apps/portal/` with client-specific UI
3. Extract shared components to `packages/ui-shared/`

**Effort:** 4-6 weeks
**Risk:** Low-Medium (mostly code organization)

### Phase 4: Infrastructure Consolidation
**Goal:** Centralize ops/deployment

1. Create `infrastructure/db/` with migration tooling
2. Create `infrastructure/queues/` with worker configs
3. Create `infrastructure/deploy/` with environment templates

**Effort:** 2-4 weeks
**Risk:** Low (mostly moving files)

---

## Boundary Enforcement Strategy

### Immediate (No Refactoring Required)

1. **Linting Rules**: Add import-linter to prevent:
   - `src/modules/core/` importing from specific modules
   - Cross-module imports violating dependency graph

2. **Documentation**: Update CONTRIBUTING.md with current boundaries:
   - API layer owns ViewSets/serializers
   - Modules own models/business logic
   - Frontend owns UI components

### Medium-Term (Gradual Refactoring)

1. **Repository Pattern**: Introduce repositories for complex queries
2. **Service Layer**: Extract multi-model operations to services
3. **Domain Events**: Use signals/events instead of direct coupling

### Long-Term (Monorepo Migration)

Follow migration path above when:
- Team grows beyond 5-7 engineers
- Multiple teams need clear ownership boundaries
- Services need to be extracted for scalability

---

## Decision: Current Structure is Intentional

**Status:** Current structure is **intentionally different** from docs/17 blueprint.

**Reasoning:**
1. Django monolith is appropriate for current team size (1-3 engineers)
2. Refactoring to monorepo requires 4-6 months (Phases 1-4)
3. Business value of monorepo (multi-team ownership, service extraction) not yet needed
4. docs/17 remains aspirational blueprint for future scaling

**Action Required:**
- Keep docs/17 as long-term vision
- Update docs/17 with "Current vs Intended" section pointing to this document
- Revisit when team reaches 5+ engineers or service extraction is required

---

## Appendix: Dependency Map (Current)

```
API Layer (src/api/)
  ↓ depends on
Modules (src/modules/)
  ├── core/ (base models, utils) ← other modules depend on this
  ├── firm/ (tenancy) ← all modules depend on this
  ├── auth/ (users)
  ├── clients/
  ├── crm/
  ├── projects/
  ├── finance/
  ├── documents/
  └── assets/

Frontend (src/frontend/)
  ↓ calls (HTTP)
API Layer
```

**Violations of docs/17:**
- No clear domain-core (business logic in models)
- No engine separation (pricing in finance module)
- UI apps not separated (staff + portal bundled)

---

## References

- **docs/17**: Intended monorepo structure blueprint
- **spec/SYSTEM_SPEC.md**: System invariants (takes precedence over structure)
- **CONTRIBUTING.md**: Current development guidelines

---

**Next Actions:**
1. Add import-linter config to enforce current boundaries
2. Update CONTRIBUTING.md with module dependency rules
3. Create ADR for "Monolith-First, Monorepo-Later" decision
4. Schedule architecture review when team reaches 5 engineers
