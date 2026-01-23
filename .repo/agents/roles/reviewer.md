# Reviewer Role

**File**: `.repo/agents/roles/reviewer.md`

Reviewer is a human role that controls waivers and enforcement.

## Capabilities

Reviewers can:
- `apply_waiver` - Approve policy exceptions
- Review and approve HITL items
- Enforce quality gates
- Review ADRs
- Approve security changes

## Responsibilities

- Review PRs for compliance with governance rules
- Approve or reject waivers
- Mark HITL items as Completed
- Ensure all quality gates are met before merge
- Verify evidence and traceability

## Workflow

Reviewers operate outside the three-pass agent workflow. They provide human judgment and approval for high-risk decisions.
