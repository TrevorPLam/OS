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

### [TASK-017] Refactor CRM Pages to Use React Query Hooks
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 0.4, all CRM pages use anti-pattern. Deals.tsx has 10+ direct API calls and 7 useState hooks. This is the most complex refactoring.

#### Acceptance Criteria
- [ ] Refactor `frontend/src/pages/crm/Deals.tsx` to use React Query hooks
- [ ] Refactor `frontend/src/pages/crm/Prospects.tsx` to use React Query hooks
- [ ] Refactor `frontend/src/pages/crm/PipelineKanban.tsx` to use React Query hooks
- [ ] Refactor `frontend/src/pages/crm/PipelineAnalytics.tsx` to use React Query hooks
- [ ] Refactor `frontend/src/pages/crm/Leads.tsx` to use React Query hooks
- [ ] Remove all manual state management and direct API calls
- [ ] Implement proper error handling

#### Notes
- Per ANALYSIS.md Section 0.4: Deals.tsx is 482 lines, most complex
- Depends on TASK-014 (CRM API hooks)
- Estimated: 10-12 hours for all CRM pages
- Files: All `frontend/src/pages/crm/*.tsx` files

---

### [TASK-018] Re-enable ESLint Rules and Fix Violations
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 0.8, 4 critical ESLint rules are disabled, compromising type safety and code quality. Per Section 11.4, 57 instances of `any` type exist.

#### Acceptance Criteria
- [ ] Re-enable `@typescript-eslint/no-explicit-any` (start with "warn")
- [ ] Re-enable `@typescript-eslint/no-unused-vars` (start with "warn")
- [ ] Re-enable `react-hooks/exhaustive-deps` (start with "warn")
- [ ] Fix all violations across codebase (57 `any` types, unused vars, etc.)
- [ ] Gradually increase rules to "error" level
- [ ] Verify `make -C frontend lint` passes

#### Notes
- Per ANALYSIS.md Section 0.8: Lines 35-38 need rule re-enabling
- Per Section 11.4: 57 `any` types need replacement
- Estimated: 8-10 hours to fix all violations
- File: `frontend/.eslintrc.cjs` + all source files

---

### [TASK-019] Create Shared Error and Loading Components
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 11.2, 88 console.error calls exist with 0 user-facing error components. Per Section 11.12, loading states are duplicated in 20+ files.

#### Acceptance Criteria
- [ ] Create `frontend/src/components/ErrorDisplay.tsx` component
- [ ] Create `frontend/src/components/ConfirmDialog.tsx` component (replace window.confirm)
- [ ] Enhance `frontend/src/components/LoadingSpinner.tsx` if needed
- [ ] Replace all `console.error` calls with ErrorDisplay component (88 instances)
- [ ] Replace all `window.confirm` calls with ConfirmDialog (19 instances)
- [ ] Replace manual loading states with shared component
- [ ] Add proper accessibility (ARIA labels, keyboard navigation)

#### Notes
- Per ANALYSIS.md Section 11.2: 88 console.error, 0 error components
- Per Section 11.5: 19 window.confirm calls need replacement
- Per Section 11.12: ~800-1000 lines of duplicate code
- Estimated: 6-8 hours
- Files: New components + all page components

---

### [TASK-020] Fix Vite Build Configuration Mismatch
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 0.9, vite.config.ts uses `outDir: 'build'` but Makefile checks for `dist` directory. This breaks build verification.

#### Acceptance Criteria
- [ ] Change `frontend/vite.config.ts` line 18: `outDir: 'build'` to `outDir: 'dist'` OR
- [ ] Update `frontend/Makefile` line 33 to check for `build` directory
- [ ] Verify `make -C frontend build-check` passes
- [ ] Update any CI/CD scripts that reference build directory
- [ ] Document the decision

#### Notes
- Per ANALYSIS.md Section 0.9: Build directory mismatch
- Quick fix - estimated 15 minutes
- Files: `frontend/vite.config.ts`, `frontend/Makefile`

---

### [TASK-004] Create .github/copilot-instructions.md
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Context engineering file for GitHub Copilot and VS Code AI features.

#### Acceptance Criteria
- [ ] Document product vision and architecture principles
- [ ] Include contribution guidelines for AI
- [ ] Reference supporting docs (ARCHITECTURE.md, PRODUCT.md)
- [ ] Test with Copilot to verify context is picked up

#### Notes
- Part of the VS Code context engineering workflow standard

---

### [TASK-005] Create PRODUCT.md
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Product vision document giving AI context about WHY features exist.

#### Acceptance Criteria
- [ ] Define UBOS product vision and mission
- [ ] Document target users (service firms)
- [ ] List key features and their business value
- [ ] Include product roadmap priorities

#### Notes
- AI agents need product context to make good decisions

---

### [TASK-006] Expand docs/ARCHITECTURE.md
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Current file is 14 lines. Needs comprehensive system documentation.

#### Acceptance Criteria
- [ ] Add Mermaid diagrams for system architecture
- [ ] Document module ownership and boundaries
- [ ] Explain data flow and integration patterns
- [ ] Include decision rationale for key choices

#### Notes
- Critical for AI to understand system structure

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

### [TASK-007] Create docs/adr/ Folder with ADR Template
- **Priority:** P2
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Architecture Decision Records document WHY decisions were made.

#### Acceptance Criteria
- [ ] Create `docs/adr/` directory
- [ ] Add ADR template (ADR-000-template.md)
- [ ] Create first ADR for multi-tenancy model
- [ ] Document ADR process in docs/architecture/decisions/

#### Notes
- ADRs help AI understand historical context

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

### [TASK-028] Add Automatic Task Lifecycle Triggering to CI
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md, archive-task.py and promote-task.sh exist but require manual execution. Should be auto-triggered in CI.

#### Acceptance Criteria
- [ ] Add GitHub Actions workflow to trigger archive-task.py on task completion
- [ ] Add webhook or scheduled job to auto-promote tasks
- [ ] Ensure task lifecycle runs automatically after PR merge
- [ ] Add error handling and notifications for lifecycle failures
- [ ] Document auto-triggering in CONTRIBUTING.md

#### Notes
- Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md Section 283: High priority enhancement
- Scripts exist: `scripts/archive-task.py`, `scripts/promote-task.sh`
- Impact: Medium - improves automation
- Files: `.github/workflows/`, `scripts/archive-task.py`

---

### [TASK-029] Verify Agent Logger Integration
- **Priority:** P1
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md, need to verify if agents actually call agent-logger.js. Logging SDK exists but usage may not be integrated.

#### Acceptance Criteria
- [ ] Audit codebase for agent-logger.js usage
- [ ] Verify agents call logging SDK in workflow
- [ ] Add integration hooks if missing
- [ ] Add logging examples to AGENTS.md
- [ ] Document logging patterns in QUICK_REFERENCE.md

#### Notes
- Per AGENTIC_SYSTEM_ASSESSMENT_REVISED.md Section 271: Medium impact
- File: Check for `agent-logger.js` or logging SDK usage
- Impact: Medium - ensures proper logging

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
