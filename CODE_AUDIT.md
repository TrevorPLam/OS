# CODE_AUDIT.md — Code Audit Pipeline

Document Type: Governance
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Canonical
Dependencies: CODEBASECONSTITUTION.md, TODO.md, DOCS_ROOT.md

## Purpose

This document defines the code audit pipeline for the repository. It establishes what must be checked, when, and how violations are handled.

## Audit Pipeline

### Pre-Commit Checks

All changes must pass:

1. **Linting** - Code style and formatting
   - Tool: `make lint` (ruff + black)
   - Auto-fix: `make format`
   - No exceptions without explicit justification

2. **Type Checking** (if applicable)
   - Tool: mypy or equivalent
   - Enforcement level: defined in pyproject.toml

3. **Security Scanning** 
   - Dependency vulnerabilities
   - Code security patterns
   - Secrets detection

### Pre-Merge Checks

All PRs must pass:

1. **Tests**
   - Command: `make test`
   - Coverage requirements: as defined in CI
   - All tests must pass

2. **Build Verification**
   - Docker build must succeed
   - No build warnings on critical paths

3. **Documentation Validation**
   - Links must resolve
   - API specs must match implementation
   - OpenAPI schema must be current

4. **Security Gates**
   - No hardcoded secrets
   - RLS policies on tenant-scoped models
   - Permission checks on endpoints
   - Input validation and sanitization

### Post-Merge Audits

Periodic reviews:

1. **Dependency Health**
   - Outdated dependencies
   - Security advisories
   - License compliance

2. **Documentation Drift**
   - Docs match implementation
   - No orphaned docs
   - No task leakage in docs

3. **Architectural Compliance**
   - No boundary violations
   - Module organization consistent
   - No circular dependencies

## Audit Execution

### Manual Audits

When to run:
- Before major releases
- After significant refactoring
- When requested via TODO task

How to run:
1. Review CODEBASECONSTITUTION.md for current rules
2. Run all automated checks
3. Review architectural boundaries
4. Check documentation accuracy
5. Document findings in TODO.md

### Automated Audits

Continuous:
- CI/CD pipeline on every PR
- Dependency scanning (daily/weekly)
- Security scanning (on commit)

## Violation Handling

### Severity Levels

1. **Critical** - Security vulnerability, data loss risk
   - Action: Block merge, immediate fix required
   - Escalation: Document in SECURITY.md format

2. **High** - Constitutional violation, broken build
   - Action: Block merge, fix required before merge
   - Escalation: Required for merge approval

3. **Medium** - Style violation, missing tests
   - Action: Fix in PR or create follow-up task
   - Grace: Can merge with justified exception

4. **Low** - Documentation gap, minor style inconsistency
   - Action: Create TODO task for cleanup
   - Grace: Does not block merge

### Exception Process

If audit fails but merge is necessary:

1. Document exception in PR description
2. Include:
   - Reason for exception
   - Impact assessment
   - Remediation plan with date
3. Link to TODO task for remediation
4. Require additional approval

## Integration with TODO.md

All audit findings must be tracked:

- Critical/High: Create task immediately with T-### ID
- Medium: Create task in next sprint
- Low: Batch into cleanup task

Format in TODO:
```
## T-XXX: [Audit] Description
- Type: Code Audit Finding
- Severity: Critical/High/Medium/Low
- Source: [Audit Type] on [Date]
- Context: Link to PR/commit/file
- Acceptance: [Specific fix criteria]
```

## Audit Schedule

- **Daily**: CI checks on all commits/PRs
- **Weekly**: Dependency vulnerability scan
- **Monthly**: Documentation drift review
- **Quarterly**: Full architectural compliance audit
- **Release**: Complete pre-release audit

## References

- CI Pipeline: `.github/workflows/ci.yml`
- Linting Config: `pyproject.toml`
- Test Config: `pytest.ini`
- Security Baseline: `docs/SECURITY_BASELINE.md`
- Constitution: `CODEBASECONSTITUTION.md`

## Version History

- 1.0.0 (2026-01-03): Initial version defining audit pipeline
