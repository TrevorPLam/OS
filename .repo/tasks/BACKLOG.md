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

### [TASK-002] Create .env.example File
- **Priority:** P0
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** Code references `.env.example` but file doesn't exist. Blocks new environment setup.

#### Acceptance Criteria
- [ ] Document all required environment variables from `env_validator.py`
- [ ] Include comments explaining each variable
- [ ] Add placeholder values (never real secrets)
- [ ] Reference in README.md and docs/getting-started/onboarding.md

#### Notes
- Required vars: DJANGO_SECRET_KEY, POSTGRES_*, AWS_*, STRIPE_*, etc.
- Production vars differ from development vars

---

### [TASK-003] Fix Duplicate Content in CI Workflow
- **Priority:** P0
- **Status:** Pending
- **Created:** 2026-01-23
- **Context:** `.github/workflows/ci.yml` has two conflicting workflow definitions causing confusion.

#### Acceptance Criteria
- [ ] Remove duplicate workflow definition
- [ ] Ensure single coherent CI pipeline
- [ ] Verify all jobs run correctly
- [ ] Test on a branch before merging

#### Notes
- File currently has 403 lines with overlapping `name: CI` and `name: CI/CD Pipeline`

---

## P1 — High

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
