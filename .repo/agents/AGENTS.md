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

See:
- `.repo/agents/capabilities.md` - List of all capabilities
- `.repo/agents/roles/` - Role definitions (primary, secondary, reviewer, release)
