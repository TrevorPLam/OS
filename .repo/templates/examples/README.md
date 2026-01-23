# Example Files

**Directory**: `.repo/templates/examples/`

This directory contains example files demonstrating the expected format for governance artifacts.

## Files

### `example_trace_log.json`

Example trace log following `.repo/templates/AGENT_TRACE_SCHEMA.json`.

**Usage:** Reference when creating trace logs for changes.

**Key fields:**
- `intent`: What the change does
- `files`: List of modified files (with paths)
- `commands`: Commands run for verification
- `evidence`: Proof of verification (test results, outputs)
- `hitl`: Related HITL items
- `unknowns`: UNKNOWN items (should be empty or resolved)

### `example_hitl_item.md`

Example HITL item file format.

**Usage:** Reference when creating HITL items in `.repo/hitl/`.

**Key sections:**
- Category (Risk, External Integration, Clarification, etc.)
- Status (Pending, In Progress, Completed, etc.)
- Required Human Action Steps
- Evidence of Completion
- Related Artifacts (PR, ADR, Waiver, Task Packet)

### `example_waiver.md`

Example waiver format.

**Usage:** Reference when creating waivers for policy exceptions.

**Key fields:**
- `Waives`: What policy/gate is being waived
- `Why`: Justification
- `Expiration`: When waiver expires
- `Remediation Plan`: How to fix the issue

### `example_task_packet.json`

Example task packet format.

**Usage:** Reference when creating task packets for changes.

**Key sections:**
- `goal`: What the task accomplishes
- `non_goals`: What's explicitly out of scope
- `acceptance_criteria`: Measurable success criteria
- `approach`: How the task will be completed
- `files_touched`: List of files to be modified
- `verification_plan`: How to verify completion
- `risks`: Potential issues
- `rollback_plan`: How to undo if needed
- `hitl_requirements`: Required HITL items

## Related Documentation

- `.repo/templates/AGENT_TRACE_SCHEMA.json` - Trace log schema
- `.repo/policy/HITL.md` - HITL process
- `.repo/agents/prompts/task_packet.md` - Task packet template
- `.repo/templates/WAIVER_TEMPLATE.md` - Waiver template
