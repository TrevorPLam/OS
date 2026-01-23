# Constitution

This document establishes the fundamental governance principles that serve as the highest authority for this repository.

## Authority

This Constitution sits at the apex of the authority chain:

**Constitution > Manifest > Agents > Policy > Standards > Product**

All other documents, policies, and decisions must align with these constitutional articles.

---

## Article 1: Final Authority (Solo Founder)

**The solo founder has final authority on all decisions.**

### Description
In this solo founder context, final decisions rest with the repository owner. When conflicts arise or clarification is needed, the founder's decision is binding.

### Application
- All HITL items ultimately route to founder for final decision
- Founder can override any policy, standard, or decision
- Founder can grant exceptions to any rule
- Founder defines what "shippable" means

### Delegation
The founder may delegate authority to:
- Technical leads for architectural decisions
- Security team for security decisions
- Process leads for workflow decisions
- AI agents for routine decisions within defined boundaries

### Balance
While founder has final authority, this framework exists to:
- Reduce cognitive load on founder
- Enable autonomous agent operation
- Ensure consistency and quality
- Make decisions traceable and reviewable

---

## Article 2: Verifiable Over Persuasive

**Decisions must be based on evidence, not rhetoric.**

### Description
Arguments and proposals must be supported by verifiable evidence:
- Test results
- Benchmarks
- Metrics
- Logs
- Examples
- Data

### Application
When evaluating decisions:
1. ✅ **Accept**: "Benchmark shows 40% performance improvement" (verifiable)
2. ❌ **Reject**: "This feels faster" (subjective, not verifiable)
3. ✅ **Accept**: "Coverage increased from 85% to 92%" (measurable)
4. ❌ **Reject**: "Tests look better" (vague, not measurable)

### Requirements
- PRs must include evidence of correctness (tests pass, builds succeed)
- Performance claims must include benchmarks
- Security claims must include security analysis
- Architectural decisions must reference data (metrics, patterns, examples)

### Rationale
- Evidence reduces bias and emotion
- Evidence enables objective evaluation
- Evidence creates shared understanding
- Evidence is reviewable by others

---

## Article 3: No Guessing (UNKNOWN Handling)

**When uncertain, declare UNKNOWN and route to Human-In-The-Loop (HITL).**

### Description
Uncertainty is acceptable. Guessing is not. When agents or developers encounter:
- Unclear requirements
- Ambiguous specifications
- Unknown constraints
- Complex decisions with insufficient context
- External system implications

They MUST declare UNKNOWN and create HITL item.

### UNKNOWN Declaration Format

```markdown
## UNKNOWN Declaration

**What Is Unknown**: [Clear statement of what we don't know]

**Why It Matters**: [Impact of not knowing]

**What We Know**: [Context and facts we do have]

**Options Considered**: [If any alternatives were explored]

**HITL Required**: Yes

**Assigned To**: [Appropriate human reviewer]
```

### Benefits
- Prevents incorrect assumptions
- Makes uncertainty visible
- Enables human judgment where needed
- Reduces risk of silent failures
- Builds trust in the system

### Cultural Norm
Declaring UNKNOWN is a sign of:
- ✅ Wisdom: Recognizing limits of knowledge
- ✅ Responsibility: Seeking help when needed
- ✅ Professionalism: Prioritizing correctness
- ❌ NOT weakness or failure

---

## Article 4: Incremental Delivery

**Deliver small, frequent, shippable increments.**

### Description
Work is delivered in small batches that:
- Can be independently tested
- Can be independently reviewed
- Can be independently deployed
- Leave the system in a working state

### Size Guidelines
- PRs: Aim for <400 lines, max 1000 lines (with justification)
- Commits: One logical change per commit
- Features: Break into smallest shippable units
- Refactoring: Incremental, not big-bang

### Frequency
- Commit: Multiple times per day
- Push: At least daily
- PR: As soon as work is complete and tested
- Deploy: Multiple times per week (when appropriate)

### Benefits
- Faster feedback
- Easier review
- Lower risk
- Clearer progress
- Better rollback capability

### Anti-Patterns
- ❌ Waiting until "everything is done"
- ❌ Large multi-purpose PRs
- ❌ Combining unrelated changes
- ❌ Long-lived feature branches

---

## Article 5: Strict Traceability

**All artifacts must include explicit filepaths for traceability.**

### Description
Every document, PR, ADR, waiver, log, and comment must reference specific files with full paths.

### Required Locations
Filepaths are mandatory in:
- Pull Requests (list all changed files)
- Task Packets (list all affected files)
- Architecture Decision Records (list impacted files)
- Waivers (list files requiring waiver)
- Logs (indicate which files changed)
- Comments (reference related files)
- Documentation (link to actual files)

### Format
Use absolute paths from repository root:

```markdown
## Files Changed
- `/.repo/policy/PRINCIPLES.md` - Added P26
- `/src/auth/login/domain/authService.ts` - Fixed token validation
- `/tests/auth/login.test.ts` - Added test cases
```

### Benefits
- Easy to locate code
- Clear what changed
- Reviewers can jump to files
- Future maintainers understand context
- AI agents can navigate codebase

### Enforcement
- PR template includes "Files Changed" section
- Code review checklist verifies filepaths present
- CI checks for filepath requirements

---

## Article 6: Safety Before Speed

**When risk is detected, stop and escalate. Do not proceed blindly.**

### Description
Speed is important, but safety is paramount. When faced with:
- Security concerns
- Data loss potential
- Breaking changes
- External system impacts
- High complexity with unknowns

STOP. Do not proceed. Escalate to HITL.

### Risk Indicators
🔴 **High Risk** - Immediate stop required:
- Security vulnerability
- Data loss potential
- Breaking changes for users
- Financial transaction bugs
- Authentication/authorization issues

🟡 **Medium Risk** - Extra review required:
- Performance degradation
- Complex refactoring
- External API integration
- Database schema changes
- Cross-feature dependencies

🟢 **Low Risk** - Normal process:
- Documentation updates
- UI styling changes
- Internal refactoring
- Test additions
- Non-breaking features

### Escalation Process
1. Stop work immediately
2. Document the risk in HITL item
3. Notify appropriate reviewer (security, tech lead, founder)
4. Wait for approval and guidance
5. Implement mitigation plan if approved
6. Document decision and rationale

### Cultural Norm
Stopping for safety is:
- ✅ Responsible: Protecting users and system
- ✅ Professional: Following best practices
- ✅ Valued: Encouraged and rewarded
- ❌ NOT cowardice or slowness

---

## Article 7: Consistency Over Innovation

**Follow existing patterns unless there's compelling reason to change.**

### Description
The codebase has established patterns, conventions, and standards. New code should follow these patterns for consistency.

### When to Follow Patterns
✅ **Follow existing patterns for**:
- Naming conventions
- File organization
- Code structure
- Error handling
- Testing approach
- API design

### When to Innovate
✅ **Introduce new patterns when**:
- Existing pattern is problematic (with evidence)
- New pattern offers significant benefit (with data)
- Technology change requires it (with justification)
- ADR documents the change (with rationale)

### Process for Pattern Changes
1. Document current pattern and its issues
2. Propose new pattern with benefits
3. Show evidence of improvement
4. Write ADR for the change
5. Get approval from tech lead
6. Update documentation
7. Apply consistently going forward

### Benefits of Consistency
- Easier onboarding
- Faster development
- Fewer surprises
- Better maintainability
- AI agents can learn patterns

---

## Article 8: External Systems Require HITL

**All external system integrations require Human-In-The-Loop approval.**

### Description
External systems introduce risks:
- Security vulnerabilities
- Data privacy concerns
- Compliance requirements
- Vendor lock-in
- Cost implications
- Reliability dependencies

Therefore, ANY external integration requires HITL review and approval.

### What Counts as External System

**External**:
- Third-party SaaS services (Stripe, SendGrid, Auth0)
- Public APIs (GitHub API, Google Maps)
- Payment processors
- Authentication providers
- Analytics services
- CDN providers
- Cloud services (AWS, Azure, GCP)

**NOT External** (internal only):
- Own backend API
- Own database
- Own services
- Standard libraries from package managers (npm, pip)

### Required Information for HITL

When proposing external integration:

```markdown
## External Integration: [Service Name]

**Service**: [Name and URL]
**Purpose**: [Why we need this]
**Alternatives**: [What else was considered]
**Data Shared**: [What data we send to them]
**Data Received**: [What data we get from them]
**Security**: [How data is secured]
**Privacy**: [GDPR/CCPA implications]
**Cost**: [Pricing model and estimates]
**Vendor Lock-in**: [How difficult to switch]
**SLA**: [Their reliability guarantees]
**Compliance**: [Any compliance certifications]

**Recommendation**: [Approve/Reject/Need More Info]
```

### Approval Requirements
- Security team reviews security and privacy
- Legal reviews compliance and contracts
- Tech lead reviews technical fit
- Finance reviews cost implications
- Founder makes final decision

### Benefits
- Prevents security holes
- Ensures compliance
- Controls costs
- Evaluates vendor reliability
- Documents decisions

---

## Constitutional Amendments

### How to Amend

This Constitution can be amended through:

1. **Founder Decision**: Founder can amend at any time
2. **Community Proposal**: 
   - Propose amendment with rationale
   - Create ADR documenting change
   - Get founder approval
   - Update this document
   - Communicate to all stakeholders

### Amendment History

- **2024-01-15**: Initial constitution created (P0)
- [Future amendments listed here]

---

## Enforcement

These constitutional articles are enforced through:

1. **Automated Checks**: CI/CD validates compliance where possible
2. **Code Review**: Reviewers check for constitutional compliance
3. **HITL System**: Escalates violations to human review
4. **Quality Gates**: Blocks merges that violate constitution
5. **Culture**: Team norms and values

## Conflicts and Resolution

### When Conflicts Arise

If conflict between:
- **Constitution vs Policy**: Constitution wins
- **Constitution vs Standards**: Constitution wins
- **Constitution vs Product needs**: Constitution wins (or founder amends it)
- **Article vs Article**: Founder decides priority

### Exceptions

Founder may grant exceptions to constitutional articles in:
- Emergency situations (production down)
- One-time circumstances (with documentation)
- Experimental features (with rollback plan)

All exceptions must be:
- Documented in HITL item
- Time-limited
- Reviewed after the fact
- Used to improve processes

---

## Related Documents

- **Governance**: `/.repo/GOVERNANCE.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md`
- **Quality Gates**: `/.repo/policy/QUALITY_GATES.md`
- **Security Baseline**: `/.repo/policy/SECURITY_BASELINE.md`
- **HITL System**: `/.repo/policy/HITL.md`
