# Definition of Done

**Status**: Active (ASSESS-R1.7)
**Last Updated**: December 31, 2025
**Owner**: Engineering Team

---

## Purpose

This document defines the criteria that must be met before a feature, bug fix, or task can be considered "done" and ready for production deployment. This ensures consistent quality, maintainability, and compliance across all code changes.

---

## Universal Criteria (All Changes)

Every code change MUST meet ALL of the following criteria:

### 1. Code Quality

- [ ] **Code is reviewed** - At least one peer review with approval
- [ ] **Follows coding standards** - Adheres to project style guide and linting rules
- [ ] **No TODOs introduced** - All TODO comments must be tracked as issues (except with explicit approval)
- [ ] **No commented-out code** - Remove dead code instead of commenting it out
- [ ] **No security vulnerabilities** - SAST checks pass, no known security issues
- [ ] **No unnecessary complexity** - Code is as simple as possible for the requirements

### 2. Testing

- [ ] **All tests pass** - CI/CD pipeline is green (unit, integration, security tests)
- [ ] **New code is tested** - Adequate test coverage for new functionality (minimum 70% coverage maintained)
- [ ] **Edge cases covered** - Known edge cases from docs/23 (EDGE_CASES_CATALOG) are tested
- [ ] **No test non-determinism** - Tests produce consistent results across runs
- [ ] **Manual testing complete** - Feature tested in development environment

### 3. Documentation

- [ ] **README updated** - If setup/installation changed
- [ ] **API docs updated** - If API endpoints added/changed
- [ ] **Code documented** - Complex logic has explanatory comments
- [ ] **Migration guide provided** - If breaking changes introduced
- [ ] **Changelog updated** - Entry added to CHANGELOG.md

### 4. Compliance & Security

- [ ] **Tenant isolation verified** - All queries are firm-scoped (no global access)
- [ ] **Authorization enforced** - Server-side permission checks on all endpoints
- [ ] **Input validation** - All external inputs validated (URLs, files, email, JSON)
- [ ] **Audit events logged** - Critical operations create audit trail
- [ ] **PII handling compliant** - Follows DATA_GOVERNANCE (docs/7) rules
- [ ] **Constitution compliance** - Adheres to docs/codingconstitution.md

### 5. Database Changes

- [ ] **Migrations tested** - Tested against production-like data volume
- [ ] **Migrations reversible** - Rollback plan documented
- [ ] **No data loss risk** - Data migration preserves existing records
- [ ] **Indexes added** - Performance indexes for new queries
- [ ] **Foreign keys enforced** - Referential integrity constraints in place

### 6. Deployment

- [ ] **CI/CD passes** - All automated checks green
- [ ] **Deployment plan documented** - Steps to deploy documented
- [ ] **Rollback plan tested** - Rollback procedure verified
- [ ] **Feature flags used** - For risky changes (if applicable)
- [ ] **Monitoring configured** - Alerts/metrics for new functionality

---

## Feature-Specific Criteria

Depending on the type of work, additional criteria may apply:

### New Features

- [ ] **Acceptance criteria met** - All requirements from issue/spec satisfied
- [ ] **User story tested** - End-to-end user flow verified
- [ ] **Error handling** - Graceful degradation for failure cases
- [ ] **Performance acceptable** - Meets performance requirements (if specified)
- [ ] **Accessibility verified** - UI changes meet accessibility standards
- [ ] **Cross-browser tested** - Works in supported browsers (if UI change)

### Bug Fixes

- [ ] **Root cause identified** - Underlying issue understood and documented
- [ ] **Regression test added** - Test prevents bug from recurring
- [ ] **Related bugs checked** - Similar issues in codebase reviewed
- [ ] **Fix verified** - Bug reporter confirms fix (if available)

### API Changes

- [ ] **Versioning handled** - Breaking changes use new API version
- [ ] **Backward compatibility** - Deprecated fields supported for 1 version cycle
- [ ] **OpenAPI schema updated** - API spec reflects changes
- [ ] **Client libraries updated** - SDKs updated if maintained
- [ ] **Deprecation notice** - If deprecating, notice added to docs

### Database Schema Changes

- [ ] **Zero-downtime migration** - Can be deployed without downtime
- [ ] **Data integrity verified** - Constraints prevent invalid data
- [ ] **Performance tested** - Migration tested on large dataset
- [ ] **Unique constraints named** - All constraints have explicit names
- [ ] **Ledger immutability** - Billing ledger entries remain immutable

### Security Changes

- [ ] **Threat model updated** - docs/THREAT_MODEL.md reflects changes
- [ ] **Security review complete** - Security team approved (if available)
- [ ] **Penetration tested** - Security changes tested for vulnerabilities
- [ ] **Security documentation** - Security implications documented

---

## Non-Blocking Criteria (Recommended)

These are strongly recommended but may be deferred with explicit justification:

- [ ] **Performance optimized** - Code is reasonably performant
- [ ] **Refactoring complete** - Surrounding code cleaned up (if touched)
- [ ] **Type hints added** - Python type annotations for new functions
- [ ] **Integration tests** - End-to-end scenarios tested
- [ ] **Load tested** - Performance under load verified

---

## Exceptions & Waivers

In rare cases, criteria may be waived with:
1. **Explicit approval** from tech lead or architect
2. **Documentation** of why waived and remediation plan
3. **Follow-up task** created to address waived criteria

Common valid exceptions:
- Emergency hotfixes (may skip some documentation)
- Prototype/spike work (clearly marked as non-production)
- External dependency blockers (documented and tracked)

---

## Verification Checklist

Use this checklist when reviewing PRs:

```markdown
## Definition of Done Checklist

### Code Quality
- [ ] Code reviewed and approved
- [ ] Follows coding standards
- [ ] No untracked TODOs
- [ ] No security vulnerabilities

### Testing
- [ ] All tests pass
- [ ] New code tested (70%+ coverage)
- [ ] Edge cases covered
- [ ] Manual testing complete

### Documentation
- [ ] Docs updated (README, API, changelog)
- [ ] Complex logic documented
- [ ] Migration guide (if needed)

### Compliance
- [ ] Tenant isolation verified
- [ ] Authorization enforced
- [ ] Input validation complete
- [ ] Audit events logged
- [ ] Constitution compliant

### Database (if applicable)
- [ ] Migrations tested and reversible
- [ ] Indexes added
- [ ] Foreign keys enforced

### Deployment
- [ ] CI/CD passes
- [ ] Deployment/rollback plan documented
- [ ] Monitoring configured
```

---

## References

- **Coding Constitution**: [docs/codingconstitution.md](./codingconstitution.md)
- **Edge Cases Catalog**: [docs/23 - EDGE_CASES_CATALOG.md](./docs/23)
- **Data Governance**: [docs/7 - DATA_GOVERNANCE.md](./docs/7)
- **Security Model**: [docs/24 - SECURITY_MODEL.md](./docs/24)
- **Threat Model**: [THREAT_MODEL.md](./THREAT_MODEL.md)
- **Rollback Procedures**: [docs/runbooks/ROLLBACK.md](./runbooks/ROLLBACK.md)

---

## Maintenance

This document should be reviewed and updated:
- **Quarterly**: Review and refine criteria
- **After incidents**: Add new criteria based on lessons learned
- **When patterns emerge**: Document recurring issues as criteria

**Next Review**: March 31, 2026
