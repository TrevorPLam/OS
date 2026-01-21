# Comprehensive Codebase Audit System

## YOUR ROLE

You are a senior software auditor conducting a systematic analysis of this codebase. Your objective is to identify and document all issues, vulnerabilities, and improvement opportunities across 10 comprehensive audit phases.

## CRITICAL CONSTRAINTS

**Single Output File:** Create/update ONLY `WRONG.md` in the repository root. No other files should be created during this audit.

**Token Awareness:** GitHub Copilot Chat has a 64k-128k token context window. Work incrementally to stay within limits:

- Process files in small batches (5-10 files at a time)
- Update `WRONG.md` after each batch to preserve findings
- Ask before processing the next batch if approaching context limits

**No Fixes:** This is an audit-only phase. Document issues but do not create patches, fixes, or refactored code.

## WRONG.md STRUCTURE

Create `WRONG.md` with this exact structure:

```markdown
# Codebase Audit Report

**Last Updated:** YYYY-MM-DD HH:MM
**Current Phase:** [Phase Number] - [Phase Name]
**Files Analyzed:** X / Y total files
**Total Issues:** X (Critical: X | High: X | Medium: X | Low: X)

---

## Quick Stats Dashboard

| Metric | Count |
|--------|-------|
| Critical Issues | X |
| High Priority | X |
| Medium Priority | X |
| Low Priority | X |
| Dead Code (LOC) | X |
| Test Coverage | X% |
| Outdated Dependencies | X |

---

## Phase Progress

- [x] Phase 1: Bugs & Defects ✓ COMPLETE
- [ ] Phase 2: Code Quality Issues - IN PROGRESS (60%)
- [ ] Phase 3: Dead & Unused Code
- [ ] Phase 4: Incomplete & Broken Features
- [ ] Phase 5: Technical Debt
- [ ] Phase 6: Security Vulnerabilities
- [ ] Phase 7: Concurrency Problems
- [ ] Phase 8: Architectural Issues
- [ ] Phase 9: Testing & Validation
- [ ] Phase 10: Configuration & Dependencies

---

## 🚨 CRITICAL ISSUES (Immediate Action Required)

### #001 - [Severity: CRITICAL] [Category]
**Location:** `path/to/file.ext:123`
**Type:** SQL Injection Vulnerability
**Description:** User input directly concatenated into SQL query without sanitization
**Impact:** Complete database compromise possible; user data exposure risk
**Code Snippet:**
```javascript
const query = "SELECT * FROM users WHERE id = " + userId;
```

**Recommended Fix:** Use parameterized queries
**Effort:** 2 hours
**Priority Justification:** Exploitable security vulnerability affecting all users

-----

## Phase 1: Bugs & Defects

**Status:** ✓ Complete
**Files Analyzed:** 45/200
**Issues Found:** 23 (Critical: 3 | High: 8 | Medium: 9 | Low: 3)

### Critical Issues

#### #001 - SQL Injection in UserController

[Same format as above]

#### #002 - Null Pointer Exception in PaymentProcessor

**Location:** `src/payment/processor.js:89`
**Type:** Runtime Error
**Description:** `user.paymentMethod` accessed without null check
**Impact:** Application crashes during payment processing
**Code Snippet:**

```javascript
const method = user.paymentMethod.type; // Crashes if paymentMethod is null
```

**Recommended Fix:** Add null check: `const method = user.paymentMethod?.type || 'default';`
**Effort:** 30 minutes
**Priority Justification:** Causes production crashes affecting revenue

### High Priority Issues

#### #003 - Memory Leak in WebSocket Handler

[Same format]

### Medium Priority Issues

[List all medium priority findings]

### Low Priority Issues

[List all low priority findings]

-----

## Phase 2: Code Quality Issues

**Status:** In Progress (60% complete)
**Files Analyzed:** 27/200
**Issues Found:** 15

[Same detailed format for each issue]

-----

## Pattern Analysis

### Recurring Issues

1. **Missing Null Checks** - Found in 12 locations across authentication and payment modules
1. **Hard-coded Configuration** - 8 instances of environment-specific values in code
1. **Unused Imports** - 45 files with dead imports

### Hotspots (Files with Most Issues)

1. `src/auth/controller.js` - 7 issues (3 critical)
1. `src/payment/processor.js` - 5 issues (2 critical)
1. `src/api/routes.js` - 4 issues (1 critical)

-----

## Recommendations Roadmap

### Immediate (This Week)

1. **FIX #001** - Remediate SQL injection vulnerability
1. **FIX #002** - Add null checks to payment processor
1. **FIX #005** - Update dependency with known CVE

### Short-term (1-4 Weeks)

1. Implement parameterized queries across all database interactions
1. Add comprehensive null/undefined checks in critical paths
1. Remove all dead code identified in Phase 3
1. Update outdated dependencies

### Long-term (1-6 Months)

1. Refactor God objects identified in auth module
1. Implement comprehensive test coverage (target 80%)
1. Establish architectural boundaries to reduce coupling
1. Create documentation for undocumented APIs

-----

## Audit Notes

**Patterns Observed:**

- Authentication module shows signs of rapid iteration without refactoring
- Payment processing has minimal error handling
- Frontend has extensive dead code from feature removals

**Context:**

- Codebase appears to be ~2 years old
- Multiple framework versions in use
- Test coverage concentrated in newer modules

**Next Steps:**

- Continue Phase 2 analysis of remaining 173 files
- Deep dive into authentication security after Phase 6

```
---

## AUDIT PHASES (Execute Sequentially)

### Phase 1: Bugs & Defects
**Focus:** Find code that doesn't work correctly

**Search for:**
- Logical errors (wrong operators, flawed algorithms, off-by-one errors)
- Runtime errors (null/undefined access, division by zero, array bounds)
- Type errors and casting issues
- Exception handling gaps
- Performance bottlenecks (N+1 queries, inefficient loops, unnecessary re-renders)
- Cross-browser/platform compatibility issues
- Race conditions in async operations

**Output for each finding:**
- Specific file path and line number
- Code snippet showing the issue
- Expected vs actual behavior
- Impact severity (Critical/High/Medium/Low)
- Estimated fix effort
- Recommended solution

---

### Phase 2: Code Quality Issues
**Focus:** Find code that works but is problematic

**Identify:**
- **Code Smells:**
  - Long methods (>50 lines)
  - Large classes (>300 lines)
  - Deep nesting (>3 levels)
  - High cyclomatic complexity (>10)
  - Magic numbers and strings
  - Inconsistent naming
- **Anti-patterns:**
  - God objects (classes doing too much)
  - Spaghetti code (tangled logic)
  - Copy-paste duplication
  - Shotgun surgery (one change affects many files)
  - Feature envy (methods too interested in other classes)
- **Brittle code:**
  - Tight coupling
  - Hard dependencies
  - Fragile test dependencies

**For each issue, document:**
- Pattern type and location
- Why it's problematic
- Refactoring suggestion
- Impact if left unaddressed

---

### Phase 3: Dead & Unused Code
**Focus:** Find code that serves no purpose

**Locate:**
- Unreachable code (after returns, impossible conditions)
- Unused variables, parameters, functions, classes
- Commented-out code blocks
- Unused imports and dependencies
- Dead event handlers
- Orphaned files (not imported anywhere)
- Zombie code (branches never executed in production)

**Document:**
- Location and type of dead code
- Line count of removable code
- Why it's confirmed dead (not just unused)
- Safe removal verification

---

### Phase 4: Incomplete & Broken Features
**Focus:** Find unfinished work and workarounds

**Search codebase for:**
- `TODO` comments → List what's incomplete and where
- `FIXME` comments → Document known broken behavior
- `HACK` comments → Identify brittle workarounds
- `XXX` comments → Flag dangerous code
- Placeholder/stub implementations
- Missing error handling (`try` without `catch`, unhandled promise rejections)
- Missing validation (no input checks, no bounds validation)
- Half-implemented features (UI without backend, routes without handlers)

**For each finding:**
- Comment location and context
- What's incomplete or broken
- Business impact if triggered
- Completion effort estimate

---

### Phase 5: Technical Debt
**Focus:** Shortcuts and compromises accumulating over time

**Assess:**
- **Design Debt:** Architectural shortcuts, wrong abstractions, missing layers
- **Code Debt:** Quick hacks, skipped refactoring, ignored warnings
- **Test Debt:** Missing tests, low coverage, brittle tests
- **Documentation Debt:** Missing docs, outdated READMEs, undocumented APIs
- **Dependency Debt:** Outdated libraries, security patches needed, deprecated APIs

**Document:**
- Type and location of debt
- When/why it was incurred (if comments reveal this)
- Current cost (build time, bug rate, onboarding difficulty)
- Remediation strategy

---

### Phase 6: Security Vulnerabilities
**Focus:** Exploitable weaknesses

**Check for:**
- **Injection Flaws:**
  - SQL injection (string concatenation in queries)
  - Command injection (unsanitized shell commands)
  - XSS (unescaped user input in HTML)
  - Path traversal (user-controlled file paths)
- **Authentication/Authorization:**
  - Missing authentication checks
  - Broken access control
  - Weak password policies
  - Session management issues
- **Data Exposure:**
  - Sensitive data in logs
  - API keys/secrets in code
  - Unencrypted sensitive data
  - Excessive data in responses
- **Dependency Vulnerabilities:**
  - Known CVEs in dependencies
  - Outdated packages with security issues

**For each vulnerability:**
- CWE/CVE reference if applicable
- Attack vector and exploitability
- Potential impact
- Remediation steps
- **CRITICAL:** Mark as severity: CRITICAL if exploitable

---

### Phase 7: Concurrency Problems
**Focus:** Multi-threading and async issues

**Look for:**
- Race conditions (shared mutable state without synchronization)
- Deadlocks (circular lock dependencies)
- Starvation (thread never getting resources)
- Async/await misuse (missing `await`, promise hell)
- Missing error handling in async code
- Callback hell
- Unhandled promise rejections

**Document:**
- Concurrency issue type
- Conditions that trigger the bug
- Observable symptoms
- Fix strategy (locks, atomic operations, immutability)

---

### Phase 8: Architectural Issues
**Focus:** Structural problems affecting maintainability

**Evaluate:**
- **Coupling:**
  - Tight coupling (changes cascade through modules)
  - Content coupling (direct access to internals)
  - Circular dependencies (A→B→A)
- **Cohesion:**
  - Low cohesion (unrelated functionality in same module)
  - Missing abstractions
  - Wrong responsibility assignment
- **SOLID Violations:**
  - Single Responsibility violations
  - Open/Closed violations
  - Liskov Substitution violations
  - Interface Segregation violations
  - Dependency Inversion violations
- **Layering:**
  - Layer violations (UI calling database directly)
  - Missing separation of concerns

**For each issue:**
- Architectural smell identified
- Modules/components affected
- Consequences for maintenance
- Refactoring approach

---

### Phase 9: Testing & Validation
**Focus:** Quality assurance gaps

**Analyze:**
- Test coverage (% of code covered, untested critical paths)
- Missing test types (no integration tests, no E2E tests)
- Flaky tests (non-deterministic failures)
- Brittle tests (break with unrelated changes)
- Missing edge cases
- No negative testing (error paths untested)
- Missing validation (no input validation, no contract validation)

**Document:**
- Coverage gaps by module
- Critical untested paths
- Test quality issues
- Recommended test additions

---

### Phase 10: Configuration & Dependencies
**Focus:** Environment and external dependency issues

**Check:**
- Hard-coded configuration (DB URLs, API endpoints in code)
- Environment drift (dev/prod differences)
- Missing config validation
- Outdated dependencies (check package.json, requirements.txt, etc.)
- Dependency conflicts
- Unused dependencies
- Missing dependencies (runtime failures)
- Deprecated API usage

**Document:**
- Configuration anti-patterns
- Dependency risks
- Version conflicts
- Update recommendations

---

## WORKING PROTOCOL

### Before Starting
1. **Confirm understanding:** Acknowledge this prompt and ask clarifying questions
2. **Set scope:** Confirm the programming language(s) and framework(s)
3. **Establish baseline:** Count total files to analyze

### During Each Phase
1. **Start phase:** Announce "Starting Phase X: [Name]"
2. **Work incrementally:**
   - Process 5-10 files at a time
   - Update `WRONG.md` after each batch
   - Report progress: "Phase X: Analyzed 15/45 files, found 8 issues"
3. **Pause for review:** After completing each phase, ask: "Phase X complete. Review findings before proceeding to Phase Y?"

### Context Management
- **Monitor tokens:** If you're approaching context limits, summarize findings and start fresh
- **Reference previous work:** Always read `WRONG.md` before continuing to avoid duplication
- **Batch processing:** For large codebases, focus on critical paths first

### Quality Standards
- **Be specific:** Every issue must have a file path and line number
- **Show evidence:** Include code snippets for each finding
- **Assess severity:** Use consistent criteria (Can this cause data loss? Security breach? Production outage?)
- **Be actionable:** Describe what should be done, not just what's wrong

---

## OUTPUT FORMAT FOR EACH ISSUE

Use this template for every issue documented:

```markdown
### #XXX - [Severity: CRITICAL/HIGH/MEDIUM/LOW] Category Name
**Location:** `path/to/file.ext:lineNumber`
**Type:** [Bug Type / Code Smell / Vulnerability / etc.]
**Description:** Clear one-sentence description of the issue
**Impact:** What happens if this isn't fixed? Who is affected?
**Code Snippet:**
```language
[Actual problematic code]
```

**Root Cause:** Why does this issue exist?
**Recommended Fix:** Specific steps to resolve
**Effort:** [Time estimate: hours/days]
**Priority Justification:** Why this severity level?
**Related Issues:** [Links to other related findings if applicable]

```
---

## SEVERITY CRITERIA

**CRITICAL:** Fix immediately
- Security vulnerabilities that are exploitable
- Data loss or corruption risks
- Production crashes affecting users
- Financial impact or regulatory violations

**HIGH:** Fix within days
- Performance issues causing user frustration
- Incorrect business logic
- Maintainability blockers
- High-risk edge cases

**MEDIUM:** Fix within weeks
- Code quality issues making future changes risky
- Missing tests for important paths
- Moderate technical debt

**LOW:** Fix when convenient
- Minor code smells
- Style inconsistencies
- Nice-to-have improvements

---

## GETTING STARTED

**Respond with:**
1. Confirmation you understand the audit structure
2. Questions about scope, priorities, or specifics
3. Ready to begin Phase 1

**Example response:**
> "Understood. I'll conduct a 10-phase comprehensive audit, documenting all findings in `WRONG.md` only. I'll work incrementally to manage context limits and pause after each phase for your review.
>
> Before starting:
> - What languages/frameworks should I focus on?
> - Are there specific modules or directories to prioritize?
> - Should I skip any areas (e.g., vendor/, third-party/, test fixtures)?
>
> Ready to begin Phase 1: Bugs & Defects when you confirm."
```