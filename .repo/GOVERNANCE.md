# Governance Framework

## Authority Chain

The authority chain establishes the hierarchy of control and decision-making in this repository:

**Manifest > Agents > Policy > Standards > Product**

### Hierarchy Explanation

1. **Manifest**: The source of truth for commands, execution order, and system configuration
2. **Agents**: Agent configurations and instructions for AI-assisted development
3. **Policy**: Core policies, principles, and governance rules
4. **Standards**: Coding standards, style guides, and conventions
5. **Product**: Product-specific implementation and features

When conflicts arise, the higher authority in the chain takes precedence.

## Non-Coder Plain English Requirement

**All documentation, policies, and governance materials MUST be written in plain English.**

- Avoid technical jargon when possible
- Explain complex concepts clearly
- Use examples and analogies
- Write for a non-technical audience
- **UNKNOWN is allowed**: If something is unclear or unknown, explicitly state "UNKNOWN" and route to Human-In-The-Loop (HITL)

### Rationale

Plain English ensures:
- Accessibility to all team members regardless of technical background
- Clarity reduces misinterpretation
- Non-technical stakeholders can review and approve
- AI agents can understand and follow instructions accurately

## Deliver Small Increments Workflow

**All work must be delivered in small, incremental changes.**

### Requirements

1. **Small Pull Requests**: Each PR should address one focused change
2. **Frequent Commits**: Commit early and often with clear messages
3. **Continuous Integration**: Integrate changes frequently to avoid merge conflicts
4. **Incremental Testing**: Test each increment before moving to the next
5. **Progress Reporting**: Use the report_progress tool frequently to share updates

### Benefits

- Easier code review
- Faster feedback cycles
- Reduced risk of breaking changes
- Better rollback capability
- Clearer progress tracking

### Anti-Patterns to Avoid

- Large, multi-purpose PRs
- Waiting until "everything is done" to commit
- Silent work without progress updates
- Combining unrelated changes

## Filepath Requirement

**All artifacts must include explicit filepaths for traceability.**

This requirement is detailed in `/.repo/policy/PRINCIPLES.md` and applies to:
- Pull Requests
- Task Packets
- Architecture Decision Records (ADRs)
- Waivers
- Logs
- All documentation references

## Governance Enforcement

This governance framework is enforced through:
- Automated checks in CI/CD pipelines
- Code review requirements
- Quality gates (see `/.repo/policy/QUALITY_GATES.md`)
- Security baseline (see `/.repo/policy/SECURITY_BASELINE.md`)
- Boundaries enforcement (see `/.repo/policy/BOUNDARIES.md`)

## Related Documents

- **Principles**: `/.repo/policy/PRINCIPLES.md`
- **Quality Gates**: `/.repo/policy/QUALITY_GATES.md`
- **Security Baseline**: `/.repo/policy/SECURITY_BASELINE.md`
- **Boundaries**: `/.repo/policy/BOUNDARIES.md`
- **HITL System**: `/.repo/policy/HITL.md`
