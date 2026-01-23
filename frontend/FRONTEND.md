# FRONTEND.md (Folder-Level Guide)

## Purpose of this folder

This folder (`frontend/`) contains the React/TypeScript frontend application built with Vite. It includes components, pages, hooks, API clients, and E2E tests.

## What agents may do here

- Create new React components in `frontend/src/components/`
- Add new pages in `frontend/src/pages/`
- Create API client functions in `frontend/src/api/` (organized by domain)
- Add React hooks and contexts in `frontend/src/`
- Create E2E tests in `frontend/e2e/`
- Add unit tests in `frontend/tests/`
- Update Vite configuration when needed
- Add dependencies (with security review)

## What agents may NOT do

- Break existing component patterns without justification
- Create new abstractions before checking existing patterns in `frontend/src/components/`
- Use non-React Query patterns for API data fetching
- Break TypeScript types or skip type checking
- Modify build configuration without testing
- Add dependencies without security review
- Create components that don't follow React Hook Form patterns for forms

## Required links

- Refer to higher-level policy: `.repo/policy/BESTPR.md` for frontend-specific practices
- See `.repo/policy/PRINCIPLES.md` for operating principles
- See `.repo/policy/BOUNDARIES.md` for architectural boundaries
- See `backend/BACKEND.md` for backend API contract rules

## Frontend Standards

- Use functional components with TypeScript (`React.FC`)
- Use TanStack React Query for all API data fetching
- Keep API client functions in `frontend/src/api/` organized by domain
- Use React Hook Form for form handling
- Keep page components in `frontend/src/pages/` with co-located CSS
- Use React contexts (`frontend/src/contexts/`) for global state (auth, impersonation)
- Follow existing component patterns before introducing new abstractions
- All components must be properly typed with TypeScript

## Testing

- Unit tests: Use Vitest in `frontend/tests/`
- E2E tests: Use Playwright in `frontend/e2e/`
- Always add/update tests for new features
- Ensure `make -C frontend test` passes before submitting
