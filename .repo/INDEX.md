# Governance Directory Index

**File**: `.repo/INDEX.md`

This file catalogs the contents of the `.repo/` governance directory. See [root `INDEX.md`](../INDEX.md) for repository overview.

## Directory Structure

### Core Files
- `GOVERNANCE.md` - Framework entry point and overview
- `repo.manifest.yaml` - Command definitions (source of truth for executable commands)
- `AGENT.md` - Folder-level agent guide

### `policy/` - Authoritative Governance Rules
- `CONSTITUTION.md` - 8 fundamental articles (immutable)
- `PRINCIPLES.md` - Operating principles (P3-P25, updateable)
- `QUALITY_GATES.md` - Quality standards and merge gates
- `SECURITY_BASELINE.md` - Security requirements and HITL triggers
- `BOUNDARIES.md` - Architectural boundaries and import rules
- `HITL.md` - Human-in-the-loop tracking (index of active/archived items)
- `BESTPR.md` - Repository-specific best practices

### `agents/` - AI Agent Framework
- `AGENTS.md` - Core agent rules (UNKNOWN workflow, 3-pass generation)
- `capabilities.md` - List of all agent capabilities
- `roles/` - Agent role definitions
  - `primary.md` - Primary agent role
  - `secondary.md` - Secondary agent role
  - `reviewer.md` - Reviewer role (human)
  - `release.md` - Release role (human)

### `templates/` - Document Templates
- `AGENT_LOG_TEMPLATE.md` - Agent log structure template
- `AGENT_TRACE_SCHEMA.json` - Agent trace log JSON schema

### `docs/` - Documentation Standards
- `standards/` - Documentation standards
  - `manifest.md` - Manifest command resolution guide

### `hitl/` - HITL Item Files
- `README.md` - HITL items directory documentation
- Individual HITL item files: `HITL-XXXX.md`

## Navigation

- [Root `INDEX.md`](../INDEX.md) - Repository master index
- [`backend/INDEX.md`](../backend/INDEX.md) - Backend directory index
- [`frontend/INDEX.md`](../frontend/INDEX.md) - Frontend directory index

## See Also

- `.repo/GOVERNANCE.md` - Framework entry point
- `.repo/AGENT.md` - What agents may do in this directory
- `.repo/repo.manifest.yaml` - Command definitions
