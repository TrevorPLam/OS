# ESLint Rules Re-enablement Plan

**Date:** 2026-01-24  
**Status:** In Progress  
**Related Task:** TASK-018 - Re-enable ESLint Rules and Fix Violations

## Overview

ESLint rules were previously disabled due to widespread violations. As part of code stabilization, we're re-enabling them progressively:

1. **Phase 1 (COMPLETED)**: Enable as "warn" to surface issues without blocking CI
2. **Phase 2 (TODO)**: Fix all violations systematically
3. **Phase 3 (TODO)**: Upgrade rules to "error" level

## Current Status

### Re-enabled Rules (as warnings)

| Rule | Status | Count | Notes |
|------|--------|-------|-------|
| `@typescript-eslint/no-explicit-any` | warn | ~23 | API layer fixed, ~23 remain in pages |
| `@typescript-eslint/no-unused-vars` | warn | ~19 | Most are incomplete features |
| `react-hooks/exhaustive-deps` | warn | ~6 | Missing dependencies in useEffect |

### Configuration

```javascript
// frontend/.eslintrc.cjs
rules: {
  "@typescript-eslint/no-explicit-any": "warn",
  "@typescript-eslint/no-unused-vars": ["warn", { 
    "argsIgnorePattern": "^_",
    "varsIgnorePattern": "^_"
  }],
  "react-hooks/exhaustive-deps": "warn",
}
```

## Violation Breakdown

### 1. `@typescript-eslint/no-explicit-any` (23 violations)

**Files with violations:**
- `src/api/client.ts` (1)
- `src/pages/AssetManagement.tsx` (1)
- `src/pages/CalendarOAuthCallback.tsx` (1)
- `src/pages/CalendarSync.tsx` (3)
- `src/pages/ClientPortal.tsx` (1)
- `src/pages/Documents.tsx` (5)
- `src/pages/Proposals.tsx` (1)
- `src/pages/SiteMessages.tsx` (1)
- `src/pages/WorkflowBuilder.tsx` (4)

**Fix Strategy:**
1. Define proper TypeScript interfaces for each `any` usage
2. Use `unknown` for truly unknown types, then narrow with type guards
3. Document any remaining `any` with `// eslint-disable-next-line` and justification

### 2. `@typescript-eslint/no-unused-vars` (19 violations)

**Common patterns:**
- Unused imports (useEffect, type imports)
- Incomplete features (selectedNode, setSelectedAsset)
- Unused destructured variables

**Fix Strategy:**
1. Remove unused imports
2. Prefix with `_` for intentionally unused variables: `const _unused = value`
3. Complete or remove incomplete features
4. Remove dead code

### 3. `react-hooks/exhaustive-deps` (6 violations)

**Files with violations:**
- `src/pages/AssetManagement.tsx`
- `src/pages/ClientPortal.tsx`
- `src/pages/Documents.tsx`
- `src/pages/ProjectKanban.tsx`
- `src/pages/TimeTracking.tsx`

**Fix Strategy:**
1. Add missing dependencies to useEffect
2. Wrap functions in useCallback if they're dependencies
3. Use `// eslint-disable-next-line` only if intentionally stale closure needed

## Phase 2: Systematic Fixes (TODO)

### Week 1: Fix `any` types (Estimated: 4 hours)
- [ ] Create TypeScript interfaces for remaining `any` usages
- [ ] Replace with proper types or `unknown`
- [ ] Test changes

### Week 2: Fix unused variables (Estimated: 2 hours)
- [ ] Remove unused imports
- [ ] Complete or remove incomplete features
- [ ] Add `_` prefix where appropriate

### Week 3: Fix exhaustive-deps (Estimated: 3 hours)
- [ ] Add missing dependencies
- [ ] Wrap callbacks with useCallback
- [ ] Test for infinite loops or stale closures

### Week 4: Upgrade to errors (Estimated: 1 hour)
- [ ] Change all "warn" to "error" in .eslintrc.cjs
- [ ] Verify CI passes
- [ ] Update documentation

## Phase 3: Upgrade to Error Level (TODO)

Once all violations are fixed:

```javascript
rules: {
  "@typescript-eslint/no-explicit-any": "error",
  "@typescript-eslint/no-unused-vars": ["error", { 
    "argsIgnorePattern": "^_",
    "varsIgnorePattern": "^_"
  }],
  "react-hooks/exhaustive-deps": "error",
}
```

## Benefits

1. **Type Safety**: Eliminates `any` types, improving IDE autocomplete and catching type errors
2. **Code Quality**: Removes dead code and unused variables
3. **React Best Practices**: Ensures hooks have correct dependencies
4. **Developer Experience**: Better warnings during development
5. **CI Quality**: Eventually blocks merges with quality issues

## Progress Tracking

- [x] Phase 1: Enable as warnings (2026-01-24)
- [ ] Phase 2: Fix all violations
- [ ] Phase 3: Upgrade to error level

## References

- ANALYSIS.md Section 0.8: ESLint rules disabled
- ANALYSIS.md Section 11.4: 57 instances of `any` type (API layer fixed)
- TASK-018 in BACKLOG.md

---

**Last Updated:** 2026-01-24  
**Next Review:** After Phase 2 completion
