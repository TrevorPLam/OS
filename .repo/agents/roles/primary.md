# Primary Agent Role

**File**: `.repo/agents/roles/primary.md`

Primary agents have full capabilities except for waiver and release process management.

## Capabilities

Primary agents can:
- `create_feature`
- `modify_existing`
- `add_dependency` (with security review)
- `change_api_contract` (with ADR)
- `change_schema` (with migration planning)
- `update_security` (with HITL)
- `create_adr`
- `create_task_packet`
- `run_verification_profiles`

## Restrictions

Primary agents CANNOT:
- `apply_waiver` (reviewer role only)
- `update_release_process` (release role only)

## Workflow

Primary agents follow the standard three-pass workflow:
1. Plan (with HITL escalation when needed)
2. Change (within boundaries)
3. Verify (with evidence)
