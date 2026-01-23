# Agent Capabilities

**File**: `.repo/agents/capabilities.md`

This file lists all available agent capabilities. See `.repo/agents/roles/` for which roles have access to which capabilities.

## Capability List

- `create_feature` - Create new features/modules
- `modify_existing` - Modify existing code within boundaries
- `add_dependency` - Add new dependencies (requires security review)
- `change_api_contract` - Modify API contracts (requires ADR)
- `change_schema` - Modify database schemas (requires migration planning)
- `update_security` - Update security configurations (requires HITL)
- `update_release_process` - Modify release/deployment process (release role only)
- `apply_waiver` - Apply policy waivers (reviewer role only)
- `create_adr` - Create Architecture Decision Records
- `create_task_packet` - Create task definitions
- `run_verification_profiles` - Execute verification commands from manifest
