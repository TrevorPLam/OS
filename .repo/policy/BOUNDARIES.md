# Architectural Boundaries Configuration

This document defines the architectural boundaries using the hybrid domain/feature/layer model.

## Boundary Model

**Model**: `hybrid_domain_feature_layer`

### Description
This hybrid model combines domain-driven design, feature-based organization, and layered architecture to provide flexibility while maintaining discipline.

### Structure
```
src/
├── <domain>/              # Business domain (e.g., auth, billing, inventory)
│   └── <feature>/         # Feature within domain (e.g., login, checkout)
│       ├── ui/            # Presentation layer
│       ├── domain/        # Business logic layer
│       └── data/          # Data access layer
└── platform/              # Shared platform utilities
    ├── api/               # API clients
    ├── utils/             # Utility functions
    ├── types/             # Shared types
    └── config/            # Configuration
```

### Benefits
- **Domain**: Organizes code by business capability
- **Feature**: Groups related functionality together
- **Layer**: Enforces separation of concerns
- **Hybrid**: Balances structure with pragmatism

---

## Allowed Import Direction

**Direction**: `ui → domain → data → shared_platform`

### Import Rules

Each layer can only import from layers below it:

```
┌─────────────────┐
│   UI Layer      │  Can import: domain, data, shared_platform
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Domain Layer   │  Can import: data, shared_platform
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Data Layer    │  Can import: shared_platform only
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Shared Platform │  Can import: nothing (no dependencies)
└─────────────────┘
```

### Examples

✅ **Allowed**:
```typescript
// ui layer
import { calculateTotal } from '../domain/pricing';
import { fetchOrders } from '../data/orderRepository';
import { formatCurrency } from '@/platform/utils/format';

// domain layer
import { db } from '../data/database';
import { logger } from '@/platform/utils/logger';

// data layer
import { config } from '@/platform/config/database';
```

❌ **Forbidden**:
```typescript
// domain layer importing from ui - WRONG
import { OrderForm } from '../ui/OrderForm';

// data layer importing from domain - WRONG
import { validateOrder } from '../domain/validation';

// shared_platform importing anything - WRONG
import { getUserId } from '@/auth/domain/user';
```

---

## Cross-Feature Rule

**Rule**: `adr_required`

### Description
Dependencies between features require an Architecture Decision Record (ADR) justifying the coupling.

### Why This Rule Exists
- Prevents tight coupling between features
- Makes dependencies explicit and reviewable
- Forces consideration of alternatives
- Maintains feature independence

### When Cross-Feature Import Is Needed

If Feature A needs to import from Feature B:

1. **Consider Alternatives First**:
   - Can this be in shared platform?
   - Can logic be duplicated (if small)?
   - Can dependency be inverted?
   - Can communication be via events?

2. **If Cross-Feature Import Is Necessary**:
   - Create ADR documenting the decision
   - Explain why alternatives were rejected
   - Document the expected coupling
   - Add to manifest's allowed edges
   - Get approval from architect

3. **Document in Code**:
   ```typescript
   // Cross-feature import approved in ADR-042
   // Reason: Shared authentication logic
   // Allowed: src/billing → src/auth (read-only)
   import { getCurrentUser } from '@/auth/domain/user';
   ```

### ADR Template for Cross-Feature Dependencies

```markdown
# ADR-XXX: Allow Cross-Feature Dependency: [Feature A] → [Feature B]

## Status
Proposed / Accepted / Rejected

## Context
[Why is this dependency needed?]

## Decision
[What cross-feature import is being allowed?]

## Alternatives Considered
1. Shared platform: [Why not suitable?]
2. Duplication: [Why not acceptable?]
3. Inversion: [Why not feasible?]
4. Events: [Why not chosen?]

## Consequences
- Coupling: [What coupling is introduced?]
- Maintenance: [Impact on future changes?]
- Testing: [Impact on test isolation?]

## Approval
Architect: [Name]
Date: [YYYY-MM-DD]
```

---

## Shared Platform Directory

**Location**: `src/platform/`

### Purpose
The platform directory contains shared utilities, types, and configurations used across all domains and features.

### What Belongs in Platform

✅ **Appropriate**:
- Generic utility functions (formatting, parsing, validation)
- Shared types and interfaces
- API clients and HTTP wrappers
- Logging and monitoring utilities
- Configuration management
- Error handling utilities
- Common constants
- Framework extensions

❌ **Not Appropriate**:
- Business logic (belongs in domain layer)
- UI components (belongs in ui layer)
- Feature-specific code
- Domain models (unless truly shared)

### Platform Structure

```
src/platform/
├── api/
│   ├── client.ts         # HTTP client
│   └── interceptors.ts   # Request/response interceptors
├── utils/
│   ├── format.ts         # Formatting utilities
│   ├── validation.ts     # Generic validators
│   └── date.ts           # Date utilities
├── types/
│   ├── common.ts         # Common type definitions
│   └── api.ts            # API type definitions
├── config/
│   ├── app.ts            # App configuration
│   └── env.ts            # Environment variables
├── errors/
│   ├── AppError.ts       # Base error class
│   └── handlers.ts       # Error handlers
└── README.md             # Platform documentation
```

### Adding to Platform

Before adding to platform, ask:
1. Is this used by 3+ features? (Rule of three)
2. Is this generic enough to be reusable?
3. Does this have no business logic?
4. Will this be stable over time?

If all yes, add to platform. Otherwise, keep in feature.

---

## Structure Pattern

**Pattern**: `src/<domain>/<feature>/<layer>/`

### Full Example

```
src/
├── auth/                    # Authentication domain
│   ├── login/               # Login feature
│   │   ├── ui/
│   │   │   ├── LoginForm.tsx
│   │   │   └── LoginButton.tsx
│   │   ├── domain/
│   │   │   ├── authService.ts
│   │   │   └── validation.ts
│   │   └── data/
│   │       └── authRepository.ts
│   └── registration/        # Registration feature
│       ├── ui/
│       ├── domain/
│       └── data/
├── billing/                 # Billing domain
│   ├── checkout/            # Checkout feature
│   │   ├── ui/
│   │   ├── domain/
│   │   └── data/
│   └── invoices/            # Invoices feature
│       ├── ui/
│       ├── domain/
│       └── data/
└── platform/                # Shared platform
    ├── api/
    ├── utils/
    ├── types/
    └── config/
```

### Layer Responsibilities

**UI Layer** (`ui/`):
- React components
- Forms and inputs
- Presentation logic
- User interaction handlers
- Styling (CSS modules, styled-components)

**Domain Layer** (`domain/`):
- Business logic
- Validation rules
- State management
- Services and use cases
- Domain models (if not in data layer)

**Data Layer** (`data/`):
- API calls
- Database queries
- Data transformations
- Repository pattern
- Caching logic

---

## Enforcement Method

**Method**: `hybrid_static_checker_plus_manifest`

### How Boundaries Are Enforced

1. **Static Checker**: 
   - Runs at build time
   - Analyzes import statements
   - Checks against allowed import direction
   - Validates cross-feature dependencies
   - Fails build on violation

2. **Manifest**:
   - `repo.manifest.yaml` defines allowed edges
   - Explicit list of cross-feature dependencies
   - Single source of truth for exceptions
   - Version controlled and reviewed

### Static Checker Configuration

Tools used:
- **TypeScript**: `@typescript-eslint/no-restricted-imports`
- **Python**: `import-linter`
- **Custom**: Script in `/.repo/automation/boundary-checker.js`

### Manifest Format

```yaml
# repo.manifest.yaml
boundaries:
  allowed_edges:
    # Cross-feature dependencies (require ADR)
    - from: "src/billing"
      to: "src/auth"
      reason: "Need current user for billing"
      adr: "ADR-042"
    
    # Cross-domain dependencies (rare, need strong ADR)
    - from: "src/inventory"
      to: "src/billing/checkout"
      reason: "Real-time inventory check during checkout"
      adr: "ADR-058"
```

### Check Execution

```bash
# Run boundary checker
npm run check:boundaries

# Output example
✓ src/auth/login/ui imports from src/auth/login/domain (allowed: same feature)
✓ src/billing/checkout/domain imports from src/platform/utils (allowed: platform)
✓ src/billing imports from src/auth (allowed: manifest ADR-042)
✗ src/inventory/ui imports from src/billing/ui (forbidden: cross-feature without ADR)

Boundary violations: 1
```

---

## Exception Process

**Process**: `task_packet_for_small_exceptions_adr_for_large`

### Small Exceptions (Task Packet)

For temporary or minor boundary violations:

1. Create task packet documenting:
   - What violation is needed
   - Why it's necessary
   - How it will be fixed
   - Timeline for fix (max 30 days)

2. Add to manifest as temporary edge:
   ```yaml
   - from: "src/feature-a"
     to: "src/feature-b"
     reason: "Temporary coupling during migration"
     task: "TASK-123"
     expires: "2024-06-30"
   ```

3. Create follow-up task to remove coupling

4. Merge with waiver

### Large Exceptions (ADR Required)

For permanent or significant cross-feature dependencies:

1. Write ADR (see template above)
2. Get architect approval
3. Add to manifest permanently
4. Update documentation
5. No expiration date

---

## Violation Severity

**Severity**: `waiver_plus_auto_task`

### When Violation Detected

1. **Block Build**: Build fails immediately
2. **Generate Waiver**: Auto-generate waiver document
3. **Create Task**: Auto-create task to fix violation
4. **Notify**: Alert PR author and architect
5. **Require Review**: Extra review from architect needed

### Waiver Contents

```markdown
# Boundary Violation Waiver

**Violation**: src/X/ui imports from src/Y/domain
**Detected**: 2024-01-15
**Author**: @username
**PR**: #123

## Details
- From: src/auth/login/ui/LoginForm.tsx:42
- To: src/billing/domain/priceService.ts
- Reason: [Author must explain]

## Remediation Plan
- [ ] Create shared platform utility
- [ ] Update imports to use platform
- [ ] Remove direct cross-feature dependency

**Target Fix Date**: 2024-02-15
**Tracking Task**: TASK-456
```

### Auto-Generated Task

```markdown
# TASK-456: Fix Boundary Violation

**Type**: Technical Debt
**Priority**: P1
**Assigned**: @username

## Description
Boundary violation detected in PR #123.
Fix cross-feature import between auth and billing.

## Acceptance Criteria
- [ ] Remove direct import from auth/ui to billing/domain
- [ ] Move shared logic to platform if applicable
- [ ] Update manifest if exception is permanent
- [ ] Boundary checker passes

**Related Waiver**: WAIVER-123
**Deadline**: 2024-02-15
```

---

## Boundary Visibility

**Visibility**: `inline_comments_plus_summary`

### Inline Comments

Document boundaries in code:

```typescript
// === BOUNDARY: UI Layer ===
// Allowed imports: domain, data, platform
// Forbidden: other features' ui layers

import { validateLogin } from '../domain/validation';  // ✓ Same feature domain
import { apiClient } from '@/platform/api/client';     // ✓ Platform utility

// Cross-feature import approved in ADR-042
import { getCurrentUser } from '@/auth/domain/user';    // ✓ Manifest allows

// === END BOUNDARY ===
```

### Summary Document

`/.repo/docs/BOUNDARIES_SUMMARY.md` contains:
- Visual diagram of boundaries
- List of all cross-feature dependencies
- Quick reference for developers
- Links to relevant ADRs

---

## Exception Evidence

**Standard**: `standard`

### Required Evidence for Exceptions

When requesting boundary exception:

1. **Justification**: Why is this needed?
2. **Alternatives**: What else was considered?
3. **Impact**: What coupling is introduced?
4. **Mitigation**: How to minimize impact?
5. **Testing**: How will this be tested?

---

## Exception Representation

**Representation**: `explicit_edges_in_manifest`

### Manifest as Source of Truth

All exceptions are explicitly listed in `repo.manifest.yaml`:

```yaml
boundaries:
  model: "hybrid_domain_feature_layer"
  
  allowed_edges:
    # Each edge must be explicitly documented
    - from: "src/billing"
      to: "src/auth"
      layers: ["domain"]  # Only domain layer allowed
      reason: "Need user info for billing"
      adr: "ADR-042"
      approved_by: "architect@example.com"
      approved_date: "2024-01-15"
```

### Benefits
- Single source of truth
- Version controlled
- Reviewable in PRs
- Auditable history
- Easy to understand dependencies

---

## Boundary Checker Tool

Location: `/.repo/automation/boundary-checker.js`

### Usage

```bash
# Check current code
npm run check:boundaries

# Check specific directory
npm run check:boundaries -- src/auth/

# Auto-fix safe violations
npm run check:boundaries -- --fix

# Generate dependency graph
npm run check:boundaries -- --graph
```

---

## Related Documents

- **Governance**: `/.repo/GOVERNANCE.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md` (P13: Respect Boundaries by Default)
- **Manifest**: `/repo.manifest.yaml`
- **ADR Template**: `/.repo/templates/ADR.md`
- **Boundary Summary**: `/.repo/docs/BOUNDARIES_SUMMARY.md`
