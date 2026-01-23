# Governance Directory Index

**File**: `.repo/INDEX.md`

This file catalogs the contents of the `.repo/` governance directory. See [root `INDEX.md`](../INDEX.md) for repository overview.

## Directory Structure

### Core Files
- `GOVERNANCE.md` - Framework entry point and overview
- `repo.manifest.yaml` - Command definitions (source of truth for executable commands)
- `AGENT.md` - Folder-level agent guide
- `DOCUMENT_MAP.md` - Token-optimized document reference system
- `CHANGELOG.md` - Framework change history
- `INDEX.md` - This file

### Current Analysis & Progress
- `CRITICAL_ANALYSIS_FAILURES.md` - Current critical analysis of system gaps
- `PROJECTED_ANALYSIS_AFTER_FIXES.md` - Projected analysis after fixes
- `IMPLEMENTATION_PROGRESS.md` - Current implementation progress tracking

### Entry Points (Root Level)
- `AGENTS.json` - **Primary entry point** (structured JSON for model parsing)
- `AGENTS.md` - Entry point (human-readable fallback)

### `policy/` - Authoritative Governance Rules
- `CONSTITUTION.md` - 8 fundamental articles (immutable)
- `PRINCIPLES.md` - Operating principles (P3-P25, updateable)
- `QUALITY_GATES.md` - Quality standards and merge gates
- `SECURITY_BASELINE.md` - Security requirements and HITL triggers
- `BOUNDARIES.md` - Architectural boundaries and import rules
- `HITL.md` - Human-in-the-loop tracking (index of active/archived items)
- `BESTPR.md` - Repository-specific best practices

### `agents/` - AI Agent Framework
- `rules.json` - **Primary rules source** (machine-readable, all rules)
- `QUICK_REFERENCE.md` - Human-readable rules cheat sheet
- `AGENTS.md` - Framework documentation (UNKNOWN workflow, 3-pass generation)
- `rules-compact.md` - Compact format (~200 tokens)
- `capabilities.md` - List of all agent capabilities
- `FORMATS.md` - Available format documentation
- `checklists/` - Agent checklists
  - `change-plan.md` - Change planning checklist
  - `pr-review.md` - PR review checklist
  - `incident.md` - Incident response checklist
- `prompts/` - Prompt templates
  - `pr_template.md` - PR prompt template
  - `task_packet.md` - Task packet template
- `roles/` - Agent role definitions
  - `primary.md` - Primary agent role
  - `secondary.md` - Secondary agent role
  - `reviewer.md` - Reviewer role (human)
  - `release.md` - Release role (human)

### `templates/` - Document Templates
- `AGENT_LOG_TEMPLATE.md` - Agent log structure template
- `AGENT_TRACE_SCHEMA.json` - Agent trace log JSON schema
- `PR_TEMPLATE.md` - Pull request template
- `ADR_TEMPLATE.md` - Architecture decision record template
- `WAIVER_TEMPLATE.md` - Policy waiver template
- `RFC_TEMPLATE.md` - Request for comments template
- `RUNBOOK_TEMPLATE.md` - Runbook template
- `examples/` - Example files
  - `example_trace_log.json` - Example trace log
  - `example_hitl_item.md` - Example HITL item
  - `example_waiver.md` - Example waiver
  - `example_task_packet.json` - Example task packet
  - `README.md` - Examples documentation

### `tasks/` - Task Management
- `TODO.md` - Current active task (ONE only)
- `BACKLOG.md` - Prioritized task queue (P0→P3)
- `ARCHIVE.md` - Completed tasks
- `REMAINING_TASKS.md` - Remaining implementation tasks from critical analysis
- `README.md` - Task management workflow

**Note:** Documentation has been moved to root `docs/` directory. See [`docs/README.md`](../docs/README.md) for documentation structure.

### `automation/` - Automation Infrastructure
- `ci/` - CI automation
  - `governance-verify.yml` - Governance verification workflow
- `scripts/` - Automation scripts
  - `governance-verify.js` - Governance verification script
  - `validate-agent-trace.js` - Trace log validation script

### `hitl/` - HITL Item Files
- `README.md` - HITL items directory documentation
- Individual HITL item files: `HITL-XXXX.md`

### `logs/` - Agent Logs
- Agent logs stored here (see `templates/AGENT_LOG_TEMPLATE.md`)

### `traces/` - Trace Logs
- Trace logs stored here (see `templates/AGENT_TRACE_SCHEMA.json`)

### `waivers/` - Policy Waivers
- Active policy waivers stored here

### `archive/` - Historical Documents
- `assessments/` - Archived assessment and analysis documents (historical reference only)
  - See `archive/assessments/README.md` for details

## Navigation

- [Root `INDEX.md`](../INDEX.md) - Repository master index
- [`backend/INDEX.md`](../backend/INDEX.md) - Backend directory index
- [`frontend/INDEX.md`](../frontend/INDEX.md) - Frontend directory index

## Entry Point Usage

**For AI Agents:**
1. Read `AGENTS.json` (root) - Primary structured entry point
2. Or read `AGENTS.md` (root) - Human-readable entry point
3. Follow instructions to read required files

**For Humans:**
- Start with `GOVERNANCE.md` for framework overview
- Use `DOCUMENT_MAP.md` to navigate documents
- See `CHANGELOG.md` for recent changes

## See Also

- `.repo/GOVERNANCE.md` - Framework entry point
- `.repo/AGENT.md` - What agents may do in this directory
- `.repo/repo.manifest.yaml` - Command definitions
- `AGENTS.json` - Primary agent entry point (root)
- `AGENTS.md` - Agent entry point (root, human-readable)
