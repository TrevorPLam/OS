# Agent Log Template

**File**: `.repo/templates/AGENT_LOG_TEMPLATE.md`

**Status**: Placeholder - To be filled in with actual log structure

This template defines the structure for agent logs. All agent work must be logged following this structure.

## Log Structure

```
# Agent Log: [Task/Feature Name]

## Date
[YYYY-MM-DD]

## Agent Role
[primary/secondary/reviewer/release]

## Task Reference
[Link to agents/tasks/TODO.md or BACKLOG.md item]

## Plan (Pass 1)
- Actions planned:
  - [Action 1]
  - [Action 2]
- Files to modify:
  - [filepath 1]
  - [filepath 2]
- Risks identified:
  - [Risk 1]
- UNKNOWN items:
  - [UNKNOWN item 1] → HITL item: [HITL-XXXX]
- HITL items created:
  - [HITL-XXXX]: [Description]

## Changes (Pass 2)
- Files modified:
  - [filepath 1]: [what changed]
  - [filepath 2]: [what changed]
- Commands run:
  - [command]: [output summary]

## Verification (Pass 3)
- Tests run:
  - [test command]: [result]
- Quality gates:
  - [gate name]: [pass/fail]
- Evidence:
  - [filepath to evidence]: [description]

## Notes
[Any additional notes or observations]
```

## Notes

This is a placeholder template. The actual log structure will be defined based on repository needs and tooling integration.
