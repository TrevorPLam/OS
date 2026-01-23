# Quality Gates Configuration

This document defines the quality gates that ensure code quality standards are maintained.

## Merge Policy

**Policy**: `soft_block_with_auto_generated_waivers`

### Description
Quality gate failures create soft blocks that can be bypassed with auto-generated waivers. This allows progress while maintaining visibility into quality issues.

### How It Works
1. CI/CD runs quality checks on every PR
2. If checks fail, a waiver is automatically generated
3. Waiver includes failure details and requires acknowledgment
4. PR can merge after waiver is reviewed and accepted
5. Waiver is tracked for future remediation

### Rationale
- Prevents complete blockage on minor issues
- Maintains awareness of quality debt
- Enables emergency fixes when needed
- Tracks quality issues over time

---

## Coverage Strategy

**Strategy**: `gradual_ratchet`

### Description
Code coverage cannot decrease over time. Each PR must maintain or improve the current coverage percentage.

### Ratcheting Rules
1. Baseline coverage percentage is stored
2. New PRs must meet or exceed baseline
3. Coverage improvements update the baseline
4. Coverage decreases require waiver with plan to recover
5. Baseline resets only with explicit approval

### Implementation
- Baseline stored in `/.repo/metrics/coverage-baseline.txt`
- CI checks coverage on every PR
- Coverage reports generated and archived
- Trends tracked over time

### Exceptions
- Pure refactoring may temporarily reduce coverage (requires waiver)
- Removing dead code may reduce total coverage (acceptable)

---

## Performance Budgets

**Strategy**: `strict_with_fallback_to_default`

### Description
Performance budgets are strictly enforced when defined. If no budget exists for a metric, default acceptable ranges apply.

### Budget Categories
1. **Page Load Time**: Max 3 seconds for initial load
2. **Time to Interactive (TTI)**: Max 5 seconds
3. **Bundle Size**: 
   - JavaScript: Max 200KB gzipped
   - CSS: Max 50KB gzipped
4. **API Response Time**: Max 500ms for p95
5. **Database Query Time**: Max 100ms for p95

### Enforcement
- Lighthouse CI runs on every frontend PR
- Performance tests run on every backend PR
- Budgets defined in `lighthouserc.cjs` and `performance-budgets.json`
- Violations generate waiver requiring optimization plan

### Fallback to Default
If specific budget not defined:
- Use default values above
- Warning (not failure) on first violation
- Establishes new budget at current level + 10% headroom

---

## Zero Warnings Policy

**Policy**: Zero compiler/linter warnings allowed

### Description
Warnings are treated as errors. Code must compile and lint cleanly.

### Enforcement
- TypeScript: `"strict": true` in tsconfig.json
- ESLint: All warnings promoted to errors
- Python: flake8, mypy, pylint with strict settings
- CI fails on any warnings

### Rationale
- Prevents warning fatigue
- Forces addressing issues immediately
- Keeps codebase clean
- Warnings often indicate real problems

### Exceptions
- Third-party library warnings (must be documented)
- Deprecated API warnings during migration period (temporary waiver)

---

## PR Size Policy

**Policy**: `no_limits` (but small PRs encouraged)

### Description
No hard limits on PR size, but small incremental PRs are strongly encouraged per P3 principle.

### Guidelines
- Aim for PRs under 400 lines of changes
- Split large features into multiple PRs
- Use feature flags for partial implementations
- Incremental PRs enable faster review and feedback

### When Large PRs Are Acceptable
- Database migrations
- Generated code (e.g., OpenAPI clients)
- Large refactoring with automated tools
- Third-party code integration

### Large PR Requirements
PRs over 1000 lines should include:
- Justification for size
- Clear description of sections
- Suggested review order
- Extra review time allocation

---

## Governance Verify Checks

**Configuration**: Run all governance verification checks

### Checks Included
1. **Authority Chain Compliance**: Files respect Manifest > Agents > Policy hierarchy
2. **Filepath Requirements**: All artifacts include explicit filepaths
3. **Plain English**: Documentation is understandable
4. **Boundary Compliance**: Imports respect architectural boundaries
5. **Security Baseline**: Security policies are followed
6. **Principle Adherence**: Code follows P3-P25 principles
7. **Waiver Tracking**: Waivers are properly documented
8. **HITL Completion**: HITL items are resolved before merge

### Check Execution
- Automated checks run in CI/CD
- Manual checks during code review
- Results tracked in PR status checks
- Failures generate waivers or block merge

### Check Definitions
Detailed check specifications in:
- `/.repo/automation/governance-checks/` directory
- Each check has its own validation script
- Checks are version controlled and tested

---

## Auto-Generated Waivers

### When Waivers Are Generated
Waivers are automatically generated for:
1. Coverage ratchet failures
2. Performance budget violations
3. Linter/compiler warnings (if critical path)
4. Boundary violations
5. Missing documentation
6. Test failures (with HITL approval)

### Waiver Contents
Auto-generated waivers include:
- Failure type and details
- Affected files and line numbers
- Current vs. expected values
- Generated timestamp
- Expiration date (7-30 days based on severity)
- Owner (PR author by default)
- Remediation suggestions

### Waiver Location
- Active: `/waivers/active/`
- Resolved: `/waivers/historical/`
- Template: `/.repo/templates/WAIVER.md`

### Waiver Lifecycle
1. **Generated**: Auto-created on quality gate failure
2. **Reviewed**: PR author acknowledges and accepts
3. **Active**: PR merges with active waiver
4. **Tracked**: Waiver tracked in issue tracker
5. **Resolved**: Follow-up PR fixes issue
6. **Archived**: Waiver moved to historical with resolution notes

---

## Lifecycle Tracking

**Configuration**: `full_history`

### What Is Tracked
- All quality gate results (pass/fail)
- All waivers (generated, accepted, resolved)
- All coverage percentages over time
- All performance metrics over time
- All boundary violations and resolutions

### Historical Data Location
- Coverage: `/.repo/metrics/coverage-history/`
- Performance: `/.repo/metrics/performance-history/`
- Waivers: `/waivers/historical/`
- Violations: `/.repo/metrics/violations-history/`

### History Retention
- Keep all data indefinitely (storage is cheap)
- Monthly aggregations for trends
- Quarterly reports generated automatically
- Historical data informs future decisions

### Access
- History accessible via CLI tools
- Dashboard shows trends and current status
- Reports generated on demand
- Auditing supported for compliance

---

## Quality Gate Execution Order

Quality gates run in this order during CI/CD:

1. **Linting**: Code style and syntax
2. **Type Checking**: TypeScript/mypy validation
3. **Unit Tests**: Fast, isolated tests
4. **Integration Tests**: Component interaction tests
5. **Coverage Check**: Verify coverage meets ratchet
6. **Boundary Check**: Validate architectural boundaries
7. **Security Scan**: Dependency and code security
8. **Performance Tests**: Load time, response time
9. **Governance Checks**: Policy compliance
10. **Build**: Final production build

### Early Termination
- Gates run in order
- Failure in early gate stops execution (fail fast)
- Exception: Security scans always run (even if tests fail)

---

## Waiver Review Process

### Who Reviews Waivers
- Minor: PR author self-approves with acknowledgment
- Moderate: Team lead reviews and approves
- Major: Architecture/security lead reviews and approves
- Critical: All stakeholders must approve

### Waiver Severity Levels
- **Minor**: Linting, formatting, minor documentation
- **Moderate**: Coverage decrease, performance regression
- **Major**: Boundary violation, security warning
- **Critical**: Security vulnerability, data loss risk

### Review SLA
- Minor: Immediate (self-approved)
- Moderate: Within 24 hours
- Major: Within 8 hours
- Critical: Within 1 hour (urgent escalation)

---

## Metrics Collection

### Automated Metrics
Collected automatically on every PR:
- Lines of code (LoC)
- Test coverage percentage
- Cyclomatic complexity
- Number of tests
- Build time
- Test execution time
- Bundle size
- Number of dependencies

### Manual Metrics
Collected periodically:
- Code review time
- Time to merge
- Waiver resolution time
- Incident count
- Rollback frequency

### Metrics Dashboard
- Located at: `/.repo/metrics/dashboard.md`
- Updated automatically post-merge
- Trends visualized in CI/CD
- Alerts for concerning trends

---

## Continuous Improvement

### Monthly Review
- Review all active waivers
- Analyze quality trends
- Adjust baselines if needed
- Update quality gates if too strict/loose

### Quarterly Planning
- Set quality improvement goals
- Plan technical debt reduction
- Update performance budgets
- Review and update policies

---

## Related Documents

- **Governance**: `/.repo/GOVERNANCE.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md`
- **Security Baseline**: `/.repo/policy/SECURITY_BASELINE.md`
- **Boundaries**: `/.repo/policy/BOUNDARIES.md`
- **Waiver Template**: `/.repo/templates/WAIVER.md`
