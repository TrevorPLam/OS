# GitHub Copilot Prompt: Professional Task List Formatting

## Purpose

This prompt guides GitHub Copilot to restructure task lists into a professional, diamond-standard format with proper task abbreviations, hierarchical organization, scope definitions, and traceability.

## Prompt for Copilot

```
I need you to restructure this task list into a professional, diamond-standard format following these specifications:

## Required Structure

### 1. Phase Metadata
Include at the top of each phase document:
- **Phase**: P[X] (phase number)
- **Priority**: Critical/High/Medium/Low
- **Overall Status**: Not Started/In Progress/Blocked/Complete
- **Owner**: Team/Person responsible
- **Dependencies**: List prerequisite phases or external dependencies
- **Target Completion**: Date or Sprint number

### 2. Scope Definition
Clearly separate what is and isn't included:

**In Scope:**
- Specific deliverables and boundaries
- What IS included in this phase

**Out of Scope:**
- What is explicitly NOT included
- Deferred items or future considerations

### 3. Success Criteria
List measurable outcomes as checkboxes:
- [ ] Specific, testable criterion 1
- [ ] Specific, testable criterion 2

### 4. Work Packages (WP)
Organize tasks into logical work packages with this structure:

**WP-P[X].[Y]: [Work Package Name]**

**Block**: [Infrastructure/Documentation/Automation/Security/Configuration/Architecture]
**Priority**: P0/P1/P2/P3 (P0 = highest)
**Status**: Not Started/In Progress/Blocked/Complete
**Owner**: Name/Team
**Effort**: XS/S/M/L/XL (or specific hours)
**Risk**: 🔴 High | 🟡 Medium | 🟢 Low

**Dependencies:**
- Requires: [List of prerequisite WP IDs or tasks]
- Blocks: [List of WP IDs that depend on this]

**Description:**
[Clear description of what needs to be done]

**Acceptance Criteria:**
- [ ] Specific, testable criterion 1
- [ ] Specific, testable criterion 2

**Tasks:**
- [ ] **T-P[X].[Y].[Z]**: [Specific actionable task]
  - Files: [List of files to create/modify]
  - Commands: [Verification commands to run]
  - Evidence: [What proves this is complete]

**Out of Scope for This Work Package:**
- [Things that look related but are NOT part of this work]

**Notes:**
- [Additional context, links to ADRs, known issues]

### 5. Task Numbering System
Use this hierarchical system:
- **P[X]** = Phase number (0-9)
- **WP-P[X].[Y]** = Work Package (phase X, package Y)
- **T-P[X].[Y].[Z]** = Task (phase X, package Y, task Z)
- **T-P[X].[Y].[Z][a-z]** = Subtask (optional, for complex tasks)

Examples:
- P0 = Phase 0
- WP-P0.1 = Work Package 1 in Phase 0
- T-P0.1.1 = Task 1 in Work Package 1 of Phase 0
- T-P0.1.1a = Subtask 'a' of Task 1

### 6. Effort Sizing
- **XS**: 1-2 hours
- **S**: 2-8 hours (up to 1 day)
- **M**: 8-16 hours (1-2 days)
- **L**: 16-40 hours (2-5 days)
- **XL**: 40+ hours (1+ weeks)

### 7. Priority Levels
- **P0**: Critical path, blocks everything else
- **P1**: High priority, needed soon
- **P2**: Medium priority, important but not urgent
- **P3**: Low priority, nice to have

### 8. Risk Indicators
- 🔴 **High**: Complex, security-critical, or has many unknowns
- 🟡 **Medium**: Some complexity or dependencies
- 🟢 **Low**: Straightforward, well-understood

### 9. Block Categories
Categorize work packages by type:
- **Infrastructure**: Directory structure, tooling setup, configuration
- **Documentation**: Writing docs, standards, guides
- **Automation**: Scripts, CI/CD, automated checks
- **Security**: Security controls, scanning, policies
- **Configuration**: Config files, settings, environment
- **Architecture**: Design decisions, boundaries, patterns

### 10. End of Phase Sections

**Risks & Mitigation:**
List high-risk items with mitigation strategies

**Definition of Done:**
- [ ] All WP-P[X].X work packages marked complete
- [ ] All files committed and pushed
- [ ] Peer review completed
- [ ] No blockers for next phase

**Notes & References:**
- Related ADRs: [Links]
- Related PRs: [Links]
- External Dependencies: [List or "None"]

## Task Traceability Requirements

Every task MUST include:
1. **Files**: Specific file paths that will be created or modified
2. **Commands**: Exact commands to verify the task is complete
3. **Evidence**: Clear criteria that proves completion

Example:
```markdown
- [ ] **T-P0.1.1**: Create /.repo directory structure
  - Files: `/.repo/`, `/.repo/policy/`, `/.repo/agents/`
  - Commands: `tree /.repo -L 2`
  - Evidence: Directory structure matches specification
```

## Scope Boundaries

Always include explicit scope boundaries:
- **In Scope**: What IS being done in this phase/work package
- **Out of Scope**: What is explicitly NOT being done (defer to later or exclude entirely)

This prevents scope creep and sets clear expectations.

## Dependencies

Always document:
- **Requires**: What must be completed before this can start
- **Blocks**: What cannot start until this is complete

Use work package IDs (WP-P[X].[Y]) or external dependencies.

## Guidelines for Restructuring

1. **Preserve Content**: Don't lose any existing tasks
2. **Group Logically**: Combine related tasks into work packages
3. **Add Metadata**: Enhance with effort, risk, owner, dependencies
4. **Be Specific**: Every task should be actionable with clear success criteria
5. **No Orphans**: Every task belongs to a work package, every work package belongs to a phase
6. **Add Context**: Include "why" in descriptions, not just "what"
7. **Make it Scannable**: Use consistent formatting, clear headers, visual indicators

## Example Output Format

See TODOP0.md and TODOP3.md in this repository for complete examples of the expected format.

## Apply This Format

Please restructure the provided task list using this format. Ensure:
- Hierarchical task IDs (P[X], WP-P[X].[Y], T-P[X].[Y].[Z])
- Clear scope boundaries (in-scope/out-of-scope)
- Metadata for every work package (block, priority, status, owner, effort, risk)
- Traceability for every task (files, commands, evidence)
- Explicit dependencies (requires/blocks)
- Definition of done for the phase
- Risk mitigation strategies
```

## Usage Instructions

1. Copy the prompt above
2. Provide it to GitHub Copilot along with your task list
3. Review the output for completeness
4. Adjust work package groupings if needed
5. Verify all task IDs follow the numbering system
6. Ensure dependencies are correctly mapped

## Benefits of This Format

- **Traceability**: Every task has a unique ID and can be referenced
- **Clarity**: Clear scope prevents scope creep
- **Planning**: Dependencies and effort estimates enable better scheduling
- **Risk Management**: Visual indicators help prioritize attention
- **Verifiable**: Commands and evidence make completion objective
- **Professional**: Consistent format improves communication and handoffs

## Related Documents

- `TODOP0.md` - Example: Phase 0 (Core Infrastructure)
- `TODOP3.md` - Example: Phase 3 (Manifest & Commands)
- `TODO.md.old` - Original unstructured task list (for reference)

## Maintenance

When adding new tasks:
1. Determine which phase they belong to
2. Find or create appropriate work package
3. Assign next sequential task ID
4. Include files, commands, evidence
5. Update dependencies if needed
6. Mark scope explicitly
