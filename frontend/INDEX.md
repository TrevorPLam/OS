# Frontend Directory Index

**File**: `frontend/INDEX.md`

This file catalogs the contents of the `frontend/` directory. See [root `INDEX.md`](../INDEX.md) for repository overview.

## Directory Structure

### Core Files
- `package.json` - NPM dependencies and scripts
- `package-lock.json` - Locked dependency versions
- `vite.config.ts` - Vite build configuration
- `tsconfig.json` - TypeScript configuration
- `tsconfig.node.json` - TypeScript config for Node tools
- `index.html` - Application entry HTML
- `Makefile` - Frontend build commands
- `playwright.config.ts` - E2E test configuration
- `lighthouserc.cjs` - Lighthouse CI configuration
- `.eslintrc.cjs` - ESLint configuration
- `AGENT.md` - Folder-level agent guide

### `src/` - Application Source

#### `src/api/` - API Client Functions
API client functions organized by domain (using TanStack React Query):
- `auth.ts` - Authentication API
- `clients.ts` - Client management API
- `crm.ts` - CRM API
- `documents.ts` - Document API
- `projects.ts` - Project API
- `dashboard.ts` - Dashboard API
- `calendar.ts` - Calendar API
- `automation.ts` - Automation API
- `assets.ts` - Assets API
- `clientPortal.ts` - Client portal API
- `timeTracking.ts` - Time tracking API
- `tasks.ts` - Task management API
- `tracking.ts` - Analytics tracking
- `client.ts` - Base API client

#### `src/components/` - Reusable Components
- `Layout.tsx` / `Layout.css` - Main layout component
- `ErrorBoundary.tsx` / `ErrorBoundary.css` - Error boundary component
- `CommandCenter.tsx` / `CommandCenter.css` - Command center UI
- `LoadingSpinner.tsx` / `LoadingSpinner.css` - Loading indicator
- `ImpersonationBanner.tsx` / `ImpersonationBanner.css` - Impersonation banner
- `ProtectedRoute.tsx` - Protected route wrapper

#### `src/contexts/` - React Contexts
- `AuthContext.tsx` - Authentication context
- `ImpersonationContext.tsx` - Impersonation context

#### `src/pages/` - Page Components
Page components with co-located CSS files (33 TSX files, 23 CSS files)

#### `src/tracking/` - Analytics Tracking
- `client.ts` - Tracking client
- `webVitals.ts` - Web vitals tracking
- `types.ts` - Tracking types
- `index.ts` - Tracking exports

#### `src/` - Core Application Files
- `App.tsx` / `App.css` - Main application component
- `main.tsx` - Application entry point
- `index.css` - Global styles
- `setupTests.ts` - Test setup
- `vite-env.d.ts` - Vite type definitions

### `e2e/` - End-to-End Tests
Playwright E2E tests:
- `auth.spec.ts` - Authentication flows
- `core-business-flows.spec.ts` - Core business flows
- `smoke.spec.ts` - Smoke tests
- `README.md` - E2E test documentation

### `tests/` - Unit Tests
Vitest unit tests (see individual test files)

## Navigation

- [Root `INDEX.md`](../INDEX.md) - Repository master index
- [`backend/INDEX.md`](../backend/INDEX.md) - Backend directory index
- [`tests/INDEX.md`](../tests/INDEX.md) - Tests directory index

## See Also

- `frontend/FRONTEND.md` - What agents may do in this directory
- [`.repo/policy/BESTPR.md`](../.repo/policy/BESTPR.md) - Frontend best practices
