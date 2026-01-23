# Agentic System - Complete File Mapping

**Date:** 2026-01-23
**Purpose:** Comprehensive mapping of EVERY file in the agentic coding system
**Use Case:** Injection into other repositories, complete system documentation

---

## Table of Contents

1. [Root-Level Entry Points](#root-level-entry-points)
2. [Policy & Governance Files](#policy--governance-files)
3. [Agent Framework Files](#agent-framework-files)
4. [Task Management Files](#task-management-files)
5. [Templates & Schemas](#templates--schemas)
6. [Automation Scripts](#automation-scripts)
7. [Shell Scripts](#shell-scripts)
8. [Context Files (.agent-context.json)](#context-files-agent-contextjson)
9. [Folder Guides (.AGENT.md)](#folder-guides-agentmd)
10. [CI/CD Integration Files](#cicd-integration-files)
11. [Supporting Documentation](#supporting-documentation)

---

## Root-Level Entry Points

### `AGENTS.json`
**Path:** `/AGENTS.json`
**Type:** JSON Schema
**Lines:** 183
**Purpose:** Machine-readable agent entry point with structured workflow definitions
**Key Contents:**
- Command routing (Start/Work/Task/Review/Security/Help)
- Required reading order (TODO.md → manifest.yaml → rules.json)
- Context determination logic (security, boundaries, backend/frontend, folder entry, unknown)
- Three-pass workflow definition (Pass 0: Context, Pass 1: Plan, Pass 2: Change, Pass 3: Verify)
- Task completion workflow
- PR creation requirements
- Rules (always/never)
- Decision trees (HITL needed?)
- Troubleshooting guidance
**Dependencies:** References `.repo/tasks/TODO.md`, `.repo/repo.manifest.yaml`, `.repo/agents/rules.json`
**Used By:** Agents as primary entry point
**Schema:** JSON Schema draft-07

### `AGENTS.md`
**Path:** `/AGENTS.md`
**Type:** Markdown
**Lines:** 164
**Purpose:** Human-readable agent entry point (fallback for non-JSON parsers)
**Key Contents:**
- Command routing instructions
- Step-by-step workflow (Read files → Determine context → Three-pass workflow → Complete task)
- PR creation checklist
- Rules summary (always/never)
- Decision tree for HITL
- Troubleshooting section
**Dependencies:** References same files as AGENTS.json
**Used By:** Human agents, AI agents that prefer markdown
**Relationship:** Human-readable version of AGENTS.json

---

## Policy & Governance Files

### `.repo/policy/CONSTITUTION.md`
**Path:** `.repo/policy/CONSTITUTION.md`
**Type:** Markdown
**Lines:** 43
**Purpose:** Immutable constitutional articles (8 articles) - highest level governance
**Key Contents:**
- Article 1: Final Authority (solo founder)
- Article 2: Verifiable over Persuasive (proof required)
- Article 3: No Guessing (UNKNOWN → HITL → Stop)
- Article 4: Incremental Delivery (small PRs)
- Article 5: Strict Traceability (link to tasks, archive)
- Article 6: Safety Before Speed (risky → HITL)
- Article 7: Per-Repo Variation (manifest allows variation)
- Article 8: HITL for External Systems (credentials, billing, production)
**Status:** IMMUTABLE (unless solo founder approves)
**Referenced By:** All policy files, rules.json, QUICK_REFERENCE.md

### `.repo/policy/PRINCIPLES.md`
**Path:** `.repo/policy/PRINCIPLES.md`
**Type:** Markdown
**Lines:** 78
**Purpose:** Operating principles (25 principles) implementing the constitution
**Key Contents:**
- Global rule: Filepaths required everywhere
- P3-P25: Detailed operating principles covering:
  - Change types, shippability, surprises, evidence
  - UNKNOWN handling, assumptions, risk triggers
  - Guardrails, rollback, boundaries, complexity
  - Consistency, decisions, PR narration, scope
  - Docs, examples, naming, waivers, ADRs, logs, TODO discipline
**Status:** Updateable (flexibility below constitution)
**Referenced By:** rules.json, QUICK_REFERENCE.md, BESTPR.md

### `.repo/policy/SECURITY_BASELINE.md`
**Path:** `.repo/policy/SECURITY_BASELINE.md`
**Type:** Markdown
**Lines:** 62
**Purpose:** Security rules, triggers, and forbidden patterns
**Key Contents:**
- Absolute prohibitions (no secrets/tokens/keys)
- Dependency vulnerability handling (always HITL)
- Security check frequency (every PR)
- Security review triggers (IDs 1,2,4,5,6,8,9,10):
  1. Auth/login behavior change
  2. Money/payment flow change
  4. External service integration change
  5. Sensitive data handling change
  6. Permission/privacy change
  8. Production config/keys change
  9. Cryptography/security control change
  10. Dependency/supply-chain risk change
- Forbidden patterns (regex patterns A-H):
  - A: Hardcoded API keys
  - B: Hardcoded secrets
  - C: AWS credentials
  - D: Private keys
  - E: OAuth tokens
  - F: Database connection strings with passwords
  - G: JWT secrets
  - H: Stripe keys
- Mandatory HITL actions (IDs 1-8)
- Evidence requirements
**Referenced By:** rules.json, governance-verify scripts, CI workflows
**Enforced By:** `check:security` command

### `.repo/policy/BOUNDARIES.md`
**Path:** `.repo/policy/BOUNDARIES.md`
**Type:** Markdown
**Lines:** 58
**Purpose:** Module boundary enforcement rules
**Key Contents:**
- Model: hybrid_domain_feature_layer
- Directory pattern: src/<domain>/<feature>/<layer>/
- Default allowed import direction: ui → domain → data → shared_platform
- Cross-feature rule: Requires ADR
- Enforcement method: hybrid_static_checker_plus_manifest
- Exceptions: Small (Task Packet) vs Large (ADR)
- Violation severity: waiver_plus_auto_task
- Boundary visibility: inline_comments_plus_summary
- Practical examples (allowed/forbidden)
- UBOS-specific notes (Django modules, firm-scoped multi-tenancy)
**Referenced By:** check-boundaries.js, rules.json, BESTPR.md
**Enforced By:** lint-imports with .importlinter config

### `.repo/policy/QUALITY_GATES.md`
**Path:** `.repo/policy/QUALITY_GATES.md`
**Type:** Markdown
**Lines:** 72
**Purpose:** Merge rules and verification requirements
**Key Contents:**
- Merge policy: soft block with auto-generated waivers
- Hard gates (must pass, not waiverable):
  - Required artifacts missing
  - Trace log missing/invalid
  - Required HITL items not Completed
  - Waiver missing/expired
  - governance-verify fails
- Waiverable gates:
  - Coverage targets (gradual ratchet)
  - Performance/bundle budgets
  - Warning budgets (zero warnings)
  - Test coverage regression
- Test requirements:
  - Minimum coverage thresholds (backend 80%, frontend 70%)
  - Test file requirements
  - Coverage validation
  - Test patterns (examples in templates/)
- Coverage strategy: gradual ratchet
- Performance budgets: strict with fallback
- Warnings: zero warnings policy
- PR size policy: no limits (but Article 4 requires decomposition)
- Required checks: all governance_verify_checks
**Referenced By:** governance-verify.sh, governance-verify.js, CI workflows
**Enforced By:** `governance-verify` command

### `.repo/policy/HITL.md`
**Path:** `.repo/policy/HITL.md`
**Type:** Markdown
**Lines:** 73
**Purpose:** Human-In-The-Loop process and item management
**Key Contents:**
- Storage model: Split (index in HITL.md, items in .repo/hitl/)
- Rule: minimal human effort (human sets status + evidence, agents do mechanical work)
- Categories: External Integration, Clarification, Risk, Feedback, Vendor
- Statuses: Pending | In Progress | Blocked | Completed | Superseded
- Merge blocking rule: PR blocked if required HITL not Completed
- Who can do what: Agents create, humans complete, agents sync
- External systems detection: keywords + manifest + change type
- HITL item file format (HITL-XXXX.md):
  - ID, Category, Required For, Owner, Reviewer, Status
  - Date Required, Date Completed, Summary
  - Required Human Action steps, Evidence, Related artifacts
- Index tables: Active and Archived
- Archiving process
**Referenced By:** create-hitl-item.sh, sync-hitl-to-pr.py, governance-verify scripts
**Used By:** All agents when encountering risky/unknown situations

### `.repo/policy/BESTPR.md`
**Path:** `.repo/policy/BESTPR.md`
**Type:** Markdown
**Lines:** 106
**Purpose:** Repository-specific best practices (UBOS-specific)
**Key Contents:**
- Repository map (where to work):
  - backend/modules/ (domain modules)
  - backend/api/ (API endpoints)
  - backend/config/ (Django settings)
  - frontend/src/ (React application)
  - tests/ (cross-cutting tests)
  - docs/ (documentation)
  - .repo/tasks/ (task management)
  - scripts/ (automation)
- Tech stack & core libraries:
  - Backend: Django 4.2, Python 3.11, PostgreSQL 15, DRF
  - Frontend: React 18.3, TypeScript 5.9, Vite 5.4
  - State: TanStack React Query 5.90
  - Forms: React Hook Form 7.69
  - Routing: React Router DOM 6.30
  - Visualization: ReactFlow 11.10
  - Testing: pytest, Vitest, Playwright, Testing Library
  - Formatting: ruff, black, mypy, ESLint, Prettier, tsc
  - Observability: Sentry
- Delivery workflow (what to run):
  - Local checks: make lint, make typecheck, make test, make verify
  - OpenAPI regeneration: make -C backend openapi
- Repo-specific coding practices:
  - Backend: Django REST Framework viewsets, FirmScopedMixin, module boundaries
  - Frontend: Functional components, React Query, React Hook Form
  - Shared: Integration tests, OpenAPI schema, firm-scoped multi-tenancy
- Documentation expectations
- Governance alignment
**Referenced By:** .agent-context.json files, folder guides, rules.json
**Used By:** Agents working in backend/frontend

---

## Agent Framework Files

### `.repo/agents/rules.json`
**Path:** `.repo/agents/rules.json`
**Type:** JSON Schema
**Lines:** 240
**Purpose:** Machine-readable agent rules and policies
**Key Contents:**
- Schema metadata (version 1.0.0, last_updated 2026-01-23)
- Required files (startup, conditional)
- Constitution (8 articles with rules and workflows)
- Principles (25 principles with global rule)
- Workflows (three-pass, unknown, hitl_decision)
- Security (triggers, absolute_prohibitions)
- Rules (always, never)
- Artifacts (by change type)
- Commands (from manifest)
- Tech stack (backend, frontend)
- Project structure
- Code style (backend, frontend patterns)
**Dependencies:** References CONSTITUTION.md, PRINCIPLES.md, repo.manifest.yaml
**Used By:** Agents as machine-readable rules source
**Relationship:** Machine-readable version of QUICK_REFERENCE.md

### `.repo/agents/QUICK_REFERENCE.md`
**Path:** `.repo/agents/QUICK_REFERENCE.md`
**Type:** Markdown
**Lines:** 537
**Purpose:** Human-readable quick reference card with essential rules
**Key Contents:**
- Reading order instructions
- Decision tree: Do I Need HITL?
- Constitution (8 articles summary)
- Key principles (most critical)
- Change type determination (decision tree with examples)
- Three-pass workflow details:
  - Pass 0: Context (folder entry)
  - Pass 1: Plan (change type, actions, risks, files, UNKNOWNs, HITL)
  - Pass 2: Change (apply edits, follow patterns, include filepaths)
  - Pass 3: Verify (run tests, evidence, logs, quality gates, PR)
- Artifact requirements by change type
- Command reference (from manifest)
- Quality gates summary
- HITL workflow
- Boundary enforcement
- Task lifecycle
- Troubleshooting
**Dependencies:** References all policy files, manifest, templates
**Used By:** Agents as primary human-readable reference
**Relationship:** Human-readable version of rules.json

### `.repo/agents/AGENTS.md`
**Path:** `.repo/agents/AGENTS.md`
**Type:** Markdown
**Purpose:** Deep dive on agent rules (if QUICK_REFERENCE insufficient)
**Status:** Referenced but not read in detail (token optimization)
**Used By:** Agents needing deeper context

### `.repo/agents/capabilities.md`
**Path:** `.repo/agents/capabilities.md`
**Type:** Markdown
**Purpose:** What agent role can do
**Used By:** Agents checking capabilities

### `.repo/agents/rules-compact.md`
**Path:** `.repo/agents/rules-compact.md`
**Type:** Markdown
**Purpose:** Compact version of rules
**Used By:** Token-constrained scenarios

### `.repo/agents/FORMATS.md`
**Path:** `.repo/agents/FORMATS.md`
**Type:** Markdown
**Purpose:** Format specifications for artifacts
**Used By:** Agents creating artifacts

### `.repo/agents/checklists/change-plan.md`
**Path:** `.repo/agents/checklists/change-plan.md`
**Type:** Markdown
**Purpose:** Checklist for planning changes
**Used By:** Agents in Pass 1 (Plan)

### `.repo/agents/checklists/pr-review.md`
**Path:** `.repo/agents/checklists/pr-review.md`
**Type:** Markdown
**Lines:** 9
**Purpose:** PR review checklist
**Key Contents:**
- One change type?
- Task packet complete?
- Evidence present?
- Logs + Trace included?
- Boundaries respected?
- HITL satisfied?
- Waivers valid?
**Used By:** Agents creating/reviewing PRs

### `.repo/agents/checklists/incident.md`
**Path:** `.repo/agents/checklists/incident.md`
**Type:** Markdown
**Purpose:** Incident response checklist
**Used By:** Agents handling incidents

### `.repo/agents/prompts/pr_template.md`
**Path:** `.repo/agents/prompts/pr_template.md`
**Type:** Markdown
**Purpose:** PR template prompt
**Used By:** Agents creating PRs

### `.repo/agents/prompts/task_packet.md`
**Path:** `.repo/agents/prompts/task_packet.md`
**Type:** Markdown
**Purpose:** Task packet creation prompt
**Used By:** Agents creating task packets

### `.repo/agents/roles/primary.md`
**Path:** `.repo/agents/roles/primary.md`
**Type:** Markdown
**Purpose:** Primary agent role definition
**Used By:** Primary agents

### `.repo/agents/roles/secondary.md`
**Path:** `.repo/agents/roles/secondary.md`
**Type:** Markdown
**Purpose:** Secondary agent role definition
**Used By:** Secondary agents

### `.repo/agents/roles/reviewer.md`
**Path:** `.repo/agents/roles/reviewer.md`
**Type:** Markdown
**Purpose:** Reviewer agent role definition
**Used By:** Reviewer agents

### `.repo/agents/roles/release.md`
**Path:** `.repo/agents/roles/release.md`
**Type:** Markdown
**Purpose:** Release agent role definition
**Used By:** Release agents

### `.repo/AGENT.md`
**Path:** `.repo/AGENT.md`
**Type:** Markdown
**Lines:** 25
**Purpose:** Quick start guide pointing to rules.json
**Key Contents:**
- Points to rules.json for complete rules
- Quick start reading order
- Note about single-agent system
**Used By:** Agents entering .repo directory

---

## Task Management Files

### `.repo/tasks/TODO.md`
**Path:** `.repo/tasks/TODO.md`
**Type:** Markdown
**Lines:** 86
**Purpose:** Current active task (single task only)
**Key Contents:**
- Workflow instructions
- Task completion process
- Task format reference
- Active task section
**Dependencies:** References BACKLOG.md, ARCHIVE.md
**Used By:** Agents as FIRST file to read (per AGENTS.json)
**Workflow:** When task completes → archive → promote from BACKLOG

### `.repo/tasks/BACKLOG.md`
**Path:** `.repo/tasks/BACKLOG.md`
**Type:** Markdown
**Lines:** 225+
**Purpose:** Prioritized queue of pending tasks (P0 → P3)
**Key Contents:**
- Workflow instructions (adding, promoting)
- Task format template
- Priority legend (P0-P3 with SLA)
- Tasks organized by priority
**Dependencies:** Referenced by TODO.md, archive-task.py, promote-task.sh
**Used By:** Agents promoting tasks, archive-task.py
**Workflow:** Top task promoted to TODO.md when TODO is empty

### `.repo/tasks/ARCHIVE.md`
**Path:** `.repo/tasks/ARCHIVE.md`
**Type:** Markdown
**Lines:** 74+
**Purpose:** Historical record of completed tasks
**Key Contents:**
- Workflow instructions (archiving)
- Archive format
- Statistics (total, by priority)
- Completed tasks (prepended, newest first)
**Dependencies:** Updated by archive-task.py
**Used By:** Agents for historical reference, archive-task.py
**Workflow:** Tasks moved here from TODO.md when complete

### `.repo/tasks/README.md`
**Path:** `.repo/tasks/README.md`
**Type:** Markdown
**Purpose:** Task management workflow documentation
**Used By:** Agents managing tasks (first time)

### `.repo/tasks/REMAINING_TASKS.md`
**Path:** `.repo/tasks/REMAINING_TASKS.md`
**Type:** Markdown
**Lines:** 300
**Purpose:** Implementation status tracking
**Used By:** Humans tracking implementation progress

### `.repo/tasks/IMPLEMENTATION_COMPLETE.md`
**Path:** `.repo/tasks/IMPLEMENTATION_COMPLETE.md`
**Type:** Markdown
**Purpose:** Completed implementation tasks
**Used By:** Historical reference

---

## Templates & Schemas

### `.repo/templates/PR_TEMPLATE.md`
**Path:** `.repo/templates/PR_TEMPLATE.md`
**Type:** Markdown
**Lines:** 27
**Purpose:** PR description template with change type declaration
**Key Contents:**
- JSON structure for PR metadata
- Change type decision tree
- Required fields: title, change_type, task_packet, changes, evidence, verification_commands_run, hitl, waivers, notes
**Used By:** Agents creating PRs
**Referenced By:** pr-review.md checklist

### `.repo/templates/ADR_TEMPLATE.md`
**Path:** `.repo/templates/ADR_TEMPLATE.md`
**Type:** Markdown
**Lines:** 14
**Purpose:** Architecture Decision Record template
**Key Contents:**
- JSON structure: context, decision_drivers, options, decision, consequences, modules, commands, migration, boundary_impact, hitl
**Used By:** Agents creating ADRs (cross-module, api_change)
**Referenced By:** BOUNDARIES.md, QUALITY_GATES.md

### `.repo/templates/WAIVER_TEMPLATE.md`
**Path:** `.repo/templates/WAIVER_TEMPLATE.md`
**Type:** Markdown
**Purpose:** Waiver template for waiverable gate failures
**Used By:** Agents creating waivers
**Referenced By:** QUALITY_GATES.md, create-waiver.sh

### `.repo/templates/AGENT_CONTEXT_SCHEMA.json`
**Path:** `.repo/templates/AGENT_CONTEXT_SCHEMA.json`
**Type:** JSON Schema
**Lines:** 188
**Purpose:** Schema for .agent-context.json files
**Key Contents:**
- Schema version, type, folder structure
- agent_rules (can_do, cannot_do, requires_hitl)
- patterns (code patterns)
- boundaries (can_import_from, cannot_import_from, cross_module_requires_adr)
- quick_links (guide, index, policy, best_practices)
- common_tasks (task definitions with steps and files)
- metrics (files_count, last_modified, last_verified, test_coverage)
**Used By:** validate-agent-context.js, all .agent-context.json files
**Referenced By:** All .agent-context.json files ($schema field)

### `.repo/templates/AGENT_TRACE_SCHEMA.json`
**Path:** `.repo/templates/AGENT_TRACE_SCHEMA.json`
**Type:** JSON Schema
**Lines:** 14
**Purpose:** Schema for trace logs
**Key Contents:**
- Required fields: intent, files, commands, evidence, hitl, unknowns
**Used By:** validate-agent-trace.js, generate-trace-log.sh
**Referenced By:** QUALITY_GATES.md (hard gate: trace log validation)

### `.repo/templates/AGENT_LOG_TEMPLATE.md`
**Path:** `.repo/templates/AGENT_LOG_TEMPLATE.md`
**Type:** Markdown
**Purpose:** Agent log template
**Used By:** Agents creating agent logs (non_doc_change)

### `.repo/templates/AGENT_PATTERNS_TEMPLATE.md`
**Path:** `.repo/templates/AGENT_PATTERNS_TEMPLATE.md`
**Type:** Markdown
**Purpose:** Code patterns template
**Used By:** Agents documenting patterns

### `.repo/templates/AGENT_QUICK_REFERENCE_TEMPLATE.md`
**Path:** `.repo/templates/AGENT_QUICK_REFERENCE_TEMPLATE.md`
**Type:** Markdown
**Purpose:** Template for creating folder-level .AGENT.md files
**Used By:** Agents creating folder guides

### `.repo/templates/RFC_TEMPLATE.md`
**Path:** `.repo/templates/RFC_TEMPLATE.md`
**Type:** Markdown
**Purpose:** Request for Comments template
**Used By:** Agents creating RFCs

### `.repo/templates/RUNBOOK_TEMPLATE.md`
**Path:** `.repo/templates/RUNBOOK_TEMPLATE.md`
**Type:** Markdown
**Purpose:** Runbook template
**Used By:** Agents creating runbooks

### `.repo/templates/examples/example_task_packet.json`
**Path:** `.repo/templates/examples/example_task_packet.json`
**Type:** JSON
**Purpose:** Example task packet for feature changes
**Used By:** Agents as reference when creating task packets

### `.repo/templates/examples/example_task_packet_api_change.json`
**Path:** `.repo/templates/examples/example_task_packet_api_change.json`
**Type:** JSON
**Purpose:** Example task packet for API changes
**Used By:** Agents creating API change task packets

### `.repo/templates/examples/example_task_packet_cross_module.json`
**Path:** `.repo/templates/examples/example_task_packet_cross_module.json`
**Type:** JSON
**Purpose:** Example task packet for cross-module changes
**Used By:** Agents creating cross-module task packets

### `.repo/templates/examples/example_trace_log.json`
**Path:** `.repo/templates/examples/example_trace_log.json`
**Type:** JSON
**Purpose:** Example trace log
**Used By:** Agents creating trace logs

### `.repo/templates/examples/example_hitl_item.md`
**Path:** `.repo/templates/examples/example_hitl_item.md`
**Type:** Markdown
**Purpose:** Example HITL item
**Used By:** Agents creating HITL items

### `.repo/templates/examples/example_waiver.md`
**Path:** `.repo/templates/examples/example_waiver.md`
**Type:** Markdown
**Purpose:** Example waiver
**Used By:** Agents creating waivers

### `.repo/templates/examples/example_test_viewset.py`
**Path:** `.repo/templates/examples/example_test_viewset.py`
**Type:** Python
**Purpose:** Example Django ViewSet test
**Used By:** Agents creating backend tests

### `.repo/templates/examples/example_test_component.tsx`
**Path:** `.repo/templates/examples/example_test_component.tsx`
**Type:** TypeScript/React
**Purpose:** Example React component test
**Used By:** Agents creating frontend tests

### `.repo/templates/examples/example_test_api_integration.py`
**Path:** `.repo/templates/examples/example_test_api_integration.py`
**Type:** Python
**Purpose:** Example API integration test
**Used By:** Agents creating integration tests

### `.repo/templates/examples/README.md`
**Path:** `.repo/templates/examples/README.md`
**Type:** Markdown
**Purpose:** Documentation for example files
**Used By:** Agents understanding examples

---

## Automation Scripts

### `.repo/automation/scripts/governance-verify.js`
**Path:** `.repo/automation/scripts/governance-verify.js`
**Type:** Node.js
**Lines:** 521+
**Purpose:** Governance verification script (Node.js version)
**Key Functionality:**
- Checks required policy files exist
- Validates manifest (no UNKNOWN placeholders)
- Checks HITL items status
- Validates repository structure
- Checks trace logs (if change type requires)
- Validates artifacts by change type
- Checks boundaries
- Validates context files
- Generates summary report
**Dependencies:** agent-logger.js (graceful fallback)
**Used By:** CI workflows, Makefile (check-governance target)
**Exit Codes:** 0 = pass, 1 = hard failure, 2 = waiverable failure

### `.repo/automation/scripts/agent-logger.js`
**Path:** `.repo/automation/scripts/agent-logger.js`
**Type:** Node.js
**Lines:** 275+
**Purpose:** Agent interaction logging SDK
**Key Functionality:**
- logInteraction(entry): Logs agent actions (JSONL format)
- logError(entry): Logs errors
- generateMetrics(date): Generates daily metrics from logs
- Log rotation/cleanup
- Graceful degradation (continues if logging fails)
**Log Locations:**
- `.agent-logs/interactions/YYYY-MM-DD.jsonl`
- `.agent-logs/errors/YYYY-MM-DD.jsonl`
- `.agent-logs/metrics/YYYY-MM-DD.json`
**Used By:** governance-verify.js, agents (if integrated)
**Dependencies:** fs, path (Node.js built-in)

### `.repo/automation/scripts/check-artifacts-by-change-type.js`
**Path:** `.repo/automation/scripts/check-artifacts-by-change-type.js`
**Type:** Node.js
**Lines:** 258+
**Purpose:** Checks required artifacts based on change type
**Key Functionality:**
- Parses change type from PR description (JSON or markdown)
- Checks artifacts per change type:
  - feature: task_packet, trace_log, tests
  - api_change: task_packet, adr, trace_log, openapi_update
  - security: hitl, trace_log, security_tests
  - cross_module: adr, task_packet, trace_log
  - non_doc_change: agent_log, trace_log, reasoning_summary
- Validates artifact recency (within 24 hours)
- Checks artifact locations and formats
**Used By:** governance-verify.js
**Referenced By:** QUALITY_GATES.md

### `.repo/automation/scripts/check-boundaries.js`
**Path:** `.repo/automation/scripts/check-boundaries.js`
**Type:** Node.js
**Lines:** 104
**Purpose:** Boundary checking script (wraps lint-imports)
**Key Functionality:**
- Checks if lint-imports is installed
- Validates .importlinter config exists
- Runs lint-imports with config
- Parses violations from output
- Option to fail on violations (--fail-on-violations)
**Dependencies:** lint-imports (external tool), .importlinter config
**Used By:** governance-verify.js, CI workflows
**Referenced By:** BOUNDARIES.md, repo.manifest.yaml (check:boundaries)

### `.repo/automation/scripts/validate-agent-context.js`
**Path:** `.repo/automation/scripts/validate-agent-context.js`
**Type:** Node.js
**Lines:** 156+
**Purpose:** Validates .agent-context.json files against schema
**Key Functionality:**
- Loads JSON schema (AGENT_CONTEXT_SCHEMA.json)
- Validates using ajv (with graceful fallback)
- Optional checks:
  - --check-files: Validates folder paths exist
  - --check-boundaries: Validates boundary rules
  - --check-links: Validates quick_links paths
- Reports errors and warnings
**Dependencies:** ajv (optional, graceful fallback), AGENT_CONTEXT_SCHEMA.json
**Used By:** governance-verify.js, CI workflows
**Referenced By:** check-stale-context.js

### `.repo/automation/scripts/check-stale-context.js`
**Path:** `.repo/automation/scripts/check-stale-context.js`
**Type:** Node.js
**Lines:** 113+
**Purpose:** Checks for stale context files (older than threshold)
**Key Functionality:**
- Finds all .agent-context.json files recursively
- Checks last_verified date against threshold (default 30 days)
- Reports missing last_verified dates
- Reports stale files (older than threshold)
- Option: --warn-only (doesn't exit with error)
- Option: --threshold-days=N (custom threshold)
**Dependencies:** validate-agent-context.js (indirect)
**Used By:** CI workflows, maintenance scripts
**Referenced By:** Context file maintenance workflow

### `.repo/automation/scripts/update-context-verified.js`
**Path:** `.repo/automation/scripts/update-context-verified.js`
**Type:** Node.js
**Purpose:** Updates last_verified dates in context files
**Key Functionality:**
- Updates metrics.last_verified to current date
- Can update single file or batch
**Used By:** Maintenance scripts, agents after verifying context

### `.repo/automation/scripts/validate-agent-trace.js`
**Path:** `.repo/automation/scripts/validate-agent-trace.js`
**Type:** Node.js
**Purpose:** Validates trace logs against schema
**Key Functionality:**
- Validates trace log JSON against AGENT_TRACE_SCHEMA.json
- Checks required fields: intent, files, commands, evidence, hitl, unknowns
**Dependencies:** AGENT_TRACE_SCHEMA.json
**Used By:** governance-verify.js, generate-trace-log.sh
**Referenced By:** QUALITY_GATES.md (hard gate)

### `.repo/automation/scripts/pattern-verification.js`
**Path:** `.repo/automation/scripts/pattern-verification.js`
**Type:** Node.js
**Purpose:** Verifies code patterns match context files
**Used By:** Governance verification

### `.repo/automation/scripts/generate-agent-context.js`
**Path:** `.repo/automation/scripts/generate-agent-context.js`
**Type:** Node.js
**Purpose:** Generates .agent-context.json from code analysis
**Used By:** Context file creation/update

### `.repo/automation/scripts/generate-index-json.js`
**Path:** `.repo/automation/scripts/generate-index-json.js`
**Type:** Node.js
**Purpose:** Generates index JSON for documentation
**Used By:** Documentation generation

### `.repo/automation/scripts/package.json`
**Path:** `.repo/automation/scripts/package.json`
**Type:** JSON
**Purpose:** Node.js dependencies for automation scripts
**Dependencies:** ajv (for JSON schema validation)
**Used By:** npm install in .repo/automation/scripts/

### `.repo/automation/scripts/setup-agent-logs.sh`
**Path:** `.repo/automation/scripts/setup-agent-logs.sh`
**Type:** Bash
**Purpose:** Sets up agent log directories
**Used By:** Initial setup

### `.repo/automation/scripts/SETUP_INSTRUCTIONS.md`
**Path:** `.repo/automation/scripts/SETUP_INSTRUCTIONS.md`
**Type:** Markdown
**Purpose:** Setup instructions for automation scripts
**Used By:** Initial setup

### `.repo/automation/scripts/STATUS.md`
**Path:** `.repo/automation/scripts/STATUS.md`
**Type:** Markdown
**Purpose:** Status of automation scripts
**Used By:** Maintenance

### `.repo/automation/scripts/VERIFICATION.md`
**Path:** `.repo/automation/scripts/VERIFICATION.md`
**Type:** Markdown
**Purpose:** Verification documentation
**Used By:** Testing

### `.repo/automation/ci/governance-verify.yml`
**Path:** `.repo/automation/ci/governance-verify.yml`
**Type:** YAML (GitHub Actions template)
**Purpose:** CI workflow template for governance verification
**Status:** Template (needs integration into .github/workflows/)
**Used By:** CI integration (when integrated)

### `.repo/automation/README.md`
**Path:** `.repo/automation/README.md`
**Type:** Markdown
**Purpose:** Automation directory documentation
**Used By:** Understanding automation structure

---

## Shell Scripts

### `scripts/governance-verify.sh`
**Path:** `scripts/governance-verify.sh`
**Type:** Bash
**Lines:** 309+
**Purpose:** Governance verification script (bash version)
**Key Functionality:**
- Same functionality as governance-verify.js (bash implementation)
- Checks policy files, manifest, HITL, structure, artifacts, boundaries
- Exit codes: 0 = pass, 1 = hard failure, 2 = waiverable failure
**Used By:** Makefile (check-governance target), CI workflows
**Referenced By:** repo.manifest.yaml (check:governance)

### `scripts/archive-task.py`
**Path:** `scripts/archive-task.py`
**Type:** Python 3
**Lines:** 291
**Purpose:** Archives completed task and promotes next task
**Key Functionality:**
- Reads current task from TODO.md
- Checks if all acceptance criteria are complete
- Moves task to ARCHIVE.md (prepends)
- Promotes next task from BACKLOG.md to TODO.md
- Updates archive statistics
- Option: --force (archive even if incomplete)
**Dependencies:** Python 3, re, sys, pathlib, datetime
**Used By:** Task completion workflow, CI workflows (if integrated)
**Referenced By:** TODO.md workflow instructions

### `scripts/promote-task.sh`
**Path:** `scripts/promote-task.sh`
**Type:** Bash
**Lines:** 125
**Purpose:** Promotes task from BACKLOG.md to TODO.md
**Key Functionality:**
- Checks if TODO.md already has task (prevents duplicates)
- Promotes specific task (by ID) or highest priority task
- Updates status to "In Progress"
- Removes task from BACKLOG.md
**Dependencies:** Bash, grep, sed
**Used By:** Task promotion workflow, archive-task.py (indirect)
**Referenced By:** TODO.md workflow instructions

### `scripts/create-hitl-item.sh`
**Path:** `scripts/create-hitl-item.sh`
**Type:** Bash
**Lines:** 142+
**Purpose:** Creates new HITL item from template
**Key Functionality:**
- Validates category (External Integration, Clarification, Risk, Feedback, Vendor)
- Generates next HITL ID (HITL-XXXX)
- Creates HITL item file (.repo/hitl/HITL-XXXX.md)
- Adds entry to HITL.md index (Active table)
- Uses template format
**Dependencies:** Bash, date, find, sort
**Used By:** Agents creating HITL items, workflow automation
**Referenced By:** HITL.md, AGENTS.json (HITL workflow)

### `scripts/create-waiver.sh`
**Path:** `scripts/create-waiver.sh`
**Type:** Bash
**Lines:** 175+
**Purpose:** Creates new waiver from template
**Key Functionality:**
- Creates waiver file (.repo/waivers/WAIVER-XXX.md)
- Uses WAIVER_TEMPLATE.md
- Adds to waivers index (if exists)
- Sets creation date
**Dependencies:** Bash, date
**Used By:** Agents creating waivers, governance-verify (auto-generation)
**Referenced By:** QUALITY_GATES.md

### `scripts/sync-hitl-to-pr.py`
**Path:** `scripts/sync-hitl-to-pr.py`
**Type:** Python 3
**Lines:** 199+
**Purpose:** Syncs HITL items status to PR description
**Key Functionality:**
- Parses HITL index (.repo/policy/HITL.md)
- Reads HITL item files (.repo/hitl/)
- Updates PR description via GitHub API
- Formats HITL section in PR
- Handles Completed/Superseded items (archives)
**Dependencies:** Python 3, requests (optional), GitHub API
**Environment Variables:** GITHUB_TOKEN, GITHUB_REPOSITORY
**Used By:** CI workflows (after HITL status changes)
**Referenced By:** CI integration (governance-verify.yml)

### `scripts/generate-trace-log.sh`
**Path:** `scripts/generate-trace-log.sh`
**Type:** Bash
**Purpose:** Generates trace log from workflow
**Key Functionality:**
- Creates trace log JSON file
- Validates against schema
- Saves to .repo/traces/
**Used By:** Agents in Pass 3 (Verify)
**Referenced By:** QUALITY_GATES.md (hard gate)

### `scripts/generate-agent-log.sh`
**Path:** `scripts/generate-agent-log.sh`
**Type:** Bash
**Purpose:** Generates agent log
**Used By:** Agents for non_doc_change

### `scripts/create-adr-from-trigger.sh`
**Path:** `scripts/create-adr-from-trigger.sh`
**Type:** Bash
**Purpose:** Creates ADR from trigger detection
**Used By:** Agents when ADR trigger detected

### `scripts/detect-adr-triggers.sh`
**Path:** `scripts/detect-adr-triggers.sh`
**Type:** Bash
**Purpose:** Detects ADR triggers in changes
**Used By:** Governance verification

### `scripts/validate-manifest-commands.sh`
**Path:** `scripts/validate-manifest-commands.sh`
**Type:** Bash
**Purpose:** Validates commands in manifest exist
**Used By:** Governance verification

### `scripts/validate-pr-body.sh`
**Path:** `scripts/validate-pr-body.sh`
**Type:** Bash
**Purpose:** Validates PR body format
**Used By:** PR validation

### `scripts/validate-task-format.sh`
**Path:** `scripts/validate-task-format.sh`
**Type:** Bash
**Purpose:** Validates task format in TODO.md/BACKLOG.md
**Used By:** Task validation

### `scripts/validate-trace-log.sh`
**Path:** `scripts/validate-trace-log.sh`
**Type:** Bash
**Purpose:** Validates trace log format
**Used By:** Trace log validation

### `scripts/check-expired-waivers.sh`
**Path:** `scripts/check-expired-waivers.sh`
**Type:** Bash
**Purpose:** Checks for expired waivers
**Used By:** Governance verification

### `scripts/archive-hitl-items.sh`
**Path:** `scripts/archive-hitl-items.sh`
**Type:** Bash
**Purpose:** Archives completed HITL items
**Used By:** HITL maintenance

### `scripts/suggest-waiver.sh`
**Path:** `scripts/suggest-waiver.sh`
**Type:** Bash
**Purpose:** Suggests waiver for gate failure
**Used By:** Governance verification

### `scripts/generate-metrics.sh`
**Path:** `scripts/generate-metrics.sh`
**Type:** Bash
**Purpose:** Generates metrics from agent logs
**Used By:** Metrics generation

### `scripts/generate-dashboard.sh`
**Path:** `scripts/generate-dashboard.sh`
**Type:** Bash
**Purpose:** Generates dashboard from metrics
**Used By:** Dashboard generation

### `scripts/get-next-task-number.sh`
**Path:** `scripts/get-next-task-number.sh`
**Type:** Bash
**Purpose:** Gets next task number for new tasks
**Used By:** Task creation

### `scripts/migrate.sh`
**Path:** `scripts/migrate.sh`
**Type:** Bash
**Purpose:** Migration script
**Used By:** Migrations

### `scripts/setup-migrations.sh`
**Path:** `scripts/setup-migrations.sh`
**Type:** Bash
**Purpose:** Sets up migrations
**Used By:** Migration setup

### `scripts/INDEX.md`
**Path:** `scripts/INDEX.md`
**Type:** Markdown
**Purpose:** Index of scripts
**Used By:** Script navigation

### `scripts/SCRIPTS.md`
**Path:** `scripts/SCRIPTS.md`
**Type:** Markdown
**Purpose:** Scripts documentation
**Used By:** Script usage

### `scripts/requirements.txt`
**Path:** `scripts/requirements.txt`
**Type:** Text
**Purpose:** Python dependencies for scripts
**Used By:** Python script setup

---

## Context Files (.agent-context.json)

### `backend/.agent-context.json`
**Path:** `backend/.agent-context.json`
**Type:** JSON
**Lines:** 85
**Purpose:** Backend folder context
**Key Contents:**
- Folder: backend/ (purpose: Django backend, layer: api)
- agent_rules: can_do, cannot_do, requires_hitl
- patterns: model, viewset, serializer (Django patterns)
- boundaries: can_import_from (empty), cannot_import_from (frontend), cross_module_requires_adr (true)
- quick_links: guide (BACKEND.md), index (INDEX.md), policy (BOUNDARIES.md), best_practices (BESTPR.md)
- common_tasks: Add new module, Add field to existing model
- metrics: files_count (500), last_modified (2026-01-23), last_verified (2026-01-23), test_coverage (0.82)
**Schema:** References .repo/templates/AGENT_CONTEXT_SCHEMA.json
**Used By:** Agents entering backend/ directory (Pass 0)

### `frontend/.agent-context.json`
**Path:** `frontend/.agent-context.json`
**Type:** JSON
**Purpose:** Frontend folder context
**Key Contents:**
- Folder: frontend/ (purpose: React frontend, layer: ui)
- agent_rules: React-specific rules
- patterns: React component patterns
- boundaries: Frontend-specific boundaries
- quick_links: FRONTEND.md, INDEX.md, etc.
**Schema:** References .repo/templates/AGENT_CONTEXT_SCHEMA.json
**Used By:** Agents entering frontend/ directory (Pass 0)

### `frontend/src/components/.agent-context.json`
**Path:** `frontend/src/components/.agent-context.json`
**Type:** JSON
**Purpose:** Components folder context
**Used By:** Agents working in components/

### `frontend/src/api/.agent-context.json`
**Path:** `frontend/src/api/.agent-context.json`
**Type:** JSON
**Purpose:** API client folder context
**Used By:** Agents working in API clients

### `backend/modules/core/.agent-context.json`
**Path:** `backend/modules/core/.agent-context.json`
**Type:** JSON
**Purpose:** Core module context
**Used By:** Agents working in core module

### `backend/modules/firm/.agent-context.json`
**Path:** `backend/modules/firm/.agent-context.json`
**Type:** JSON
**Purpose:** Firm module context
**Used By:** Agents working in firm module

### `backend/modules/clients/.agent-context.json`
**Path:** `backend/modules/clients/.agent-context.json`
**Type:** JSON
**Purpose:** Clients module context
**Used By:** Agents working in clients module

### `backend/modules/crm/.agent-context.json`
**Path:** `backend/modules/crm/.agent-context.json`
**Type:** JSON
**Purpose:** CRM module context
**Used By:** Agents working in CRM module

### `backend/modules/finance/.agent-context.json`
**Path:** `backend/modules/finance/.agent-context.json`
**Type:** JSON
**Purpose:** Finance module context
**Used By:** Agents working in finance module

### `backend/modules/projects/.agent-context.json`
**Path:** `backend/modules/projects/.agent-context.json`
**Type:** JSON
**Purpose:** Projects module context
**Used By:** Agents working in projects module

### `backend/api/clients/.agent-context.json`
**Path:** `backend/api/clients/.agent-context.json`
**Type:** JSON
**Purpose:** Clients API context
**Used By:** Agents working in clients API

**Total Context Files:** 11

---

## Folder Guides (.AGENT.md)

### `backend/modules/core/.AGENT.md`
**Path:** `backend/modules/core/.AGENT.md`
**Type:** Markdown
**Lines:** 78
**Purpose:** Core module quick reference
**Key Contents:**
- Quick rules (can do, cannot do, requires HITL)
- Patterns (model, utility function)
- Boundaries (can import from: nothing, cannot import from: business modules)
- Common tasks (Add utility function)
- Links (CORE.md, BOUNDARIES.md, .agent-context.json)
**Used By:** Agents entering core module (Pass 0)

### `backend/modules/firm/.AGENT.md`
**Path:** `backend/modules/firm/.AGENT.md`
**Type:** Markdown
**Purpose:** Firm module quick reference
**Used By:** Agents entering firm module

### `backend/modules/clients/.AGENT.md`
**Path:** `backend/modules/clients/.AGENT.md`
**Type:** Markdown
**Purpose:** Clients module quick reference
**Used By:** Agents entering clients module

### `backend/modules/finance/.AGENT.md`
**Path:** `backend/modules/finance/.AGENT.md`
**Type:** Markdown
**Purpose:** Finance module quick reference
**Used By:** Agents entering finance module

### `frontend/src/components/.AGENT.md`
**Path:** `frontend/src/components/.AGENT.md`
**Type:** Markdown
**Purpose:** Components folder quick reference
**Used By:** Agents entering components/

### `frontend/src/api/.AGENT.md`
**Path:** `frontend/src/api/.AGENT.md`
**Type:** Markdown
**Purpose:** API client folder quick reference
**Used By:** Agents entering API clients

**Total Folder Guides:** 6

---

## CI/CD Integration Files

### `Makefile`
**Path:** `/Makefile`
**Type:** Makefile
**Lines:** 212+
**Purpose:** Root Makefile orchestrating backend/frontend workflows
**Key Targets:**
- setup: Backend + frontend setup
- lint: Backend + frontend linting
- test: Backend + frontend tests
- test-performance: Backend performance tests
- typecheck: Backend type checking
- e2e: Frontend e2e tests
- frontend-build: Frontend build
- verify: Full verification (SKIP_HEAVY=1 by default)
- ci: CI workflow
- check-governance: Runs governance-verify.sh (lines 200-209)
**Key Functionality:**
- Orchestrates backend/frontend Makefiles
- Summary reporting
- check-governance target calls scripts/governance-verify.sh
**Referenced By:** repo.manifest.yaml (commands resolve to Makefile targets)
**Used By:** CI workflows, local development

### `.pre-commit-config.yaml`
**Path:** `.pre-commit-config.yaml`
**Type:** YAML
**Lines:** 89
**Purpose:** Pre-commit hooks configuration
**Key Hooks:**
- Ruff (Python linter)
- Black (Python formatter)
- Mypy (Type checking)
- git-secrets (Secret detection)
- lint-firm-scoping (Custom firm scoping linter)
- Django checks
- Frontend ESLint
- Trailing whitespace, file endings, YAML/JSON checks
- governance-verify (runs on .repo/, agents/, scripts/ changes)
**Installation:** `pip install pre-commit && pre-commit install`
**Used By:** Git pre-commit hooks
**Status:** Documented, verification needed

### `.repo/repo.manifest.yaml`
**Path:** `.repo/repo.manifest.yaml`
**Type:** YAML
**Lines:** 54
**Purpose:** Source of truth for executable commands + verification profiles
**Key Contents:**
- repo metadata (ships, ship_kind, release_protects)
- prerequisites (package_manager, runtime_pinned, platform_tools_required_for_release)
- commands (canonical names):
  - install: "make setup"
  - check:quick: "make lint && make frontend-build"
  - check:ci: "make verify SKIP_HEAVY=0"
  - check:release: Full release checks (security, audits, etc.)
  - check:governance: "./scripts/governance-verify.sh"
  - check:boundaries: "lint-imports --config .importlinter"
  - check:security: Security checks (pip-audit, safety, bandit, npm audit, trufflehog)
- verify_profiles: quick, ci, release, governance
- tests: required_level (unit+integration)
- budgets: mode, enforcement, fallback_to_default
- security: every_pr, release_includes_security, dependency_vulns_always_hitl, secrets_absolute_prohibition, forbidden_patterns_source
- boundaries: enforcement, edges_model, edges
**Rule:** Agents MUST NOT guess commands. If unknown, set <UNKNOWN> and open HITL.
**Referenced By:** AGENTS.json, rules.json, all agents
**Used By:** Agents before running ANY command

**Note:** GitHub Actions workflows (.github/workflows/ci.yml) mentioned in assessments but not found in file system. May need to be created or exists in different location.

---

## Supporting Documentation

### `.repo/DOCUMENT_MAP.md`
**Path:** `.repo/DOCUMENT_MAP.md`
**Type:** Markdown
**Lines:** 248
**Purpose:** Token-optimized reference system mapping all documents
**Key Contents:**
- Document inventory (when to read, token cost, priority)
- Smart reference trails by workflow:
  - Starting a new task
  - Making code changes
  - Security/risky changes
  - Cross-module work
  - Creating PR
  - UNKNOWN situation
  - Task management
- Token optimization rules (DO/DON'T)
- Token budget by workflow
- Document size estimates
**Used By:** Agents for efficient document navigation
**Referenced By:** AGENTS.md

### `.repo/GOVERNANCE.md`
**Path:** `.repo/GOVERNANCE.md`
**Type:** Markdown
**Purpose:** Governance framework overview
**Status:** First-time onboarding, too verbose for regular use
**Used By:** Humans understanding framework (not agents - use QUICK_REFERENCE.md)

### `.repo/INDEX.md`
**Path:** `.repo/INDEX.md`
**Type:** Markdown
**Purpose:** Navigation reference
**Used By:** Navigation

### `.repo/CHANGELOG.md`
**Path:** `.repo/CHANGELOG.md`
**Type:** Markdown
**Purpose:** Changelog
**Used By:** Historical reference

### `.repo/CLEANUP_SUMMARY.md`
**Path:** `.repo/CLEANUP_SUMMARY.md`
**Type:** Markdown
**Purpose:** Cleanup summary
**Used By:** Maintenance

### `.repo/CRITICAL_ANALYSIS_FAILURES.md`
**Path:** `.repo/CRITICAL_ANALYSIS_FAILURES.md`
**Type:** Markdown
**Lines:** 730
**Purpose:** Critical analysis of failures
**Used By:** Historical reference, assessment documents

### `.repo/IMPLEMENTATION_PROGRESS.md`
**Path:** `.repo/IMPLEMENTATION_PROGRESS.md`
**Type:** Markdown
**Purpose:** Implementation progress tracking
**Status:** May be outdated (conflicts with REMAINING_TASKS.md)
**Used By:** Progress tracking

### `.repo/PROJECTED_ANALYSIS_AFTER_FIXES.md`
**Path:** `.repo/PROJECTED_ANALYSIS_AFTER_FIXES.md`
**Type:** Markdown
**Purpose:** Projected analysis after fixes
**Used By:** Historical reference

### `.repo/REPOSITORY_BEST_PRACTICES_ANALYSIS.md`
**Path:** `.repo/REPOSITORY_BEST_PRACTICES_ANALYSIS.md`
**Type:** Markdown
**Purpose:** Best practices analysis
**Used By:** Historical reference

### `.repo/docs/TROUBLESHOOTING.md`
**Path:** `.repo/docs/TROUBLESHOOTING.md`
**Type:** Markdown
**Purpose:** Troubleshooting guide
**Used By:** Problem resolution

### `.repo/hitl/README.md`
**Path:** `.repo/hitl/README.md`
**Type:** Markdown
**Purpose:** HITL directory documentation
**Used By:** Understanding HITL structure

### `.repo/waivers/`
**Path:** `.repo/waivers/`
**Type:** Directory
**Purpose:** Waiver files storage
**Used By:** Waiver management

### `.repo/traces/`
**Path:** `.repo/traces/`
**Type:** Directory
**Purpose:** Trace log storage
**Status:** Empty (infrastructure ready, awaiting first use)
**Used By:** Trace log storage

### `.repo/logs/`
**Path:** `.repo/logs/`
**Type:** Directory
**Purpose:** Agent log storage
**Status:** Empty (infrastructure ready, awaiting first use)
**Used By:** Agent log storage

### `.agent-logs/`
**Path:** `.agent-logs/`
**Type:** Directory
**Purpose:** Agent interaction logs (from agent-logger.js)
**Subdirectories:**
- interactions/ (YYYY-MM-DD.jsonl files)
- errors/ (YYYY-MM-DD.jsonl files)
- metrics/ (YYYY-MM-DD.json files)
**Status:** Directories exist, may be empty
**Used By:** agent-logger.js

### `.repo/archive/assessments/`
**Path:** `.repo/archive/assessments/`
**Type:** Directory
**Files:** 11 markdown files
**Purpose:** Archived assessment documents
**Status:** Historical reference only (not for agents)

---

## File Count Summary

| Category | Count |
|----------|-------|
| Root Entry Points | 2 |
| Policy Files | 7 |
| Agent Framework Files | 17+ |
| Task Management Files | 6 |
| Templates & Schemas | 20+ |
| Automation Scripts (Node.js) | 13+ |
| Shell Scripts | 25+ |
| Context Files (.agent-context.json) | 11 |
| Folder Guides (.AGENT.md) | 6 |
| CI/CD Integration | 3+ |
| Supporting Documentation | 15+ |
| **TOTAL** | **120+ files** |

---

## Key Directories

| Directory | Purpose | Key Files |
|----------|---------|-----------|
| `.repo/policy/` | Governance policies | CONSTITUTION.md, PRINCIPLES.md, SECURITY_BASELINE.md, etc. |
| `.repo/agents/` | Agent framework | rules.json, QUICK_REFERENCE.md, checklists/, roles/, prompts/ |
| `.repo/tasks/` | Task management | TODO.md, BACKLOG.md, ARCHIVE.md |
| `.repo/templates/` | Templates & schemas | PR_TEMPLATE.md, ADR_TEMPLATE.md, schemas, examples/ |
| `.repo/automation/scripts/` | Node.js automation | governance-verify.js, agent-logger.js, validation scripts |
| `scripts/` | Shell scripts | governance-verify.sh, archive-task.py, create-hitl-item.sh, etc. |
| `.repo/hitl/` | HITL items | HITL-XXXX.md files |
| `.repo/waivers/` | Waivers | WAIVER-XXX.md files |
| `.repo/traces/` | Trace logs | TASK-XXX-trace.json files |
| `.repo/logs/` | Agent logs | Agent log files |
| `.agent-logs/` | Interaction logs | interactions/, errors/, metrics/ subdirectories |

---

## Integration Points

### CI/CD Integration
- **Makefile:** `check-governance` target calls `scripts/governance-verify.sh`
- **Pre-commit:** `.pre-commit-config.yaml` includes governance-verify hook
- **GitHub Actions:** Template exists (`.repo/automation/ci/governance-verify.yml`) but needs integration
- **HITL Sync:** `scripts/sync-hitl-to-pr.py` syncs HITL status to PRs

### Command Resolution
- **Source of Truth:** `.repo/repo.manifest.yaml`
- **Resolution:** Commands resolve to Makefile targets or direct scripts
- **Rule:** Agents MUST use manifest, never guess commands

### Workflow Integration
- **Entry Point:** `AGENTS.json` or `AGENTS.md`
- **Reading Order:** TODO.md → manifest.yaml → rules.json/QUICK_REFERENCE.md
- **Pass 0:** Read `.agent-context.json` and `.AGENT.md` when entering folder
- **Pass 1-3:** Three-pass workflow (Plan → Change → Verify)

---

## Dependencies & Relationships

### Core Dependencies
1. **AGENTS.json** → References: TODO.md, manifest.yaml, rules.json, policy files
2. **rules.json** → References: CONSTITUTION.md, PRINCIPLES.md, manifest.yaml
3. **QUICK_REFERENCE.md** → References: All policy files, manifest, templates
4. **governance-verify.js** → Uses: agent-logger.js, check-artifacts-by-change-type.js, check-boundaries.js, validate-agent-context.js
5. **.agent-context.json** → References: AGENT_CONTEXT_SCHEMA.json
6. **archive-task.py** → Reads/Writes: TODO.md, BACKLOG.md, ARCHIVE.md
7. **create-hitl-item.sh** → Creates: .repo/hitl/HITL-XXXX.md, Updates: .repo/policy/HITL.md

### External Dependencies
- **lint-imports:** Boundary checking (Python package)
- **ajv:** JSON schema validation (Node.js package, optional with fallback)
- **requests:** GitHub API (Python package, optional)
- **pre-commit:** Git hooks framework
- **ruff, black, mypy:** Python tooling
- **ESLint, Prettier:** Frontend tooling

---

## File Status Summary

### ✅ Production Ready
- All policy files (CONSTITUTION.md, PRINCIPLES.md, etc.)
- All agent framework files (rules.json, QUICK_REFERENCE.md, etc.)
- All templates and schemas
- Core automation scripts (governance-verify.js, agent-logger.js, etc.)
- Core shell scripts (governance-verify.sh, archive-task.py, promote-task.sh)
- All context files (.agent-context.json)
- All folder guides (.AGENT.md)
- Makefile integration
- Pre-commit configuration

### ⚠️ Needs Verification
- Pre-commit hooks installation status
- GitHub Actions workflow integration (template exists, needs integration)
- Agent logger actual usage by agents (SDK exists, used by scripts, unclear if agents call it)

### ❌ Missing/Incomplete
- Learning from failures (no analysis scripts)
- Self-healing (no retry logic, no automatic recovery)
- Auto-triggering (scripts exist but not scheduled)
- Trend analysis (no historical analysis)
- Pattern extraction from code (basic verification exists, no extraction)

---

## Usage Patterns

### Agent Startup Flow
1. Read `AGENTS.json` or `AGENTS.md`
2. Read `.repo/tasks/TODO.md` (current task)
3. Read `.repo/repo.manifest.yaml` (commands)
4. Read `.repo/agents/rules.json` or `QUICK_REFERENCE.md` (rules)
5. Enter folder → Read `.agent-context.json` and `.AGENT.md` (Pass 0)

### Task Completion Flow
1. Mark criteria `[x]` in TODO.md
2. Run `scripts/archive-task.py`
3. Script archives task to ARCHIVE.md
4. Script promotes next task from BACKLOG.md to TODO.md

### PR Creation Flow
1. Read `.repo/agents/checklists/pr-review.md`
2. Read `.repo/templates/PR_TEMPLATE.md`
3. Read `.repo/policy/QUALITY_GATES.md`
4. Read `.repo/policy/HITL.md` (check blockers)
5. Create PR with required sections
6. Run `governance-verify` (checks artifacts, boundaries, HITL, etc.)

### HITL Flow
1. Agent encounters risky/unknown situation
2. Agent runs `scripts/create-hitl-item.sh`
3. HITL item created in `.repo/hitl/HITL-XXXX.md`
4. Entry added to `.repo/policy/HITL.md` (Active table)
5. Human reviews and marks Completed
6. Agent runs `scripts/sync-hitl-to-pr.py` (updates PR)
7. Agent runs `scripts/archive-hitl-items.sh` (moves to Archived)

---

**End of Complete File Mapping**

*Generated: 2026-01-23*
*Total Files Mapped: 120+*
*Status: Comprehensive mapping complete*
