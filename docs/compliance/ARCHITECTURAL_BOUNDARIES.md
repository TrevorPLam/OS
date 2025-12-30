# Architectural Boundary Enforcement (CONST-10)

**Constitution Requirement**: Section 15 - Boundary rules (forbidden imports) enforced by tooling

**Date Implemented**: December 30, 2025  
**Status**: ✅ **IMPLEMENTED**

---

## Overview

Import-linter is configured to enforce architectural boundaries in the ConsultantPro codebase. This ensures that:

1. **Layer separation** is maintained (API → Business → Infrastructure)
2. **Foundation modules** remain dependency-free
3. **Portal isolation** prevents staff-only code access
4. **API decoupling** prevents cross-API imports

---

## Configuration

**File**: `.importlinter`  
**Tool**: import-linter 2.0  
**CI Integration**: `.github/workflows/ci.yml` (security job)

### Enforcement Contracts

#### Contract 1: Core Module Isolation
**Rule**: `src.modules.core` must not import business modules  
**Rationale**: Core provides shared utilities; business logic should not pollute it  
**Status**: ✅ KEPT

**Forbidden Dependencies**:
- clients, crm, projects, finance, documents
- calendar, marketing, pricing, delivery
- orchestration, recurrence, onboarding, knowledge
- communications, email_ingestion, support, sms
- snippets, auth, jobs, assets

#### Contract 2: Firm Module Foundation
**Rule**: `src.modules.firm` must not import business modules  
**Rationale**: Firm is the tenant foundation; all modules depend on it  
**Status**: ✅ KEPT

**Forbidden Dependencies**: (same as Contract 1)

#### Contract 3: Portal API Isolation
**Rule**: `src.api.portal` must not import staff admin modules  
**Rationale**: Portal users must not access admin-only functionality  
**Status**: ✅ KEPT

**Forbidden Dependencies**:
- src.modules.firm.admin

#### Contract 4: Portal API Decoupling
**Rule**: `src.api.portal` must not import other API modules  
**Rationale**: Prevents tight coupling between API endpoints  
**Status**: ✅ KEPT

**Forbidden Dependencies**:
- src.api.crm, src.api.finance, src.api.projects
- src.api.documents, src.api.clients, src.api.assets

#### Contract 5: CRM API Decoupling
**Rule**: `src.api.crm` must not import other API modules  
**Rationale**: Prevents tight coupling between API endpoints  
**Status**: ✅ KEPT

**Forbidden Dependencies**:
- src.api.portal, src.api.finance, src.api.projects
- src.api.documents, src.api.clients, src.api.assets

---

## Analysis Results

**Last Run**: December 30, 2025

```
Analyzed 321 files, 90 dependencies.
------------------------------------

Core module has no dependencies on business modules KEPT
Firm module is foundation - business modules may not import each other directly KEPT
Portal API must not import staff admin modules KEPT
API modules should not import from each other (avoid coupling) - Portal KEPT
API modules should not import from each other (avoid coupling) - CRM KEPT

Contracts: 5 kept, 0 broken.
```

**Result**: ✅ All contracts satisfied

---

## Architectural Guidelines

### 1. Layer Hierarchy

Valid import direction (top → bottom):

```
┌─────────────────────────────────┐
│  API Layer (api/*)              │  ← ViewSets, Serializers
│  - portal, crm, finance, etc.   │
└──────────────┬──────────────────┘
               │ imports ↓
┌──────────────▼──────────────────┐
│  Business Logic (modules/*)     │  ← Models, Services
│  - clients, projects, etc.      │
└──────────────┬──────────────────┘
               │ imports ↓
┌──────────────▼──────────────────┐
│  Infrastructure (config/*)      │  ← Settings, Middleware
│  - settings, middleware, utils  │
└─────────────────────────────────┘
```

### 2. Foundation Modules

**Everyone can depend on these:**
- `src.modules.firm` - Firm/tenant foundation
- `src.modules.core` - Shared utilities

**Nobody can depend on:**
- Individual API modules (portal, crm, finance, etc.)
- Each other's business logic modules (without careful design)

### 3. Cross-Module Communication

**Recommended Patterns**:
1. **Services**: Use service classes for cross-module operations
2. **Signals**: Django signals for event-driven communication
3. **Shared Models**: Reference foundation models (Firm, User)

**Anti-Patterns**:
- Direct imports between business modules
- API modules importing each other
- Business logic in API layer

### 4. Portal Isolation

**Portal restrictions**:
- Cannot import staff admin code
- Cannot access firm-admin features
- Scoped to client-visible data only

### 5. Import Policy

**Allowed**:
- ✅ API → Modules
- ✅ Modules → Core
- ✅ Modules → Firm
- ✅ All → Config

**Forbidden**:
- ❌ Core → Business Modules
- ❌ Firm → Business Modules
- ❌ API → API (cross-module)
- ❌ Portal → Admin Code

---

## CI Integration

### Workflow Step

```yaml
- name: Check architectural boundaries
  run: |
    # CONST-10: Enforce import boundaries with import-linter
    pip install import-linter==2.0
    lint-imports --config .importlinter
```

### Build Behavior

**On Success**: Contract check passes, build continues  
**On Failure**: Build fails with violated contract details  

Example failure output:
```
Contract 'Core module has no dependencies on business modules' BROKEN

src.modules.core imports src.modules.crm:
  src/modules/core/utils.py:15 → src/modules/crm/models.py
```

---

## Running Locally

### Install
```bash
pip install import-linter==2.0
```

### Check All Contracts
```bash
lint-imports --config .importlinter
```

### Check Specific Contract
```bash
lint-imports --config .importlinter --contract 1
```

### Verbose Output
```bash
lint-imports --config .importlinter --verbose
```

---

## Adding New Contracts

### Contract Types

1. **forbidden**: Prevent specific imports
2. **layers**: Enforce layered architecture
3. **independence**: Prevent circular dependencies

### Example: Add New Contract

```ini
[importlinter:contract:6]
name = New module isolation rule
type = forbidden
source_modules =
    src.modules.newmodule
forbidden_modules =
    src.modules.othermodule
```

### Testing New Contracts

1. Add contract to `.importlinter`
2. Run `lint-imports` locally
3. Fix any violations
4. Commit changes
5. CI will enforce going forward

---

## Violation Resolution

### If Contract is Broken

**1. Understand the Violation**
- Review the import path shown in error
- Understand why the import exists

**2. Choose Resolution**

**Option A: Refactor (Preferred)**
- Move shared code to foundation module
- Use service layer for cross-module communication
- Use signals for event-driven communication

**Option B: Update Contract (Rare)**
- Document why contract needs change
- Get architecture review
- Update contract definition
- Ensure no security implications

**Option C: Temporary Exception (Emergency Only)**
- Document in PR why exception needed
- Set expiry date for exception
- Create issue to fix properly
- Only for critical production fixes

### Example Refactoring

**Before** (violates contract):
```python
# src/modules/core/utils.py
from src.modules.crm.models import Lead  # VIOLATION

def get_lead_count():
    return Lead.objects.count()
```

**After** (compliant):
```python
# Move to src/modules/crm/services.py
class LeadService:
    @staticmethod
    def get_lead_count():
        from src.modules.crm.models import Lead
        return Lead.objects.count()

# src/modules/core/utils.py (no violation)
# Caller imports from crm.services, not core
```

---

## Benefits

### 1. Maintainability
- Clear module boundaries
- Easier to understand dependencies
- Reduces coupling

### 2. Testability
- Isolated modules easier to test
- Fewer mocking dependencies
- Faster test execution

### 3. Security
- Portal isolation enforced
- Admin code protected
- Attack surface minimized

### 4. Evolvability
- Safe to refactor modules
- Dependencies explicit
- Changes remain localized

---

## Related Documentation

- [Constitution Section 15](../codingconstitution.md#15-minimal-enforcement-plan-recommended) - Boundary enforcement requirement
- [Repository Structure Delta](./repo-structure-delta.md) - Current vs intended structure
- [THREAT_MODEL.md](./THREAT_MODEL.md) - Portal isolation security

---

## Maintenance

### Regular Tasks

**Weekly**: Run import-linter locally before large PRs  
**Monthly**: Review contracts for new modules  
**Quarterly**: Audit for architectural drift

### Contract Evolution

As architecture evolves:
1. Add contracts for new modules
2. Tighten constraints where possible
3. Document exceptions and remediation plans
4. Keep contracts aligned with architectural decisions (ADRs)

---

## Compliance Status

- [x] Import-linter installed (requirements.txt)
- [x] Configuration file created (.importlinter)
- [x] 5 contracts defined and enforced
- [x] CI integration complete
- [x] All contracts currently satisfied
- [x] Documentation complete

**Constitution Section 15**: ✅ COMPLIANT

---

**Last Verified**: December 30, 2025  
**Next Review**: March 30, 2026 (quarterly)
