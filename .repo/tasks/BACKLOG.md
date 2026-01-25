# 📋 Task Backlog

> **Prioritized Queue** — All open tasks ordered by priority (P0 highest → P3 lowest).

---

## Workflow Instructions

### Adding New Tasks:
1. Use the standard task format (see template below)
2. Assign appropriate priority: P0 (Critical) | P1 (High) | P2 (Medium) | P3 (Low)
3. Insert task in correct priority order (P0 tasks at top)
4. Include clear acceptance criteria

### Promoting Tasks:
1. When `TODO.md` is empty, move the TOP task from this file to `TODO.md`
2. Update status from `Pending` to `In Progress`
3. Remove the task from this file

### Task Format Template:
```markdown
### [TASK-XXX] Task Title
- **Priority:** P0 | P1 | P2 | P3
- **Status:** Pending
- **Created:** YYYY-MM-DD
- **Context:** Brief description of why this task matters

#### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

#### Notes
- Any relevant context or links
```

---

## Priority Legend
| Priority | Meaning | SLA |
|----------|---------|-----|
| **P0** | Critical / Blocking | Immediate |
| **P1** | High / Important | This week |
| **P2** | Medium / Should do | This month |
| **P3** | Low / Nice to have | When possible |

---

## P0 — Critical

## P1 — High

### [TASK-016] Implement React Hook Form in All Forms
- **Priority:** P1
- **Status:** Blocked
- **Created:** 2026-01-23
- **Blocked By:** HITL-0001 (security review for login/register form changes)
- **Context:** Per ANALYSIS.md Section 1.3, React Hook Form is installed but ZERO usage found. All 15+ forms use manual useState, causing code duplication (~300-450 lines) and missing validation.

#### Acceptance Criteria
- [ ] Implement React Hook Form in `frontend/src/pages/Login.tsx`
- [ ] Implement React Hook Form in `frontend/src/pages/Register.tsx`
- [ ] Implement React Hook Form in `frontend/src/pages/Clients.tsx`
- [ ] Implement React Hook Form in `frontend/src/pages/crm/Deals.tsx`
- [ ] Implement React Hook Form in all remaining forms (10+ pages)
- [ ] Add proper validation rules to all forms
- [ ] Remove manual form state management (useState patterns)
- [ ] Verify all forms work correctly

#### Notes
- Per ANALYSIS.md Section 0.10, 1.3: 0% usage, 15+ forms need conversion
- Would eliminate ~300-450 lines of duplicate code
- Estimated: 12-16 hours for all forms
- Files: All page components with forms
- Blocked on HITL-0001 (security review for login/register form changes)

---

## P2 — Medium

### [TASK-021] Increase Frontend Test Coverage to 60%
- **Priority:** P2
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 1.4, 11.9, test coverage is <15% but vite.config.ts sets 60% thresholds. Only 8 test files exist for ~96 source files.

#### Acceptance Criteria
- [ ] Add tests for all API functions in `frontend/src/api/` (currently 0% coverage)
- [ ] Add tests for all page components (currently <15% coverage)
- [ ] Add tests for React Query hooks
- [ ] Add integration tests for data fetching flows
- [ ] Achieve 60%+ coverage (lines, functions, branches, statements)
- [ ] Add coverage reporting to CI
- [ ] Update coverage thresholds in vite.config.ts if needed

#### Notes
- Per ANALYSIS.md Section 1.4: 8 test files for 96 source files
- Per Section 11.9: API layer 0% coverage, pages <15%
- Critical paths not tested: Client CRUD, Deal pipeline, Proposal workflow
- Estimated: 20-30 hours
- Files: New test files in `frontend/src/**/__tests__/`

---

### [TASK-022] Refactor Remaining Pages to Use React Query Hooks
- **Priority:** P2
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 0, remaining page components (Projects, Documents, Contracts, etc.) still use anti-pattern. Complete the migration started in TASK-015 and TASK-017.

#### Acceptance Criteria
- [ ] Refactor all remaining page components to use React Query hooks
- [ ] Remove all `useState` + `useEffect` + direct API call patterns
- [ ] Implement proper error handling with ErrorDisplay component
- [ ] Verify all pages work correctly
- [ ] Update any remaining API files to export hooks

#### Notes
- Per ANALYSIS.md: Only 2/17 pages use React Query correctly (12% adherence)
- Depends on TASK-013, TASK-014 (API hooks must exist first)
- Estimated: 12-16 hours
- Files: All remaining `frontend/src/pages/*.tsx` files

---

### [TASK-023] Standardize Error Handling Across Application
- **Priority:** P2
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 11.2, error handling is inconsistent with 88 different approaches. ErrorBoundary exists but only catches render errors, not async errors.

#### Acceptance Criteria
- [ ] Create error handling pattern documentation
- [ ] Implement error states in all React Query hooks
- [ ] Add toast notifications for mutations
- [ ] Enhance ErrorBoundary to handle async errors
- [ ] Replace all `console.error` with proper error handling (88 instances)
- [ ] Add error logging to Sentry where appropriate
- [ ] Verify error handling works in production scenarios

#### Notes
- Per ANALYSIS.md Section 11.2: 88 console.error calls, inconsistent patterns
- Depends on TASK-019 (ErrorDisplay component)
- Estimated: 8-10 hours
- Files: All page components, API hooks, ErrorBoundary

---

### [TASK-008] Enable OpenAPI Drift Detection in CI
- **Priority:** P2
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** OpenAPI check job is disabled (`if: false`) in CI workflow.

#### Acceptance Criteria
- [ ] Fix blocking issues preventing OpenAPI generation
- [ ] Enable the `openapi-check` job
- [ ] Ensure schema drift fails CI
- [ ] Document OpenAPI workflow in CONTRIBUTING.md

#### Notes
- Committed OpenAPI artifact is single source of truth for API

---

### [TASK-009] Add Worker Runtime for Job Queue
- **Priority:** P2
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Job queue models exist but no worker process to execute them.

#### Acceptance Criteria
- [ ] Create management command or worker process
- [ ] Add worker service to docker-compose.yml
- [ ] Document worker scaling strategy
- [ ] Add health checks for worker

#### Notes
- Per ANALYSIS.md: jobs modeled in DB but can't run
- backend/modules/jobs/models.py defines JobQueue/DLQ

---

## P3 — Low

### [TASK-024] Optimize Bundle Size and Performance
- **Priority:** P3
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 11.7, react-hook-form (15KB) is unused, reactflow (200KB) should be code-split. Per Section 11.11, missing memoization and potential re-render issues.

#### Acceptance Criteria
- [ ] Implement code splitting for WorkflowBuilder (lazy load reactflow)
- [ ] Add React.lazy() for large page components
- [ ] Add useMemo() for expensive calculations (e.g., Deals.tsx calculateMetrics)
- [ ] Remove or use react-hook-form (currently unused, wasting 15KB)
- [ ] Run bundle analysis and document findings
- [ ] Verify performance improvements with Lighthouse

#### Notes
- Per ANALYSIS.md Section 11.7: Bundle size optimizations needed
- Per Section 11.11: Performance bottlenecks identified
- Estimated: 4-6 hours
- Files: `frontend/src/pages/WorkflowBuilder.tsx`, `frontend/src/pages/crm/Deals.tsx`, etc.

---

### [TASK-025] Improve Accessibility (A11y)
- **Priority:** P3
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 11.10, accessibility needs verification. Native window.confirm dialogs have poor accessibility, ARIA attributes need audit.

#### Acceptance Criteria
- [ ] Run Lighthouse accessibility audit
- [ ] Add ARIA labels to all custom components
- [ ] Verify keyboard navigation works on all interactive elements
- [ ] Test with screen readers
- [ ] Add ARIA live regions for dynamic content
- [ ] Verify WCAG compliance (color contrast, etc.)
- [ ] Document accessibility patterns

#### Notes
- Per ANALYSIS.md Section 11.10: Accessibility needs verification
- Depends on TASK-019 (ConfirmDialog component)
- Estimated: 6-8 hours
- Files: All components, especially custom dialogs

---

### [TASK-026] Document API Contracts (OpenAPI/Swagger)
- **Priority:** P3
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 5.1, no API contract documentation found. Frontend-backend alignment would benefit from OpenAPI spec.

#### Acceptance Criteria
- [ ] Generate OpenAPI/Swagger spec from backend
- [ ] Document all API endpoints used by frontend
- [ ] Add request/response schemas
- [ ] Include authentication requirements
- [ ] Add examples for each endpoint
- [ ] Host spec in accessible location
- [ ] Update frontend API clients to reference spec

#### Notes
- Per ANALYSIS.md Section 5.1: No API contract documentation
- Would improve frontend-backend alignment
- Estimated: 8-10 hours
- Files: New OpenAPI spec file, update API client docs

---

### [TASK-030] Implement Learning from Failures System
- **Priority:** P2
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md, system lacks ability to learn from failures. Should analyze logs and suggest improvements.

#### Acceptance Criteria
- [ ] Create `scripts/analyze-failures.js` or Python equivalent
- [ ] Analyze trace logs and agent logs for failure patterns
- [ ] Generate improvement suggestions
- [ ] Add failure categorization
- [ ] Document failure analysis in CONTRIBUTING.md

#### Notes
- Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md Section 288: High impact, high effort
- Impact: High - enables self-improvement
- Estimated: 8-12 hours

---

### [TASK-031] Add Self-Healing Capabilities
- **Priority:** P2
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md, system lacks self-healing. Should add retry logic, failure analysis, and task decomposition.

#### Acceptance Criteria
- [ ] Add retry logic for failed operations
- [ ] Implement failure analysis and categorization
- [ ] Add automatic task decomposition for complex failures
- [ ] Create self-healing workflow documentation
- [ ] Add monitoring for self-healing actions

#### Notes
- Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md Section 293: High impact, high effort
- Impact: High - improves resilience
- Estimated: 12-16 hours

---

### [TASK-032] Create Monitoring Dashboard for Agent Metrics
- **Priority:** P3
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md, system tracks metrics but lacks dashboard visualization.

#### Acceptance Criteria
- [ ] Create dashboard for agent metrics (HTML or web-based)
- [ ] Display task completion rates
- [ ] Show error rates and patterns
- [ ] Visualize trace log data
- [ ] Add real-time updates capability

#### Notes
- Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md Section 300: Low impact, medium effort
- Impact: Low - nice to have
- Estimated: 6-8 hours

---

### [TASK-033] Add Trend Analysis for Metrics
- **Priority:** P3
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md, system tracks metrics but doesn't analyze trends or detect regressions.

#### Acceptance Criteria
- [ ] Add time-series analysis for metrics
- [ ] Detect regressions in task completion rates
- [ ] Track error rate trends
- [ ] Generate trend reports
- [ ] Add alerts for significant regressions

#### Notes
- Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md Section 305: Low impact, medium effort
- Impact: Low - nice to have
- Estimated: 6-8 hours

---

### [TASK-010] Add Observability Stack (OpenTelemetry/Prometheus)
- **Priority:** P3
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Logging and Sentry exist but no metrics/tracing.

#### Acceptance Criteria
- [ ] Add OpenTelemetry instrumentation
- [ ] Configure Prometheus metrics endpoint
- [ ] Create basic Grafana dashboards-as-code
- [ ] Document observability in RUNBOOK.md

#### Notes
- Per ANALYSIS.md: observability incomplete

---

### [TASK-011] Add SBOM Generation to CI
- **Priority:** P3
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Supply chain security best practice.

#### Acceptance Criteria
- [ ] Add SBOM generation step to CI
- [ ] Choose format (SPDX or CycloneDX)
- [ ] Store SBOM artifact with releases
- [ ] Document in SECURITY.md

#### Notes
- Required for enterprise security compliance
