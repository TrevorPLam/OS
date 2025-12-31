# Definition of Done (ASSESS-R1.7)

**Status:** Active  
**Last Updated:** December 2025

## Overview

This document defines the criteria that must be met before a feature, bug fix, or change is considered complete and ready for deployment.

## Pull Request Checklist

Before a PR can be merged, all of the following must be true:

### ✅ Code Quality

- [ ] All tests pass (unit, integration, security)
- [ ] Code coverage maintained or improved (minimum 70%)
- [ ] No linter errors or warnings
- [ ] Code follows project style guide
- [ ] All TODOs resolved or documented with issue numbers
- [ ] No commented-out code (unless with explanation)

### ✅ Functionality

- [ ] Feature works as specified in requirements
- [ ] Edge cases handled appropriately
- [ ] Error handling implemented
- [ ] User-facing changes tested manually
- [ ] Backward compatibility maintained (or migration plan documented)

### ✅ Security

- [ ] No security vulnerabilities introduced
- [ ] Tenant isolation verified (firm scoping)
- [ ] Input validation implemented
- [ ] Authorization checks in place
- [ ] Sensitive data not logged
- [ ] Security tests added for new features

### ✅ Database

- [ ] Migrations created and tested
- [ ] Migration rollback tested
- [ ] No data loss in migration
- [ ] Indexes added for new queries
- [ ] Foreign key constraints properly defined

### ✅ API Changes

- [ ] API versioning considered (if breaking change, new version required)
- [ ] API documentation updated
- [ ] OpenAPI schema updated
- [ ] Deprecation notices added (if applicable)
- [ ] Error responses follow error model (ASSESS-I5.4)

### ✅ Documentation

- [ ] Code comments added for complex logic
- [ ] Docstrings updated for new functions/classes
- [ ] README/docs updated if user-facing
- [ ] Changelog entry added
- [ ] Migration guide created (if breaking change)

### ✅ Testing

- [ ] Unit tests written and passing
- [ ] Integration tests written (if applicable)
- [ ] Security tests added (if applicable)
- [ ] Edge case tests added
- [ ] Performance tests added (if applicable)
- [ ] Tests run in Postgres (not SQLite)

### ✅ Review

- [ ] Code reviewed by at least one other developer
- [ ] Security review completed (for security-sensitive changes)
- [ ] Architecture review completed (for architectural changes)
- [ ] All review comments addressed

### ✅ Deployment

- [ ] CI/CD pipeline passes
- [ ] Database migrations tested in staging
- [ ] Rollback plan documented
- [ ] Feature flags configured (if applicable)
- [ ] Monitoring/alerting updated (if applicable)

## Acceptance Criteria

Every feature must have clear acceptance criteria defined before implementation:

1. **Functional Requirements**
   - What the feature does
   - User workflows
   - Success scenarios

2. **Non-Functional Requirements**
   - Performance targets
   - Security requirements
   - Compliance requirements

3. **Edge Cases**
   - Error scenarios
   - Boundary conditions
   - Failure modes

4. **Testing Requirements**
   - Test scenarios
   - Coverage requirements
   - Performance benchmarks

## Examples

### Feature Implementation

**Example:** Add new API endpoint

✅ **Done:**
- Endpoint implemented with proper versioning
- Tests written and passing
- API documentation updated
- Error handling implemented
- Security checks in place
- Migration created (if needed)

❌ **Not Done:**
- Endpoint works but no tests
- Documentation missing
- Error handling incomplete

### Bug Fix

**Example:** Fix IDOR vulnerability

✅ **Done:**
- Vulnerability fixed
- Regression tests added
- Security review completed
- All similar patterns checked
- Documentation updated

❌ **Not Done:**
- Fix applied but no tests
- Similar vulnerabilities not checked
- Security review pending

## Exceptions

### Emergency Fixes

For critical security or production issues:
- Minimum: Fix + test + security review
- Documentation can follow in separate PR
- Must be reviewed by security team

### Experimental Features

For experimental/prototype features:
- Clearly marked as experimental
- Documentation notes limitations
- Can skip some tests (with justification)
- Must be removed or completed within 1 sprint

## Quality Gates

### Pre-Merge

- All automated checks pass
- Code review approved
- Tests passing

### Pre-Deploy

- Staging deployment successful
- Smoke tests passing
- Rollback plan verified

### Post-Deploy

- Production monitoring shows no errors
- Feature verified in production
- Documentation published

## References

- **ASSESS-R1.7:** Definition of done establishment
- [Contributing Guide](../CONTRIBUTING.md)
- [Style Guide](./STYLE_GUIDE.md)
- [Security Policy](../SECURITY.md)