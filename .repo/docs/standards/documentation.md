# Documentation Standards

This document defines standards for documentation, location anchors, navigation aids, and iteration accelerators.

## Location Anchors

Location anchors help developers quickly locate and reference code.

### File Headers Required

Every source file should have a header with:

```typescript
/**
 * File: src/auth/login/domain/authService.ts
 * Purpose: Handles authentication logic and token management
 * Domain: Authentication
 * Feature: Login
 * Layer: Domain
 */
```

### Filepaths in Pull Requests

Every PR description must include explicit filepaths for changed files:

```markdown
## Files Changed

- `src/auth/login/ui/LoginForm.tsx` - Updated form validation
- `src/auth/login/domain/authService.ts` - Added token refresh logic
- `tests/auth/login.test.ts` - Added new test cases
```

### Filepaths in Task Packets

Task descriptions must list files to be created or modified:

```markdown
## Task: Implement password reset

**Files to Modify:**
- `src/auth/reset/ui/ResetForm.tsx`
- `src/auth/reset/domain/resetService.ts`
- `src/auth/reset/data/resetRepository.ts`

**Files to Create:**
- `src/auth/reset/ui/ResetConfirmation.tsx`
- `tests/auth/reset.test.ts`
```

### Filepaths in Commentary

Code comments referencing other files should use full paths:

```typescript
// See src/auth/login/domain/authService.ts for token refresh logic
// Related: src/platform/api/client.ts handles HTTP interceptors
```

### Filepaths in ADRs and Waivers

ADRs and waivers must reference specific files:

```markdown
## ADR-042: Use JWT for Authentication

**Affected Files:**
- `src/auth/login/domain/authService.ts` - Token generation
- `src/auth/middleware/authMiddleware.ts` - Token validation
- `src/platform/api/client.ts` - Token interceptor
```

---

## Navigation Aids

Navigation aids help developers understand the codebase structure.

### Domain Index Files

Each domain should have an index file:

```typescript
// src/auth/index.ts

/**
 * Authentication Domain
 * 
 * Features:
 * - Login: User authentication
 * - Registration: New user signup
 * - Password Reset: Forgotten password recovery
 * - MFA: Multi-factor authentication
 */

export * from './login';
export * from './registration';
export * from './reset';
export * from './mfa';
```

### Feature Index Files

Each feature should have an index file:

```typescript
// src/auth/login/index.ts

/**
 * Login Feature
 * 
 * Responsibilities:
 * - User credential validation
 * - JWT token generation
 * - Session management
 * 
 * Dependencies:
 * - Platform API client
 * - User repository
 */

export { LoginForm } from './ui/LoginForm';
export { authService } from './domain/authService';
export { authRepository } from './data/authRepository';
```

### Directory READMEs with Boundaries

Each major directory should have a README explaining its purpose and boundaries:

```markdown
# Authentication Domain

## Purpose
Handles all user authentication and authorization logic.

## Features
- **Login**: User authentication with email/password
- **Registration**: New user signup and verification
- **Password Reset**: Forgotten password recovery flow
- **MFA**: Multi-factor authentication (future)

## Boundaries
- **Allowed Imports**: Platform utilities only
- **Forbidden Imports**: Other domains (billing, inventory)
- **Exports**: Public API through index.ts

## Related Documents
- ADR-042: JWT Authentication
- Security Baseline: /.repo/policy/SECURITY_BASELINE.md
```

### Full Path Imports (Optional)

Use full paths for clarity (optional but encouraged):

```typescript
// Clear where this comes from
import { formatCurrency } from '@/platform/utils/format';

// Also acceptable
import { formatCurrency } from '@/platform/utils/format';
```

---

## Iteration Accelerators

Accelerators help developers work faster and more safely.

### Pattern Reference Required

When implementing common patterns, reference the pattern:

```typescript
/**
 * Repository Pattern Implementation
 * 
 * Pattern: Repository (Data Access)
 * Reference: src/platform/patterns/repository.md
 * Example: src/auth/data/authRepository.ts
 */

export class OrderRepository {
  // Implementation following repository pattern
}
```

### Verification Commands Required

Every change should include verification commands:

```markdown
## Verification

**Build:**
```bash
npm run build
```

**Tests:**
```bash
npm run test -- src/auth/login
```

**Lint:**
```bash
npm run lint -- src/auth/
```

**Type Check:**
```bash
npm run type-check
```

**Evidence:**
- All tests pass ✓
- No linting errors ✓
- Build successful ✓
```

### File Touch Reason Required

When modifying files, explain why:

```markdown
## Files Modified

**src/auth/login/ui/LoginForm.tsx**
- Reason: Add email validation
- Changes: Added regex pattern for email format
- Impact: Prevents invalid email submissions

**src/auth/login/domain/authService.ts**
- Reason: Support new token format
- Changes: Updated token parsing logic
- Impact: Backward compatible with old tokens

**tests/auth/login.test.ts**
- Reason: Test new email validation
- Changes: Added 5 new test cases
- Impact: Coverage increased from 85% to 92%
```

### TODO Archive References (Optional)

When resolving TODOs, reference where they're archived:

```typescript
// Resolved TODO: Implement caching
// Original: src/auth/domain/authService.ts:42 (2024-01-10)
// Resolution: Added Redis caching layer
// Archived: /.repo/archive/todos/2024-01-15-auth-caching.md
// PR: #234
```

---

## Related Documents

- **Governance**: `/.repo/GOVERNANCE.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md` (P19: Docs Age With Code)
- **ADR Template**: `/.repo/templates/ADR.md`
