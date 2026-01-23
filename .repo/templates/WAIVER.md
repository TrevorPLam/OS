# Waiver: [Short Description]

**Waiver ID**: WAIVER-YYYY-MM-DD-description  
**Created**: YYYY-MM-DD  
**Author**: [Agent or Person]  
**PR**: #XXX  
**Status**: Pending | Approved | Rejected | Expired

## Quality Gate Failed

**Gate**: Coverage | Performance | Boundary | Linting | Security  
**Expected**: [What should have passed]  
**Actual**: [What actually happened]

Example:
**Gate**: Coverage Ratchet  
**Expected**: Coverage ≥ 85%  
**Actual**: Coverage = 83% (decreased by 2%)

## Failure Details

**Location**: [File paths where failure occurred]

Example:
**Location**:
- `/src/migration/data-migration-2024-01.ts` - No tests (migration script)
- Overall coverage: 85% → 83%

## Reason for Waiver

[Clear explanation of why this failure should be waived]

Example:
This is a one-time data migration script that:
- Will only run once in production
- Will be archived after execution
- Has been manually tested in staging
- Low test value (simple SQL queries)
- Risk: Low (can rollback migration)

## Remediation Plan

[How and when this will be fixed]

**Actions**:
- [ ] Action 1
- [ ] Action 2
- [ ] Action 3

**Target Date**: YYYY-MM-DD

Example:
**Actions**:
- [ ] Execute migration in production
- [ ] Verify migration success
- [ ] Archive migration script to `/archive/migrations/`
- [ ] Remove from active codebase

**Target Date**: 2024-02-15

## Risk Assessment

**Risk Level**: 🟢 Low | 🟡 Medium | 🔴 High

**Impact**: [What could go wrong]

**Mitigation**: [How risk is reduced]

Example:
**Risk Level**: 🟢 Low

**Impact**: Migration could fail or corrupt data

**Mitigation**:
- Tested in staging with production-like data
- Database backup taken before migration
- Migration is reversible (rollback script exists)
- Can restore from backup if needed

## Evidence

[Proof that this is safe to waive]

Example:
- Staging test results: [link to logs]
- Manual verification: [screenshots]
- Rollback tested: [log output]
- Team approval: [Slack thread]

## Expiration

**Expires On**: YYYY-MM-DD  
**Auto-Archive**: Yes | No

[Waiver is temporary and must expire]

Example:
**Expires On**: 2024-02-15 (30 days)  
**Auto-Archive**: Yes (after migration completes)

## Approval

**Required Approver**: [Role or Person]  
**Approved By**: [Name] (if approved)  
**Approved Date**: YYYY-MM-DD (if approved)  
**Rejection Reason**: [If rejected]

Example:
**Required Approver**: Tech Lead  
**Approved By**: tech-lead@example.com  
**Approved Date**: 2024-01-16

## Follow-Up

**Tracking Issue**: TASK-XXX (if applicable)  
**Related Waivers**: [Links to related waivers]

## Related Documents

- PR: #XXX
- Task: TASK-XXX
- ADR: ADR-XXX (if applicable)

---

## Example Waiver

# Waiver: Coverage Decrease for Data Migration

**Waiver ID**: WAIVER-2024-01-15-migration-coverage  
**Created**: 2024-01-15  
**Author**: @agent  
**PR**: #456  
**Status**: Approved

## Quality Gate Failed

**Gate**: Coverage Ratchet  
**Expected**: Coverage ≥ 85%  
**Actual**: Coverage = 83%

## Failure Details

**Location**:
- `/src/migration/add-email-verified-column.ts` - Migration script (no tests)
- `/src/migration/rollback-email-verified.ts` - Rollback script (no tests)

**Impact on Coverage**:
- Previous: 2,450 lines total, 2,082 covered (85%)
- Current: 2,550 lines total, 2,118 covered (83%)
- New lines: 100 (migration scripts)
- Covered new lines: 36 (36%)

## Reason for Waiver

This is a one-time database migration that:
- Adds `email_verified` boolean column to `users` table
- Runs once in production, then archived
- Simple SQL queries with low complexity
- Manually tested extensively in staging
- Rollback script exists and tested

Testing these migration scripts provides minimal value because:
- They're one-time operations
- SQL is straightforward
- Risk is managed through staging testing and rollback
- Will be archived after execution

## Remediation Plan

**Actions**:
- [x] Test migration in staging (completed)
- [x] Test rollback in staging (completed)
- [ ] Execute migration in production
- [ ] Verify all users have email_verified field
- [ ] Archive migration scripts
- [ ] Coverage will return to 85%+ after archiving

**Target Date**: 2024-02-01 (migration) and 2024-02-15 (archive)

## Risk Assessment

**Risk Level**: 🟢 Low

**Impact**: Migration could fail or take too long

**Mitigation**:
- ✅ Tested in staging with 50k test users (took 3 seconds)
- ✅ Rollback script tested and verified
- ✅ Database backup scheduled before migration
- ✅ Migration runs in transaction (atomic)
- ✅ Can rollback within 30 seconds if issues

## Evidence

**Staging Test Results**:
```sql
-- Migration test
✓ Added email_verified column
✓ Set existing users to false
✓ New default: false
✓ Time: 2.8 seconds (50k rows)

-- Rollback test
✓ Removed email_verified column
✓ No data loss
✓ Time: 1.2 seconds
```

**Manual Verification**:
- Staging DB inspected: All users have email_verified field ✓
- Application works with new field ✓
- Queries performant (no index needed for now) ✓

## Expiration

**Expires On**: 2024-02-15 (30 days)  
**Auto-Archive**: Yes (when scripts moved to archive/)

## Approval

**Required Approver**: Tech Lead  
**Approved By**: tech-lead@example.com  
**Approved Date**: 2024-01-16  
**Rationale**: Low risk, well-tested, temporary coverage decrease

## Follow-Up

**Tracking Issue**: TASK-234 (Archive migration after execution)

## Related Documents

- PR: #456
- Task: TASK-230 (Add email verification feature)
- Migration logs: /logs/migration-2024-01-15.log
