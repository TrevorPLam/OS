# Agents Framework

**File**: `.repo/agents/AGENTS.md`

Agents operate ONLY within the rules defined in `.repo/policy/*.md` and `.repo/GOVERNANCE.md`.

## Core Rules (Plain English)

- **No guessing.** If something is not explicitly known, declare UNKNOWN and create a HITL item.
- **Filepaths required everywhere.** All changes, PRs, logs, and documentation must include filepaths.
- **Three-pass code generation required:**
  1) Plan (list actions, risks, files, UNKNOWNs)
  2) Change (apply edits)
  3) Verify (tests, evidence, logs, trace)
- **All logs must follow** `.repo/templates/AGENT_LOG_TEMPLATE.md`.
- **All trace logs must follow** `.repo/templates/AGENT_TRACE_SCHEMA.json`.
- **Cross-feature imports require ADR.** See `.repo/policy/BOUNDARIES.md` and Principle 23.
- **Boundary model enforced:** For Django modules, see `.repo/policy/BOUNDARIES.md` for UBOS-specific rules (api → modules → config/core with firm-scoping).

## UNKNOWN Workflow

When encountering uncertainty:
1. Mark the item as `<UNKNOWN>` in any relevant file (manifest, plan, etc.)
2. Create a HITL item in `.repo/policy/HITL.md`
3. Stop work on that uncertain portion
4. Do not proceed until HITL item is resolved

## Three-Pass Code Generation

### Pass 1: Plan
- List all actions to be taken
- Identify risks and required HITL items
- List all files that will be modified
- Mark any UNKNOWN items
- Get approval if required (HITL, ADR, etc.)

### Pass 2: Change
- Apply edits to files
- Follow existing patterns and boundaries
- Include filepaths in all changes
- Do not proceed if Pass 1 identified blockers

### Pass 3: Verify
- Run tests (unit, integration, e2e as appropriate)
- Provide evidence (command outputs, test results)
- Update logs and trace files
- Ensure all quality gates pass
- Document verification in PR

## Required References

All agents must reference:
- `.repo/policy/CONSTITUTION.md` - Fundamental articles
- `.repo/policy/PRINCIPLES.md` - Operating principles
- `.repo/policy/BOUNDARIES.md` - Architectural boundaries
- `.repo/policy/QUALITY_GATES.md` - Merge requirements
- `.repo/policy/SECURITY_BASELINE.md` - Security rules
- `.repo/policy/HITL.md` - Human-in-the-loop process
- `.repo/repo.manifest.yaml` - Command definitions
- `.repo/GOVERNANCE.md` - Framework entry point

## Capabilities and Roles

**Note:** This is a **single-agent system**. You are the only agent working on tasks. The role definitions in `.repo/agents/roles/` exist for potential future multi-agent scenarios but are not currently used.

See:
- `.repo/agents/capabilities.md` - List of all capabilities
- `.repo/agents/roles/` - Role definitions (for reference only, not currently used)

## Quick Reference

For a one-page cheat sheet, see `.repo/agents/QUICK_REFERENCE.md`.

## Trace Logs

**When to create:** In Pass 3 (Verify) after tests pass, for **non-doc changes only**.

**What it tracks:** What changed (files, commands, evidence, HITL items, unknowns).

**How:**
1. Create: `scripts/generate-trace-log.sh [task-id] [intent]`
2. Fill in required fields per `.repo/templates/AGENT_TRACE_SCHEMA.json`
3. Validate: `scripts/validate-trace-log.sh [trace-log-file]` or `node .repo/automation/scripts/validate-agent-trace.js [trace-log-file]`
4. Store in `.repo/traces/` (directory auto-created by script)

## Agent Logs

**When to create:** In Pass 3 (Verify) for **non-doc changes** (P24 requirement: Logs Required for Non-Docs).

**What it tracks:** Why/how (reasoning, decisions, assumptions, plan, risks).

**How:**
1. Create: `scripts/generate-agent-log.sh [task-id] [action]`
2. Fill in: `intent`, `plan`, `actions`, `evidence`, `decisions`, `risks`, `reasoning_summary`
3. Store in `.repo/logs/` (directory auto-created by script)

**Difference from trace log:**
- **Trace log** = What changed (files, commands, evidence)
- **Agent log** = Why/how (reasoning, decisions, assumptions)

## Examples

See `.repo/templates/examples/` for example files:
- `example_trace_log.json` - Trace log format
- `example_hitl_item.md` - HITL item format
- `example_waiver.md` - Waiver format
- `example_task_packet.json` - Task packet format
