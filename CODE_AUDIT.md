# CODE_AUDIT.md — Code Audit Pipeline

Document Type: Governance
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Canonical
Dependencies: CODEBASECONSTITUTION.md, TODO.md, DOCS_ROOT.md

## Purpose

This document defines the code audit pipeline for the repository. It establishes what must be checked, when, and how violations are handled.

## Audit Pipeline

### Pre-Commit Checks

All changes must pass:

1. **Linting** - Code style and formatting
   - Tool: `make lint` (ruff + black)
   - Auto-fix: `make format`
   - No exceptions without explicit justification

2. **Type Checking** (if applicable)
   - Tool: mypy or equivalent
   - Enforcement level: defined in pyproject.toml

3. **Security Scanning** 
   - Dependency vulnerabilities
   - Code security patterns
   - Secrets detection

### Pre-Merge Checks

All PRs must pass:

1. **Tests**
   - Command: `make test`
   - Coverage requirements: as defined in CI
   - All tests must pass

2. **Build Verification**
   - Docker build must succeed
   - No build warnings on critical paths

3. **Documentation Validation**
   - Links must resolve
   - API specs must match implementation
   - OpenAPI schema must be current

4. **Security Gates**
   - No hardcoded secrets
   - RLS policies on tenant-scoped models
   - Permission checks on endpoints
   - Input validation and sanitization

### Post-Merge Audits

Periodic reviews:

1. **Dependency Health**
   - Outdated dependencies
   - Security advisories
   - License compliance

2. **Documentation Drift**
   - Docs match implementation
   - No orphaned docs
   - No task leakage in docs

3. **Architectural Compliance**
   - No boundary violations
   - Module organization consistent
   - No circular dependencies

## Audit Execution

### Manual Audits

When to run:
- Before major releases
- After significant refactoring
- When requested via TODO task

How to run:
1. Review CODEBASECONSTITUTION.md for current rules
2. Run all automated checks
3. Review architectural boundaries
4. Check documentation accuracy
5. Document findings in TODO.md

### Automated Audits

Continuous:
- CI/CD pipeline on every PR
- Dependency scanning (daily/weekly)
- Security scanning (on commit)

## Violation Handling

### Severity Levels

1. **Critical** - Security vulnerability, data loss risk
   - Action: Block merge, immediate fix required
   - Escalation: Document in SECURITY.md format

2. **High** - Constitutional violation, broken build
   - Action: Block merge, fix required before merge
   - Escalation: Required for merge approval

3. **Medium** - Style violation, missing tests
   - Action: Fix in PR or create follow-up task
   - Grace: Can merge with justified exception

4. **Low** - Documentation gap, minor style inconsistency
   - Action: Create TODO task for cleanup
   - Grace: Does not block merge

### Exception Process

If audit fails but merge is necessary:

1. Document exception in PR description
2. Include:
   - Reason for exception
   - Impact assessment
   - Remediation plan with date
3. Link to TODO task for remediation
4. Require additional approval

## Integration with TODO.md

All audit findings must be tracked:

- Critical/High: Create task immediately with T-### ID
- Medium: Create task in next sprint
- Low: Batch into cleanup task

Format in TODO:
```
## T-XXX: [Audit] Description
- Type: Code Audit Finding
- Severity: Critical/High/Medium/Low
- Source: [Audit Type] on [Date]
- Context: Link to PR/commit/file
- Acceptance: [Specific fix criteria]
```

## Audit Schedule

- **Daily**: CI checks on all commits/PRs
- **Weekly**: Dependency vulnerability scan
- **Monthly**: Documentation drift review
- **Quarterly**: Full architectural compliance audit
- **Release**: Complete pre-release audit

## References

- CI Pipeline: `.github/workflows/ci.yml`
- Linting Config: `pyproject.toml`
- Test Config: `pytest.ini`
- Security Baseline: `docs/SECURITY_BASELINE.md`
- Constitution: `CODEBASECONSTITUTION.md`

## Version History

- 1.0.0 (2026-01-03): Initial version defining audit pipeline
# CODE AUDIT

Precedence: CODEBASECONSTITUTION.md → READMEAI.md → specs/* → this document.

Purpose: produce a trustworthy, prioritized TODO.md and TODO_COMPLETED.md by running a phased audit:

1. Task Hygiene (consolidate tasks from docs/code/config)
2. Spec Completeness (requirements → implementation coverage)
3. Code Quality (maintainability + consistency)
4. Dead Code (safe removal candidates + validation plan)
5. Enhancements (small, measurable improvements)

⠀
Primary outputs (must be produced/updated):

* TODO.md (execution backlog)
* TODO_COMPLETED.md (dated archive)

Secondary outputs (optional, only if needed):

* Updates to specs/project-tasks.md if specs are your task truth source
* Updates to DECISIONS.md / CHANGELOG.md if audit changes behavior or policy

Hard rule: Do not mix phases. Complete Phase 1 before Phase 2, etc.

---

## AGENT EXECUTION PROMPT (RUN THIS EXACTLY)

You are an implementation agent operating inside this repository.

Your job is to execute CODE AUDIT by phases and update files in-place.

You must:

* Start by reading READMEAI.md and CODEBASECONSTITUTION.md.
* Follow this document exactly.
* Avoid adding new feature scope. This is an audit + backlog hygiene task.
* Produce concrete tasks only (no vague refactors).
* Use file references and acceptance criteria for every task.
* Remove “task leakage” by moving actionable items out of docs and code comments into TODO.md (or replacing them with task IDs).

If you cannot run commands, still proceed by static analysis and file inspection.

Deliverables:

1. Update TODO.md and TODO_COMPLETED.md.
2. Remove or replace actionable TODO/FIXME/TBD markers in docs/code with references to T-### tasks in TODO.md.
3. Ensure TODO.md is deduped and prioritized, and that the top 5 tasks are immediately actionable.

⠀
Stop conditions:

* If a doc/code note contains important context, do not delete context. Replace only the actionable part and add a T-### pointer.
---

## Task Format Standard (REQUIRED)

Every task in TODO.md must follow this template:

* ID: T-###
* Priority: P0 / P1 / P2
* Type: HYGIENE / COMPLETE / QUALITY / DEADCODE / ENHANCE
* Title: imperative, specific
* Context: why this matters (1–2 sentences)
* Acceptance Criteria:

  * bullet list of verifiable outcomes
* References:

  * file paths and/or spec/doc sections
* Dependencies: optional
* Effort: S / M / L

Rules:

* Split any task > 1 day into smaller tasks.
* Cap Enhancements created in Phase 5 at 20 tasks.
* Any “refactor” task must state the exact measurable/observable outcome.
---

## Phase 0 — Setup (must be done first)

1. Read:

⠀
* READMEAI.md
* CODEBASECONSTITUTION.md
* specs/project-spec.md
* specs/project-tasks.md (if present)
* specs/technical-plan.md (if present)

1. Determine task truth source:

⠀
* If specs/project-tasks.md is source-of-truth: update that first, then sync TODO.md.
* Otherwise: TODO.md is source-of-truth.

Record one sentence at the top of TODO.md:

“Task truth source: (specs/project-tasks.md | TODO.md)”

Gate:

* You can state where task truth lives and how tasks should be updated.
---

## Phase 1 — UPDATE TODO (Task Hygiene)

Goal: no executable tasks remain stranded in docs/code/config; completed tasks are moved; TODO is clean.

Step 1 — Move completed tasks

* Scan TODO.md.
* Move completed tasks into TODO_COMPLETED.md with:

  * completion date (YYYY-MM-DD)
  * one-line result
  * references (files/PR/commit) if available

Step 2 — Sweep docs for tasks

Search /docs/** for:

* TODO, FIXME, HACK, TBD, TKTK, OPEN QUESTION, UNDECIDED, REVISIT, “follow up”, “later”, “missing”

* For each actionable item:
* Create/merge a task in TODO.md (format required)
* Remove the actionable line from the doc OR replace it with: “Tracked in TODO: T-###”

Step 3 — Sweep code for tasks

Search codebase for:

* TODO:, FIXME:, HACK:, XXX:, @todo, TKTK, OPEN QUESTION, UNDECIDED, REVISIT, TEMP, REMOVE ME

* For each actionable item:
* Create/merge a task in TODO.md
* Replace the inline note with: “Tracked in TODO: T-###”
* If the comment is necessary context, keep context but remove the “task” directive.

Step 4 — Sweep repo config for task leaks

Check for:

* unused env vars in env.example (if present)
* unused scripts in package managers
* obsolete feature flags
* unused CI steps (if applicable)

* Convert actionable items into TODO tasks.

Step 5 — Normalize, split, dedupe

* Split large tasks
* Ensure every task has acceptance criteria + references
* Merge duplicates

Step 6 — Provisional prioritize

* P0: correctness, security, data integrity, payment correctness, crashes, shipping blockers
* P1: reliability, core UX, maintainability that prevents bugs, major DX bottlenecks
* P2: polish/optional

Gate:

* TODO.md has no completed tasks.
* Docs/code no longer contain executable tasks (only “Tracked in TODO: T-###” pointers).
* Top 5 tasks are immediately startable.
---

## Phase 2 — CODE COMPLETENESS (Spec Coverage)

Goal: every required behavior in specs exists end-to-end, including non-functional expectations.

Step 1 — Requirement → Implementation map

For each requirement in specs/project-spec.md:

* Identify:

  * UI entry point(s)
  * API/route(s)
  * service/domain logic
  * persistence logic (if any)
  * tests validating it

  * If any link is missing:
* Add a COMPLETE task.

Step 2 — Flow walkthrough (success/failure/recovery)

Pick the top 3–5 user flows and confirm:

* loading/empty/error states
* validation messages
* permission enforcement (if applicable)
* idempotency/retries (for writes/payments)

* Missing behaviors become COMPLETE tasks.

Step 3 — Contract completeness (if API boundaries exist)

Confirm:

* request/response validation
* error contracts
* backward compatibility expectations (if needed)

* Missing becomes COMPLETE tasks.

Rule:

* Do not create enhancements here. Only requirement gaps.

Gate:

* Every spec requirement is either mapped to code/tests or represented as a COMPLETE task.
---

## Phase 3 — CODE QUALITY (Maintainability + Consistency)

Goal: improve maintainability without doing feature work.

Step 1 — Run existing gates (if available)

* lint
* typecheck
* tests
* build

* Convert failures into QUALITY tasks if not immediately fixed.

Step 2 — Identify hotspots

Look for:

* very large files (“god files”)
* duplication
* unclear naming
* overly complex functions/logic
* boundary violations (layering)
* inconsistent error handling

* Convert into QUALITY tasks with:
* pain removed
* scoped changes
* acceptance criteria
* file references

Step 3 — Test quality

Address:

* flakiness
* missing boundary cases
* overly mocked tests

* Convert into QUALITY tasks.

Gate:

* Top 10 quality issues exist as concrete QUALITY tasks with acceptance criteria.
---

## Phase 4 — DEAD CODE (Safe Removal)

Goal: identify and remove dead code in safe batches with validation.

Step 1 — Find candidates

Candidates include:

* unused files/exports/components
* unused routes/endpoints
* obsolete feature flags
* unused env vars
* unused scripts/CI steps

* Convert into DEADCODE tasks that include:
* what to remove
* why it’s dead
* validation steps (tests/build/checks)

Step 2 — Remove only if safe

If you remove code now:

* do it in small batches
* run checks after each batch
* update docs that referenced removed code
* log completion in TODO_COMPLETED.md

Gate:

* Every dead code item has a validation plan.
* No “big bang” deletions.
---

## Phase 5 — CODE ENHANCEMENTS (Measurable Improvements)

Goal: produce a small, high-signal enhancement backlog that does not dilute shipping.

Rules (strict):

* Enhancements must have a trigger signal (feedback, metric, recurring issue, perf/cost/DX pain).
* Enhancements must define a benefit/metric and acceptance criteria.
* Cap at 20 enhancement tasks.
* Enhancements are P2 by default unless they reduce P0 risk.
* Enhancements must be safe to do in isolation unless explicitly marked otherwise.

Categories:

* PERF, UX, REL, DX, COST, SEC

Output:

* Add ENHANCE tasks into TODO.md with category in the title or context.

Gate:

* Enhancements are specific, measurable, and non-overlapping with completeness/quality work.
---

## Phase 6 — FINAL MERGE + PRIORITIZATION

Goal: one coherent TODO.md.

Steps:

1. Ensure tasks are deduped across phases.
2. Enforce ordering:

⠀
* P0 COMPLETE / correctness/security blockers
* P1 RELIABILITY + QUALITY
* P2 ENHANCE + polish

1. Order within each priority by dependency chain.
2. Confirm top 5 tasks are actionable and have references.

⠀
Final acceptance:

* TODO.md matches required format.
* TODO_COMPLETED.md contains dated completed items.
* Docs/code do not contain executable TODOs—only pointers to task IDs.
---

