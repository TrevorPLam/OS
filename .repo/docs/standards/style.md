# Code Style Standards

This document defines code style standards including code anchors and safety heuristics.

## Code Anchors

Code anchors help developers locate and reference specific sections of code.

### Region Comments Required

Use region comments to mark important sections:

```typescript
// === REGION: Authentication Logic ===

export async function authenticateUser(email: string, password: string) {
  // Implementation...
}

export async function refreshToken(token: string) {
  // Implementation...
}

// === END REGION: Authentication Logic ===

// === REGION: Token Validation ===

export function validateToken(token: string): boolean {
  // Implementation...
}

// === END REGION: Token Validation ===
```

### Critical Code Excerpts in PR

When submitting PRs, include excerpts of critical changes:

```markdown
## Critical Changes

**File: src/auth/domain/authService.ts**

```typescript
// Before
function hashPassword(password: string): string {
  return crypto.createHash('md5').update(password).digest('hex');
}

// After
function hashPassword(password: string): string {
  return bcrypt.hashSync(password, 10);  // Changed from MD5 to bcrypt for security
}
```

**Rationale**: MD5 is cryptographically broken. Migrated to bcrypt with salt rounds.
```

### Named Function Anchors

Use descriptive function names as anchors:

```typescript
/**
 * ANCHOR: calculateTotalPrice
 * 
 * Calculates the total price including tax and discounts.
 * This is the canonical price calculation used throughout the app.
 * 
 * Referenced in:
 * - src/billing/checkout/domain/checkoutService.ts
 * - src/billing/invoice/domain/invoiceService.ts
 * - src/reporting/sales/domain/salesReport.ts
 */
export function calculateTotalPrice(
  subtotal: number,
  taxRate: number,
  discount: number
): number {
  const tax = subtotal * taxRate;
  const total = subtotal + tax - discount;
  return Math.max(0, total);  // Ensure non-negative
}
```

---

## Safety Heuristics

Safety heuristics help prevent errors and ensure code quality.

### Impact Summary Required

Every PR must include an impact summary:

```markdown
## Impact Summary

**Scope**: Authentication system
**Users Affected**: All users (100%)
**Risk Level**: 🟡 Medium

**What Changes**:
- Password hashing algorithm changed from MD5 to bcrypt
- Existing passwords will be migrated on next login
- Session tokens remain valid (no re-login required)

**What Doesn't Change**:
- Login API endpoints (backward compatible)
- Session management
- OAuth flows

**Breaking Changes**: None

**Rollback Impact**: Users who changed passwords after deployment will need to reset password if rolled back
```

### Explicit Unknowns Required

State what you don't know or are unsure about:

```markdown
## Unknowns and Assumptions

**UNKNOWN**: 
- Impact on legacy mobile app (v1.2.3) - might use different auth flow
- Performance impact of bcrypt on high traffic (needs load testing)
- Compatibility with SSO integration (needs QA verification)

**ASSUMPTIONS**:
- All users use web app or mobile app v2.0+
- Database can handle migration load (tested with 10k users)
- Bcrypt performance is acceptable (<100ms per hash)

**MITIGATION**:
- [ ] Test with legacy mobile app - HITL required
- [ ] Run load test with bcrypt - HITL if >200ms
- [ ] Verify SSO integration - Manual QA before production
```

### Rollback Plan Required

Every significant change needs a rollback plan:

```markdown
## Rollback Plan

**Rollback Trigger**:
- Auth failure rate >1%
- Login latency >5 seconds p95
- Critical bug in password validation
- SSO integration breaks

**Rollback Steps**:
1. Revert to previous deployment (git tag: v2.4.1)
2. Run rollback migration script: `npm run migrate:rollback auth-bcrypt`
3. Restart application servers
4. Verify auth is working
5. Monitor error rates for 1 hour

**Rollback Time**: ~15 minutes (tested in staging)

**Data Loss**: 
- Users who changed passwords after deployment will need to use "forgot password" flow
- Session tokens remain valid
- No data loss, only inconvenience for ~0.1% of users

**Alternative Rollback** (if migration fails):
- Feature flag: Disable new auth, use old MD5 temporarily
- Fix issues in next hotfix
- Re-enable new auth
```

---

## Code Organization

### File Structure

Organize code consistently:

```typescript
// === IMPORTS ===
import { external } from 'external-package';
import { platform } from '@/platform/utils';
import { local } from './localModule';

// === TYPES ===
interface UserCredentials {
  email: string;
  password: string;
}

// === CONSTANTS ===
const MAX_LOGIN_ATTEMPTS = 3;
const SESSION_TIMEOUT = 3600;

// === MAIN LOGIC ===
export async function authenticateUser(credentials: UserCredentials) {
  // Implementation...
}

// === HELPER FUNCTIONS ===
function validateEmail(email: string): boolean {
  // Implementation...
}

// === EXPORTS ===
export { UserCredentials };
```

### Function Order

Order functions logically:
1. Public API functions (exported)
2. Internal helper functions
3. Utility functions

### Naming Conventions

Follow consistent naming:
- **Functions**: `camelCase` (e.g., `getUserById`)
- **Classes**: `PascalCase` (e.g., `UserService`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Files**: `camelCase.ts` or `PascalCase.tsx` (components)
- **Private**: Prefix with `_` (e.g., `_internalHelper`)

---

## Error Handling

### Consistent Error Patterns

```typescript
// === REGION: Error Classes ===

export class AuthenticationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends Error {
  constructor(field: string, message: string) {
    super(`${field}: ${message}`);
    this.name = 'ValidationError';
  }
}

// === END REGION: Error Classes ===

// === REGION: Error Handling ===

export async function authenticateUser(email: string, password: string) {
  try {
    // Validate inputs
    if (!email) {
      throw new ValidationError('email', 'Email is required');
    }
    
    // Attempt authentication
    const user = await findUserByEmail(email);
    if (!user) {
      throw new AuthenticationError('Invalid credentials');
    }
    
    // More logic...
    
  } catch (error) {
    // Log error for debugging
    logger.error('Authentication failed', { email, error });
    
    // Re-throw for caller to handle
    throw error;
  }
}

// === END REGION: Error Handling ===
```

---

## Performance Considerations

### Performance Comments

Document performance-critical code:

```typescript
/**
 * PERFORMANCE: This function is called on every request.
 * Keep it fast. Current benchmark: <5ms for 1000 items.
 * 
 * Optimizations applied:
 * - Early return for empty arrays
 * - Single-pass algorithm (O(n))
 * - No object allocations in loop
 * 
 * If modifying, run benchmark: npm run benchmark:filter
 */
export function fastFilter<T>(items: T[], predicate: (item: T) => boolean): T[] {
  if (items.length === 0) return [];
  
  const result: T[] = [];
  for (let i = 0; i < items.length; i++) {
    if (predicate(items[i])) {
      result.push(items[i]);
    }
  }
  return result;
}
```

### Benchmark Requirements

Performance-critical changes must include benchmarks:

```markdown
## Performance Impact

**Benchmark Results**:

| Operation | Before | After | Change |
|-----------|--------|-------|--------|
| Hash password | 150ms | 95ms | -37% ✓ |
| Validate token | 5ms | 5ms | 0% ✓ |
| Login (p95) | 200ms | 180ms | -10% ✓ |

**Test Environment**: MacBook Pro M1, 16GB RAM, Node 18
**Test Script**: `npm run benchmark:auth`
**Sample Size**: 10,000 operations
```

---

## Security Annotations

### Security-Critical Code

Mark security-critical sections:

```typescript
/**
 * SECURITY CRITICAL: Token validation
 * 
 * This function validates JWT tokens. Any bugs here could allow:
 * - Unauthorized access
 * - Token forgery
 * - Session hijacking
 * 
 * DO NOT modify without security review.
 * Last reviewed: 2024-01-15 by security@example.com
 * 
 * See: /.repo/policy/SECURITY_BASELINE.md
 */
export function validateJWT(token: string): TokenPayload | null {
  try {
    // Verify signature
    const verified = jwt.verify(token, SECRET_KEY);
    
    // Check expiration
    if (verified.exp < Date.now() / 1000) {
      return null;
    }
    
    // Check issuer
    if (verified.iss !== EXPECTED_ISSUER) {
      return null;
    }
    
    return verified as TokenPayload;
    
  } catch (error) {
    // Invalid token
    return null;
  }
}
```

---

## Testing Requirements

### Test Organization

```typescript
// === REGION: Test Setup ===

describe('AuthService', () => {
  let authService: AuthService;
  let mockDatabase: Database;
  
  beforeEach(() => {
    mockDatabase = createMockDatabase();
    authService = new AuthService(mockDatabase);
  });
  
  // === REGION: Happy Path Tests ===
  
  describe('authenticateUser', () => {
    it('should return token for valid credentials', async () => {
      // Test implementation...
    });
  });
  
  // === END REGION: Happy Path Tests ===
  
  // === REGION: Error Cases ===
  
  describe('authenticateUser - errors', () => {
    it('should throw ValidationError for missing email', async () => {
      // Test implementation...
    });
    
    it('should throw AuthenticationError for invalid password', async () => {
      // Test implementation...
    });
  });
  
  // === END REGION: Error Cases ===
});

// === END REGION: Test Setup ===
```

---

## Related Documents

- **Governance**: `/.repo/GOVERNANCE.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md` (P21: Naming Matters)
- **Security**: `/.repo/policy/SECURITY_BASELINE.md`
- **Documentation**: `/.repo/docs/standards/documentation.md`
