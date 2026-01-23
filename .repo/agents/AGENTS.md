# Agents Framework

This document defines the core rules, requirements, and guidelines for AI agents working in this repository.

## Purpose

AI agents are autonomous contributors that follow strict rules to maintain code quality, security, and governance compliance. This framework ensures agents operate safely and effectively.

## Core Principles

Agents must follow all principles in `/.repo/policy/PRINCIPLES.md`, especially:

- **P7: UNKNOWN Is a First-Class State** - Never guess; declare UNKNOWN and create HITL
- **P8: Read Repo First** - Always read /.repo docs and repo.manifest.yaml before acting
- **P10: Risk Triggers a Stop** - Stop and escalate when risk is detected
- **P13: Respect Boundaries by Default** - Follow architectural boundaries strictly

---

## Core Rules

### Rule 1: No Guessing - UNKNOWN Is Required

**When uncertain, declare UNKNOWN and create HITL.**

Agents MUST NOT:
- Guess at requirements
- Assume implementation details
- Infer user intent without explicit confirmation
- Proceed with ambiguous instructions

Agents MUST:
- Explicitly state UNKNOWN when information is missing
- Create HITL item with specific questions
- Wait for human clarification
- Document assumptions if proceeding with caveats

**Example UNKNOWN Declaration**:
```markdown
## UNKNOWN

**What**: User wants authentication, but method is unclear
**Options**: JWT, OAuth2, session-based, SSO
**Question**: Which authentication method should be used?
**HITL Created**: HITL-2024-01-15-auth-method-clarification.md
**Status**: Waiting for human decision
```

---

### Rule 2: Filepaths Required Everywhere

**All references to code, documentation, or artifacts must include explicit filepaths.**

Required in:
- Task packets
- Pull requests
- Logs
- Trace logs
- Comments
- ADRs
- Waivers
- HITL items

**Format**: Use absolute paths from repository root:
- ✅ Good: `/.repo/policy/PRINCIPLES.md`
- ✅ Good: `/src/auth/login/domain/authService.ts`
- ❌ Bad: `PRINCIPLES.md`
- ❌ Bad: `the auth service file`

**Why**: Enables quick navigation, clear references, and precise tracking of changes.

---

### Rule 3: Three-Pass Code Generation

**Code generation follows a structured three-pass approach.**

#### Pass 1: Plan
- Read existing code and documentation
- Understand requirements and constraints
- Identify affected files and dependencies
- Check for boundary violations
- Create high-level plan
- List verification commands
- Identify risks and unknowns

**Output**: Plan document with:
- Affected files (filepaths)
- Changes required
- Dependencies
- Risks
- Verification strategy

#### Pass 2: Implement
- Generate or modify code following the plan
- Follow existing patterns and conventions
- Respect boundaries
- Add appropriate comments
- Update related documentation
- Create or update tests

**Output**: Code changes with:
- Implementation files
- Test files
- Documentation updates

#### Pass 3: Verify
- Run verification commands
- Check tests pass
- Verify linting passes
- Check type checking passes
- Verify boundary compliance
- Run security checks
- Document results

**Output**: Verification report with:
- Commands executed
- Results (pass/fail)
- Evidence (logs, screenshots)
- Any waivers needed

**Example Three-Pass Flow**:
```
Pass 1 (Plan):
  - Read: src/auth/login/domain/authService.ts
  - Change: Add password reset functionality
  - Files: authService.ts, resetService.ts, resetRepository.ts
  - Tests: authService.test.ts, resetService.test.ts
  - Risks: Email sending (external), token expiration
  - Verify: npm test, npm run lint

Pass 2 (Implement):
  - Created: src/auth/reset/domain/resetService.ts
  - Created: src/auth/reset/data/resetRepository.ts
  - Modified: src/auth/login/domain/authService.ts
  - Created: tests/auth/reset.test.ts
  - Updated: docs/auth/README.md

Pass 3 (Verify):
  ✓ npm run lint -- src/auth/
  ✓ npm test -- tests/auth/reset.test.ts
  ✓ npm run type-check
  ✗ boundary check (cross-feature import detected)
  → Created: HITL-2024-01-15-reset-email-service.md
```

---

## Log Requirements

**All agents must produce comprehensive logs for every action.**

### Log Template
Reference: `/.repo/templates/AGENT_LOG_TEMPLATE.md`

### Required Log Sections
1. **Task Summary**: What was requested
2. **Plan**: How the task will be accomplished
3. **Execution**: Step-by-step actions taken
4. **Verification**: Commands run and results
5. **Files Changed**: Complete list with filepaths
6. **Issues Encountered**: Problems and resolutions
7. **HITL Items Created**: Links to any HITL items
8. **Status**: Complete, Blocked, Needs Review

### Log Location
- Active logs: `/.repo/logs/active/`
- Archived logs: `/.repo/logs/archived/`

### Example Log Entry
```markdown
# Agent Log - 2024-01-15-add-password-reset

## Task Summary
Add password reset functionality to authentication system

## Plan
1. Create reset service in src/auth/reset/domain/
2. Create reset repository in src/auth/reset/data/
3. Add reset endpoint in src/auth/login/
4. Create tests
5. Update documentation

## Execution
- [x] Created resetService.ts
- [x] Created resetRepository.ts
- [x] Updated authService.ts
- [x] Created reset.test.ts
- [ ] BLOCKED: Email service integration requires HITL

## Verification
✓ lint passed
✓ tests passed (15/15)
✗ boundary check failed (cross-feature email import)

## Files Changed
- /src/auth/reset/domain/resetService.ts (new)
- /src/auth/reset/data/resetRepository.ts (new)
- /src/auth/login/domain/authService.ts (modified)
- /tests/auth/reset.test.ts (new)
- /docs/auth/README.md (modified)

## Issues Encountered
Email service import crosses feature boundary.
Created HITL: HITL-2024-01-15-reset-email-service.md

## HITL Items Created
- HITL-2024-01-15-reset-email-service.md

## Status
Blocked - Waiting for HITL approval on email service integration
```

---

## Trace Log Requirements

**All agents must produce machine-readable trace logs for governance verification.**

### Trace Schema
Reference: `/.repo/templates/AGENT_TRACE_SCHEMA.json`

### Required Trace Fields
```json
{
  "trace_id": "unique-trace-id",
  "agent_id": "agent-name",
  "timestamp": "2024-01-15T10:30:00Z",
  "task_id": "TASK-123",
  "change_type": "feature|bugfix|refactor|docs",
  "files_changed": [
    "/path/to/file1.ts",
    "/path/to/file2.ts"
  ],
  "verification_commands": [
    "npm run lint",
    "npm test"
  ],
  "verification_results": {
    "lint": "pass",
    "tests": "pass",
    "coverage": "85%"
  },
  "hitl_items": [
    "HITL-2024-01-15-example.md"
  ],
  "risks_identified": [
    "Cross-feature dependency"
  ],
  "waivers_needed": [],
  "status": "complete|blocked|failed"
}
```

### Trace Validation
- Governance verify checks trace logs against schema
- Invalid traces block merge
- Missing required fields cause verification failure

---

## Cross-Feature Import Rule

**Cross-feature imports require an Architecture Decision Record (ADR).**

### What Is a Cross-Feature Import?

❌ **Forbidden without ADR**:
```typescript
// Feature A importing from Feature B
import { getUserData } from '@/auth/user/domain/userService';  // In billing feature
```

✅ **Allowed**:
```typescript
// Same feature imports
import { getUserData } from '../domain/userService';  // Within auth feature

// Platform imports (always allowed)
import { formatDate } from '@/platform/utils/date';
```

### Process for Cross-Feature Imports

1. **Check if really needed**:
   - Can logic go in shared platform?
   - Can functionality be duplicated (if small)?
   - Can dependency be inverted?
   - Can communication use events?

2. **If cross-feature import is necessary**:
   - Create ADR documenting the decision
   - Explain why alternatives were rejected
   - Get approval from architect
   - Add to manifest's allowed_edges

3. **Agent Actions**:
   - Detect cross-feature import during Pass 1 (Plan)
   - Create HITL item with ADR proposal
   - Wait for human approval
   - Update manifest if approved
   - Implement import in Pass 2

---

## Boundary Model Enforcement

**Agents must respect the hybrid_domain_feature_layer boundary model.**

### Boundary Rules

**Allowed Import Direction**:
```
UI → Domain → Data → Platform
```

**Forbidden**:
- Domain importing from UI
- Data importing from Domain or UI
- Platform importing from anything
- Cross-feature imports without ADR

### Boundary Checking

**During Pass 1 (Plan)**:
- Identify all imports
- Check against boundary rules
- Flag violations
- Create HITL if violation needed

**During Pass 2 (Implement)**:
- Only implement approved imports
- Add boundary comments to code
- Document in PR narration

**During Pass 3 (Verify)**:
- Run boundary checker: `make check:boundaries`
- Verify no violations
- Create waivers if needed with justification

### Agent Behavior on Boundary Violation

1. **Detect violation** during planning
2. **Stop implementation** immediately
3. **Create HITL item** explaining:
   - What import is needed
   - Why it's needed
   - Alternatives considered
   - Proposed ADR
4. **Wait for approval** before proceeding
5. **Document decision** in code and manifest

---

## Agent Roles

Agents have specific roles with different permissions and responsibilities.

### Primary Agent
- Makes code changes
- Creates PRs
- Runs verification
- Creates HITL items
- Follows three-pass approach

### Secondary Agent
- Reviews primary agent's work
- Checks for rule compliance
- Verifies boundary adherence
- Validates trace logs
- Approves or requests changes

### Reviewer Agent
- Performs code review
- Checks quality and style
- Verifies tests
- Checks documentation
- Ensures principles followed

### Release Agent
- Prepares releases
- Runs full verification suite
- Checks security baseline
- Verifies all HITL completed
- Creates release notes

---

## Agent Capabilities

See `/.repo/agents/capabilities.md` for detailed list of agent capabilities.

Capabilities define what actions agents are authorized to perform.

---

## Safety Rules

### Hard Stops (MUST create HITL)
- Security vulnerabilities detected
- Secrets in code
- External system integration
- Database schema changes
- Breaking API changes
- Production configuration changes
- Financial/payment code
- Authentication/authorization changes

### Soft Stops (Verify carefully)
- Performance concerns
- Complex refactoring
- New dependencies
- Cross-feature imports
- Unusual patterns

### Proceed with Caution
- Documentation updates
- Test additions
- Bug fixes (low risk)
- Style improvements
- Internal refactoring (same feature)

---

## Error Handling

**When errors occur, agents must**:

1. **Document the error** with full context
2. **Attempt automatic recovery** if safe
3. **Create HITL if unsure** how to proceed
4. **Never hide errors** or suppress failures
5. **Log everything** for debugging

**Example Error Response**:
```markdown
## Error Encountered

**Error**: Test suite failed on authService.test.ts
**Context**: Implementing password reset feature
**Root Cause**: Mock email service not configured
**Impact**: Cannot complete verification (Pass 3)

**Attempted Recovery**:
- Tried using existing email mock (not compatible)
- Checked docs for email service setup (not found)

**Action**: Created HITL-2024-01-15-email-mock-setup.md
**Status**: Blocked pending human guidance
```

---

## Communication with Humans

### When to Create HITL
- Unclear requirements
- Ambiguous specifications
- Unknown constraints
- Security concerns
- External system needs
- Breaking changes
- Complex architectural decisions
- Any UNKNOWN state

### HITL Best Practices
- Be specific about what's unclear
- Provide options with pros/cons
- Show research done
- Include relevant context
- Link to related files
- Suggest recommendation if confident
- Ask clear, answerable questions

---

## Continuous Improvement

### Learning from Experience
- Archive completed logs for reference
- Review resolved HITL items for patterns
- Update documentation with lessons learned
- Refine rules based on feedback

### Feedback Loop
- Humans can update agent rules
- Agents can propose rule improvements via HITL
- Regular retrospectives on agent performance
- Document new patterns and conventions

---

## Related Documents

- **Capabilities**: `/.repo/agents/capabilities.md`
- **Roles**: `/.repo/agents/roles.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md`
- **Constitution**: `/.repo/policy/CONSTITUTION.md`
- **Boundaries**: `/.repo/policy/BOUNDARIES.md`
- **HITL System**: `/.repo/policy/HITL.md`
- **Log Template**: `/.repo/templates/AGENT_LOG_TEMPLATE.md`
- **Trace Schema**: `/.repo/templates/AGENT_TRACE_SCHEMA.json`
