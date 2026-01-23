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

Example task packet format for **feature** changes.

**Usage:** Reference when creating task packets for feature changes.

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

### `example_task_packet_api_change.json`

Example task packet format for **API change** changes.

**Usage:** Reference when creating task packets for API contract changes.

**Key differences from feature:**
- Must include OpenAPI schema updates
- Requires ADR for API contract changes
- Must maintain backward compatibility
- Includes API-specific verification steps

### `example_task_packet_cross_module.json`

Example task packet format for **cross-module** changes.

**Usage:** Reference when creating task packets for cross-module integrations.

**Key differences from feature:**
- Requires ADR (Principle 23, BOUNDARIES.md)
- Must verify no boundary violations
- Must respect firm-scoping (multi-tenancy)
- Includes boundary checking in verification plan

### `example_test_viewset.py`

Example test pattern for Django ViewSet tests.

**Usage:** Reference when writing tests for Django REST Framework viewsets.

**Key patterns:**
- Uses pytest fixtures for firm, user, api_client
- Tests CRUD operations (list, create, retrieve, update, delete)
- Tests firm-scoping (multi-tenancy)
- Tests authentication/authorization

### `example_test_component.tsx`

Example test pattern for React component tests.

**Usage:** Reference when writing tests for React components.

**Key patterns:**
- Uses Vitest and Testing Library
- Mocks React Query hooks
- Tests loading, success, error states
- Tests user interactions

### `example_test_api_integration.py`

Example test pattern for API integration tests.

**Usage:** Reference when writing integration tests for API workflows.

**Key patterns:**
- Tests complete workflows (create → list → update → delete)
- Tests pagination and filtering
- Tests firm-scoping across API calls

## Related Documentation

- `.repo/templates/AGENT_TRACE_SCHEMA.json` - Trace log schema
- `.repo/policy/HITL.md` - HITL process
- `.repo/agents/prompts/task_packet.md` - Task packet template
- `.repo/templates/WAIVER_TEMPLATE.md` - Waiver template
