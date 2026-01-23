# Secondary Agent Role

**File**: `.repo/agents/roles/secondary.md`

Secondary agents have limited capabilities focused on modifications within existing boundaries.

## Capabilities

Secondary agents can:
- `modify_existing` (within boundaries only)
- Refactor/port code within module boundaries
- `run_verification_profiles`

## Restrictions

Secondary agents CANNOT:
- `create_feature`
- `add_dependency`
- `change_api_contract`
- `change_schema`
- `update_security`
- `apply_waiver`
- `update_release_process`
- `create_adr`
- `create_task_packet`

## Workflow

Secondary agents follow the standard three-pass workflow but with stricter boundary enforcement. All changes must stay within existing module boundaries.
