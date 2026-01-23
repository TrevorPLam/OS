# Foundational Principles

This document defines the 23 foundational principles (P3-P25) that guide all development work in this repository.

## Filepath Requirement

**All artifacts must include explicit filepaths for traceability.**

Filepaths are required in:
- Pull Requests (PR descriptions and comments)
- Task Packets (every task must list affected files)
- Architecture Decision Records (ADRs)
- Waivers (must reference specific files)
- Logs (must indicate which files were changed)
- All documentation that references code

This ensures clear traceability and helps future maintainers understand the context of decisions.

---

## P3: One Change Type Per PR

**Each Pull Request should focus on one type of change: feature, bugfix, refactor, or docs.**

### Description
Mixing change types makes code review harder and increases risk. Keep PRs focused on a single purpose.

### Examples
- ✅ Good: PR adds new authentication feature
- ✅ Good: PR fixes login bug
- ❌ Bad: PR adds feature AND refactors unrelated code AND updates docs

### Verification
Reviewer confirms PR description matches single change type.

---

## P4: Make It Shippable

**Every commit should leave the codebase in a working, shippable state.**

### Description
Don't break the build. Every commit should compile, pass tests, and be deployable.

### Criteria
- All tests pass
- No build errors
- No linting errors
- Application runs successfully

### Verification
CI/CD pipeline validates build and tests.

---

## P5: Don't Break Surprises

**Avoid unexpected breaking changes. Deprecate gracefully.**

### Description
Breaking changes should be announced, documented, and deprecated gradually when possible.

### Examples
- ✅ Good: Add deprecation warning, maintain backward compatibility for 2 releases
- ❌ Bad: Remove API endpoint without warning

### Verification
Breaking changes documented in CHANGELOG and migration guide provided.

---

## P6: Evidence Over Vibes

**Decisions must be based on data, measurements, and evidence, not gut feelings.**

### Description
Use metrics, benchmarks, logs, and tests to justify decisions.

### Requirements
- Performance claims backed by benchmarks
- Bug reports include reproduction steps
- Refactoring decisions justified with code metrics
- Architecture decisions reference data

### Verification
PRs include evidence (test results, benchmarks, logs) supporting the change.

---

## P7: UNKNOWN Is a First-Class State

**It's okay to not know. Mark unknowns explicitly and route to Human-In-The-Loop (HITL).**

### Description
When something is unclear, ambiguous, or unknown, don't guess. Mark it as UNKNOWN and escalate to HITL.

### HITL Routing Rules
- External system integrations → HITL
- Security concerns → HITL
- Unclear requirements → HITL
- Ambiguous specifications → HITL
- High-risk changes → HITL

### Verification
UNKNOWN items documented and HITL ticket created.

---

## P8: Read Repo First

**Before making changes, read existing code, docs, and ADRs to understand context.**

### Description
Understand the current state before proposing changes. Check for existing patterns, conventions, and decisions.

### Mandatory Steps
1. Review relevant code files
2. Check for existing ADRs
3. Read related documentation
4. Search for similar past implementations
5. Understand dependencies and boundaries

### Verification
PR description references existing patterns and ADRs consulted.

---

## P9: Assumptions Must Be Declared

**State your assumptions explicitly in PRs, ADRs, and documentation.**

### Description
Hidden assumptions lead to misunderstandings. Make them visible.

### Declaration Requirements
- List assumptions in PR description
- Document assumptions in ADRs
- Note assumptions in comments for complex logic
- Update assumptions when they change

### Verification
Reviewer confirms assumptions are reasonable and documented.

---

## P10: Risk Triggers a Stop

**When risk is detected, stop and escalate. Don't proceed blindly.**

### Description
Safety over speed. If something feels risky, pause and get help.

### Escalation Process
1. Stop work immediately
2. Document the risk
3. Create HITL ticket
4. Wait for approval before proceeding
5. Implement mitigation if approved

### Risk Indicators
- Security concerns
- Data loss potential
- Breaking changes
- External system impacts
- Performance degradation
- Unclear requirements

### Verification
High-risk changes have HITL approval and mitigation plan.

---

## P11: Prefer Guardrails Over Heroics

**Build automated systems to prevent problems rather than relying on manual vigilance.**

### Description
Automation beats human effort. Use linters, tests, and CI/CD to catch issues early.

### Automation-First Approach
- Linters for code style
- Tests for correctness
- CI/CD for quality gates
- Static analysis for security
- Automated metrics collection

### Verification
New features include automated checks where applicable.

---

## P12: Rollback Thinking

**Every change should have a clear rollback plan.**

### Description
Plan for failure. Know how to undo changes quickly if needed.

### Rollback Requirements
- Database migrations are reversible
- Feature flags for risky features
- Deployment scripts support rollback
- Document rollback steps in ADRs
- Test rollback procedure

### Verification
High-impact changes include documented rollback procedure.

---

## P13: Respect Boundaries by Default

**Follow architectural boundaries unless there's a documented exception.**

### Description
Boundaries prevent coupling and maintain clean architecture. Don't cross boundaries without justification.

### Boundary Rules
- UI layer calls domain layer only
- Domain layer calls data layer only
- Data layer calls shared platform only
- No circular dependencies
- Cross-feature dependencies require ADR

### Verification
Boundary checker validates imports and dependencies.

---

## P14: Localize Complexity (Option B)

**Keep complexity contained. Use Option B: limit complexity to well-defined places.**

### Description
Complex code should be isolated in specific modules with clear interfaces. Don't let complexity spread.

### Option B Strategy
- Identify unavoidable complexity
- Isolate it in dedicated modules
- Provide simple, clean interfaces
- Document the complexity thoroughly
- Prevent complexity from leaking

### Verification
Complex logic is contained and well-documented.

---

## P15: Consistency Beats Novelty

**Follow existing patterns in the codebase. Don't introduce new patterns without good reason.**

### Description
Consistency makes code easier to understand and maintain. Innovation is good, but consistency is better.

### Consistency Guidelines
- Use existing naming conventions
- Follow established patterns
- Match existing code style
- Reuse existing utilities
- Justify deviations with ADR

### Verification
New code follows patterns established in similar existing code.

---

## P16: Decisions Written Down (Token-Optimized)

**Important decisions must be documented in Architecture Decision Records (ADRs).**

### Description
Write down why decisions were made. Keep ADRs concise and token-efficient.

### ADR Requirements
- Title: Clear, specific decision
- Status: Proposed/Accepted/Deprecated/Superseded
- Context: Why this decision is needed (1-2 paragraphs max)
- Decision: What was decided (concise)
- Consequences: Trade-offs and implications (bullet points)
- Alternatives: Options considered and rejected (brief)

### Token Optimization
- Use bullet points over prose
- Link to external docs instead of duplicating
- Keep total ADR under 500 words
- Use tables for comparisons

### Verification
Significant architectural changes have corresponding ADR.

---

## P17: PR Narration

**Pull Requests must tell a story. Explain what, why, and how.**

### Description
PR descriptions are documentation. They should be clear, complete, and helpful.

### Narration Template
1. **What**: What changed (files, features)
2. **Why**: Why this change is needed
3. **How**: How it was implemented
4. **Evidence**: Tests, benchmarks, screenshots
5. **Risks**: Known risks and mitigation
6. **Rollback**: How to undo if needed

### Verification
PR description follows narration template.

---

## P18: No Silent Scope Creep

**If scope changes, communicate it immediately. Don't let PRs grow silently.**

### Description
Scope changes are natural but must be transparent. Update stakeholders when scope shifts.

### Scope Change Process
1. Recognize scope has changed
2. Document new scope in PR
3. Notify reviewers/stakeholders
4. Consider splitting into multiple PRs
5. Update estimates if needed

### Verification
Scope changes documented in PR comments or description updates.

---

## P19: Docs Age With Code

**Documentation must be updated when code changes. Stale docs are worse than no docs.**

### Description
Keep documentation synchronized with code changes. Don't let docs drift.

### Update Requirements
- Update inline comments when logic changes
- Update README when features change
- Update API docs when interfaces change
- Update ADRs when decisions change
- Mark outdated docs clearly

### Verification
PRs that change functionality also update related documentation.

---

## P20: Examples Are Contracts

**Code examples in documentation must work. They are tested contracts, not suggestions.**

### Description
Examples should be accurate, tested, and maintained. Broken examples undermine trust.

### Example Maintenance Rules
- Examples must be executable
- Include examples in automated tests
- Update examples when APIs change
- Remove examples that no longer work
- Keep examples simple and clear

### Verification
Documentation examples are tested or clearly marked as illustrative only.

---

## P21: Naming Matters

**Names should be clear, consistent, and meaningful. Invest time in good naming.**

### Description
Good names make code self-documenting. Bad names cause confusion and bugs.

### Naming Conventions
- Use descriptive names, not abbreviations
- Be consistent within the codebase
- Follow language idioms
- Avoid misleading names
- Rename when better names are found

### Examples
- ✅ Good: `getUserByEmail`, `isAuthenticated`, `calculateTotalPrice`
- ❌ Bad: `getData`, `flag`, `temp`, `x`

### Verification
Code review includes naming quality assessment.

---

## P22: Waivers Rare + Temporary

**Quality gate waivers should be exceptional and time-limited.**

### Description
Waivers are for emergencies, not convenience. Every waiver needs justification and expiration.

### Waiver Policy
- Waivers require written justification
- All waivers have expiration dates
- Auto-generated waivers for soft blocks
- Waivers tracked in `/waivers/` directory
- Historical waivers archived for audit
- Review waiver usage monthly

### Verification
Waivers include justification, owner, and expiration date.

---

## P23: ADR Required When Triggered

**Architecture Decision Records (ADRs) are mandatory for significant decisions.**

### Description
Not every decision needs an ADR, but significant ones do.

### Trigger Conditions
When any of these occur, create an ADR:
1. Choosing between architectural approaches
2. Adding new major dependency
3. Changing data models or schemas
4. Introducing new patterns or conventions
5. Making security-related decisions
6. Establishing new boundaries
7. Significant performance trade-offs
8. Breaking backward compatibility

### Verification
Triggered decisions have corresponding ADR in `/.repo/docs/adr/` directory.

---

## P24: Logs Required for Non-Docs

**All code changes (non-documentation) must include a changelog entry or commit log.**

### Description
Track what changed and why. Logs enable understanding history and debugging.

### Log Requirements
- Commit messages are clear and descriptive
- CHANGELOG.md updated for user-facing changes
- Breaking changes prominently noted
- Link commits to issues/tickets
- Include author and date

### Verification
PRs include changelog updates or clear commit messages.

---

## P25: Token-Optimized TODO Discipline

**TODOs must be tracked, actionable, and archived when resolved.**

### Description
TODOs in code should be managed systematically, not forgotten.

### TODO Format
```
// TODO(owner, YYYY-MM-DD): Brief description
// Context: Why this is needed
// Tracked: Link to issue/ticket
```

### TODO Discipline
- Every TODO has an owner
- Every TODO has a date
- Every TODO links to a tracking ticket
- Review TODOs monthly
- Archive resolved TODOs with reference
- Don't leave orphaned TODOs

### Archive References
- Resolved TODOs moved to `/.repo/archive/todos/`
- Include resolution date and outcome
- Link to PR that resolved it

### Verification
Code review checks TODO format and tracking.

---

## Principle Enforcement

These principles are enforced through:
- Code review checklists
- Automated linting and checks
- CI/CD quality gates
- Periodic audits
- Team training and onboarding

## Related Documents

- **Governance**: `/.repo/GOVERNANCE.md`
- **Quality Gates**: `/.repo/policy/QUALITY_GATES.md`
- **Security Baseline**: `/.repo/policy/SECURITY_BASELINE.md`
- **Boundaries**: `/.repo/policy/BOUNDARIES.md`
