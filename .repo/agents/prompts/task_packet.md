# Task Packet Template

Task packets define work before it begins. They enforce planning and provide clear success criteria.

## When Required

Task packets are required for:
- All non-trivial changes (>50 lines)
- New features
- Bug fixes with complex changes
- Refactoring across multiple files
- Security changes
- Schema changes
- API changes
- Any change requiring HITL

## Template

```markdown
# Task Packet: [Brief Title]

**Task ID**: TASK-XXX  
**Type**: Feature | Bugfix | Refactor | Docs | Security | Performance  
**Priority**: P0 | P1 | P2 | P3  
**Status**: Planning | In Progress | Blocked | Complete  
**Created**: YYYY-MM-DD  
**Owner**: [Agent or Person]

## Goal

[Clear statement of what needs to be accomplished in 1-2 sentences]

Example: Add password reset functionality that allows users to securely reset forgotten passwords via email.

## Non-Goals

[Explicitly state what is NOT included in this task]

Example:
- Social login (separate task)
- Password strength requirements (already implemented)
- Remember me functionality (future enhancement)

## Acceptance Criteria

[Specific, testable conditions that define "done"]

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

Example:
- [ ] User can request password reset from login page
- [ ] Reset email sent with unique token
- [ ] Token expires after 1 hour
- [ ] User can set new password with valid token
- [ ] All tests pass with ≥85% coverage
- [ ] Security review approved
- [ ] Documentation updated

## Approach

[High-level technical approach]

Example:
1. Create reset request endpoint: POST /auth/reset-request
2. Generate unique token, store with expiration
3. Send email with reset link
4. Create reset confirmation endpoint: POST /auth/reset-confirm
5. Validate token, update password
6. Invalidate all existing sessions

## Files Touched

[List all files to be created or modified - REQUIRED for traceability]

**Files to Create**:
- `/path/to/new/file1.ts` - Description
- `/path/to/new/file2.ts` - Description

**Files to Modify**:
- `/path/to/existing/file1.ts` - What will change
- `/path/to/existing/file2.ts` - What will change

Example:
**Files to Create**:
- `/src/auth/reset/domain/resetService.ts` - Reset logic
- `/src/auth/reset/data/resetRepository.ts` - Reset data access
- `/src/auth/reset/ui/ResetForm.tsx` - Reset UI
- `/tests/auth/reset.test.ts` - Tests

**Files to Modify**:
- `/src/auth/login/ui/LoginPage.tsx` - Add reset link
- `/docs/auth/README.md` - Add reset documentation

## Verification Plan

[Commands to verify the change works]

Example:
```bash
# Linting
npm run lint -- src/auth/reset/

# Type checking
npm run type-check

# Unit tests
npm test -- tests/auth/reset.test.ts

# Integration tests
npm run test:integration -- auth

# Manual verification
1. Navigate to /login
2. Click "Forgot Password"
3. Enter email, click Send
4. Check email inbox for reset link
5. Click link, set new password
6. Verify can log in with new password
```

## Risks

[Potential problems and mitigation strategies]

Example:
- **Risk**: Email service failure prevents reset
  - **Mitigation**: Add retry logic, log failures, provide manual reset option
- **Risk**: Token collision (unlikely but possible)
  - **Mitigation**: Use crypto.randomBytes(32) for uniqueness
- **Risk**: User receives multiple reset emails (spam)
  - **Mitigation**: Rate limit: 3 requests per hour per email

## Rollback Plan

[How to undo this change if it causes problems]

Example:
1. Revert deployment: `git revert <commit-sha> && deploy`
2. Or feature flag: Set `ENABLE_PASSWORD_RESET=false` in env
3. No data loss: Reset requests stored but ignored
4. Users fall back to: Contact support for password reset

## HITL Requirements

[What requires human review/approval]

Example:
- **Email Service Integration**: Requires approval (external system)
  - **HITL Item**: HITL-2024-01-15-email-service.md
- **Security Review**: Required for auth changes
  - **Reviewer**: security@example.com
- **Token Expiration Policy**: Needs confirmation
  - **Question**: 1 hour or 24 hours?

## Dependencies

[What must be completed first]

Example:
- TASK-120: Email service configured (must be complete)
- TASK-115: User model has email field (complete ✓)

## Notes

[Additional context, links, references]

Example:
- Similar implementation: `/src/auth/verification/` (email verification)
- Security reference: OWASP Password Reset Cheat Sheet
- Design mockup: Figma link
- ADR-042: JWT authentication (context)

## Changelog

[Track updates to this task packet]

- 2024-01-15: Created
- 2024-01-16: Added rate limiting to risks
- 2024-01-17: Clarified email service dependency
```

## Best Practices

1. **Update During Work**: Task packets are living documents
2. **Be Specific**: "Add tests" → "Add tests for happy path, error cases, edge cases"
3. **Use Filepaths**: Always include absolute paths from repo root
4. **Link HITL**: Reference HITL items by filename
5. **Show Evidence**: In verification, show actual command output
6. **Think Rollback**: Every change should be reversible

## Examples by Type

### Feature Task Packet
```markdown
# Task Packet: Add Dark Mode Toggle

**Type**: Feature
**Priority**: P2

## Goal
Add dark mode toggle to user settings that persists preference.

## Acceptance Criteria
- [ ] Toggle in settings page
- [ ] Preference saved to user profile
- [ ] Applied site-wide on all pages
- [ ] Default: system preference
```

### Bugfix Task Packet
```markdown
# Task Packet: Fix Login Form Validation

**Type**: Bugfix
**Priority**: P0

## Goal
Fix bug where empty email field passes validation.

## Approach
Add null/empty check before regex validation in validateEmail().

## Files Touched
**Files to Modify**:
- `/src/auth/login/domain/validation.ts` - Add empty check

## Verification Plan
- Test with empty email → should fail
- Test with valid email → should pass
- Run existing tests → should all pass
```

## Related Documents

- **Agents Framework**: `/.repo/agents/AGENTS.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md` (P6: Evidence, P8: Read Repo First)
- **PR Template**: `/.repo/templates/PR_TEMPLATE.md`
