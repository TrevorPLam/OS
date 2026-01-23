# BACKEND.md (Folder-Level Guide)

## Purpose of this folder

This folder (`backend/`) contains the Django backend application code. It includes domain modules, API endpoints, configuration, and core utilities.

## What agents may do here

- Create new modules in `backend/modules/` (within firm-scoping rules)
- Modify existing modules (within boundaries)
- Create/modify API endpoints in `backend/api/`
- Update configuration in `backend/config/` (with care for production impact)
- Add migrations when schema changes
- Follow Django patterns and Django REST Framework conventions

## What agents may NOT do

- Cross-module imports without ADR (see `.repo/policy/BOUNDARIES.md`)
- Break firm-scoping (all models must be firm-scoped)
- Import from `backend/modules/core/` and re-export across modules
- Modify migrations directly (use `makemigrations`)
- Break existing API contracts without ADR
- Add dependencies without security review

## Required links

- Refer to higher-level policy: `.repo/policy/BOUNDARIES.md` for import rules
- See `.repo/policy/BESTPR.md` for Django-specific best practices
- See `.repo/policy/SECURITY_BASELINE.md` for security requirements
- See `backend/modules/core/CORE.md` for platform layer rules

## Boundary Rules

- `backend/api/` may import from `backend/modules/`
- `backend/modules/` should not import from `backend/api/`
- `backend/modules/core/` is the platform layer - other modules may depend on it
- Cross-module imports require ADR (see Principle 23)
