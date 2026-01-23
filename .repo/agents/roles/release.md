# Release Role

**File**: `.repo/agents/roles/release.md`

Release is a human role that controls release process and deployment.

## Capabilities

Release role can:
- `update_release_process` - Modify release/deployment procedures
- Deploy to production
- Manage release artifacts
- Control release gates

## Responsibilities

- Manage release process changes
- Execute production deployments
- Verify release readiness
- Manage release artifacts and versioning

## Workflow

Release role operates outside the three-pass agent workflow. They control the final step of getting code to production.
