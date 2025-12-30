# Architectural Boundary Rules

**Status:** Active (enforced in CI via import-linter)
**Constitution Reference:** [Section 4 (Architecture)](codingconstitution.md#4-architecture-constitution), [Section 15 (Enforcement)](codingconstitution.md#15-minimal-enforcement-plan-recommended)
**Enforcement:** `.importlinter` configuration + CI check

---

## 1. Purpose

This document defines the architectural boundaries and layering rules for the ConsultantPro codebase. These rules are **automatically enforced** in CI using `import-linter` to prevent violations.

### 1.1 Why Boundary Rules Matter

- **Maintainability:** Clear boundaries prevent spaghetti code and "big ball of mud" architecture
- **Testability:** Layered architecture enables unit testing of business logic without infrastructure dependencies
- **Evolvability:** Changes remain localized to specific layers/modules
- **Onboarding:** New developers can understand dependencies and flow

---

## 2. Layering Architecture

ConsultantPro follows a **layered architecture** based on clean architecture principles:

```
┌─────────────────────────────────────────────────────┐
│  UI / Delivery Layer (API Controllers, Views)      │
│  - src/api/                                         │
│  - src/modules/*/views.py                           │
└──────────────────┬──────────────────────────────────┘
                   │ may call ↓
┌──────────────────▼──────────────────────────────────┐
│  Application / Use Case Layer (Services)            │
│  - src/modules/*/services.py                        │
│  - src/modules/*/serializers.py                     │
└──────────────────┬──────────────────────────────────┘
                   │ may call ↓
┌──────────────────▼──────────────────────────────────┐
│  Domain Logic Layer (Models, Business Rules)        │
│  - src/modules/*/models.py                          │
│  - src/modules/*/validators.py                      │
└──────────────────┬──────────────────────────────────┘
                   │ implements ↓
┌──────────────────▼──────────────────────────────────┐
│  Infrastructure Layer (DB, Queues, External APIs)   │
│  - src/modules/*/tasks.py (Celery)                  │
│  - src/modules/*/signals.py (Django signals)        │
│  - Storage, Email, SMS integrations                 │
└─────────────────────────────────────────────────────┘
```

**Key Principle:** Upper layers may call lower layers, but **lower layers must never call upper layers** (dependency inversion).

---

## 3. Enforced Boundary Rules

### Rule 1: API Layer Must Not Import Infrastructure Directly

**Contract:** `forbidden` import from `src.api` → `src.modules.*.tasks`, `src.modules.*.signals`, `celery`

**Rationale:**
- API controllers should not directly trigger async tasks or signals
- Use service layer to orchestrate async work
- Prevents tight coupling between HTTP layer and background jobs

**Allowed:**
```python
# src/api/clients/views.py
from modules.clients.services import ClientService

class ClientViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        client = serializer.save()
        # Use service to trigger async work
        ClientService.send_welcome_email(client.id)
```

**Forbidden:**
```python
# src/api/clients/views.py
from modules.clients.tasks import send_welcome_email  # ❌ FORBIDDEN

class ClientViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        client = serializer.save()
        send_welcome_email.delay(client.id)  # ❌ Direct task call
```

---

### Rule 2: Domain/Service Layer Must Not Import Django ORM Query Directly

**Contract:** `forbidden` import from `src.modules.*.services`, `src.modules.*.domain` → `django.db.models.query`

**Rationale:**
- Service layer should work with domain models, not ORM internals
- Enables potential future migration to different ORM/database
- Allows exceptions for `django.db.transaction` (necessary for atomicity)

**Allowed:**
```python
# src/modules/clients/services.py
from django.db import transaction
from modules.clients.models import Client

class ClientService:
    @transaction.atomic
    def create_client_with_defaults(self, data):
        client = Client.objects.create(**data)
        return client
```

**Forbidden:**
```python
# src/modules/clients/services.py
from django.db.models.query import QuerySet  # ❌ FORBIDDEN

def get_active_clients() -> QuerySet:
    return Client.objects.filter(status='active')  # ❌ Leaking QuerySet
```

---

### Rule 3: No Circular Dependencies Between Core Modules

**Contract:** `independence` between `crm`, `finance`, `projects`, `documents`, `clients`, `calendar`

**Rationale:**
- Core modules should be independent and cohesive
- Prevents tight coupling and circular imports
- Shared functionality goes in `src.modules.core`

**Allowed:**
```python
# src/modules/crm/models.py
from modules.clients.models import Client  # ✅ OK (crm → clients)

# src/modules/finance/models.py
from modules.clients.models import Client  # ✅ OK (finance → clients)

# src/modules/core/utils.py
from modules.crm.models import Lead        # ✅ OK (core can import)
from modules.finance.models import Invoice # ✅ OK (core can import)
```

**Forbidden:**
```python
# src/modules/clients/models.py
from modules.crm.models import Lead  # ⚠️ Creates circular dependency

# src/modules/finance/models.py
from modules.projects.models import Task  # ⚠️ Avoid cross-module imports
from modules.calendar.models import Appointment  # ⚠️ Use indirection
```

**Resolution:** Use foreign key strings (`"crm.Lead"`) or create an intermediate model in `core`.

---

### Rule 4: Portal API Must Not Import Staff-Only Modules

**Contract:** `forbidden` import from `src.api.portal` → `src.modules.firm.provisioning`, `src.modules.firm.admin`

**Rationale:**
- Portal API is for clients, not staff
- Prevents accidental exposure of admin functionality
- Clear security boundary

**Allowed:**
```python
# src/api/portal/views.py
from modules.clients.models import Client
from modules.documents.models import Document
```

**Forbidden:**
```python
# src/api/portal/views.py
from modules.firm.provisioning import TenantProvisioningService  # ❌ FORBIDDEN
from modules.firm.admin import grant_admin_access  # ❌ FORBIDDEN
```

---

### Rule 5: Infrastructure Must Not Import Domain Logic

**Contract:** `layers` enforce `views → serializers → services → models`

**Rationale:**
- Infrastructure layer (tasks, signals) should call service layer, not reverse
- Prevents inversion of dependencies

**Allowed:**
```python
# src/modules/clients/tasks.py (infrastructure)
from modules.clients.services import ClientService  # ✅ OK

@shared_task
def send_welcome_email(client_id):
    ClientService.send_welcome_email(client_id)  # ✅ Calls service
```

**Forbidden:**
```python
# src/modules/clients/services.py (domain)
from modules.clients.tasks import send_welcome_email  # ❌ Creates circular dependency

class ClientService:
    def create_client(self, data):
        client = Client.objects.create(**data)
        send_welcome_email.delay(client.id)  # ❌ Service calling infrastructure
```

---

## 4. Running Import Linter

### 4.1 Locally

```bash
# Install import-linter
pip install -r requirements-dev.txt

# Run boundary checks
lint-imports
```

### 4.2 In CI

Boundary rules are automatically enforced in the CI pipeline (`.github/workflows/ci.yml`):

```yaml
- name: Check boundary rules with import-linter
  run: |
    # CONST-10: Enforce architectural boundary rules
    lint-imports
```

**CI will fail** if any boundary rule is violated.

### 4.3 Interpreting Errors

Example error:
```
ERROR: Contract 'API layer must not import infrastructure directly' violated
  src.api.clients.views imports src.modules.clients.tasks
  Forbidden import: src.api.clients.views -> src.modules.clients.tasks.send_welcome_email
```

**Resolution:**
1. Identify the forbidden import in the error message
2. Refactor to call through service layer:
   - Move task invocation to `src.modules.clients.services`
   - Have API view call `ClientService.send_welcome_email()`

---

## 5. Exceptions and Overrides

### 5.1 When to Request an Exception

Boundary rules should rarely be violated. Valid reasons for exceptions:

1. **Framework Constraints:** Django requires certain imports in specific files (e.g., `admin.py`)
2. **Migration Path:** Temporary exception during large refactoring (with clear end date)
3. **Performance:** Proven performance issue that requires boundary bypass (with ADR)

### 5.2 Requesting an Exception

1. Create an ADR in `docs/05-decisions/` explaining:
   - Why the boundary rule cannot be followed
   - What the impact is
   - How long the exception will last
   - Plan to remove exception (if temporary)

2. Update `.importlinter` to add the specific exception:
   ```ini
   [importlinter:contract:1]
   name = API layer must not import infrastructure directly
   type = forbidden
   source_modules = src.api
   forbidden_modules = src.modules.*.tasks
   ignore_imports =
       src.api.specific.view -> src.modules.specific.tasks  # ADR-0042: Temporary exception for migration
   ```

3. Get approval from architecture review (CTO/Tech Lead)

---

## 6. Common Violations and Fixes

### 6.1 Violation: API View Calling Celery Task Directly

**Problem:**
```python
# src/api/clients/views.py
from modules.clients.tasks import send_welcome_email

class ClientViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        client = serializer.save()
        send_welcome_email.delay(client.id)  # ❌ Violates Rule 1
```

**Fix:**
```python
# src/modules/clients/services.py
from modules.clients.tasks import send_welcome_email

class ClientService:
    @staticmethod
    def trigger_welcome_email(client_id):
        send_welcome_email.delay(client_id)

# src/api/clients/views.py
from modules.clients.services import ClientService

class ClientViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        client = serializer.save()
        ClientService.trigger_welcome_email(client.id)  # ✅ Calls through service
```

---

### 6.2 Violation: Circular Module Dependency

**Problem:**
```python
# src/modules/crm/models.py
from modules.finance.models import Invoice  # ❌ Violates Rule 3

class Prospect(models.Model):
    invoice = models.ForeignKey(Invoice, ...)

# src/modules/finance/models.py
from modules.crm.models import Prospect  # ❌ Circular import!

class Invoice(models.Model):
    prospect = models.ForeignKey(Prospect, ...)
```

**Fix (Option 1): Use String References**
```python
# src/modules/crm/models.py
class Prospect(models.Model):
    invoice = models.ForeignKey("finance.Invoice", ...)  # ✅ String reference

# src/modules/finance/models.py
class Invoice(models.Model):
    prospect = models.ForeignKey("crm.Prospect", ...)  # ✅ String reference
```

**Fix (Option 2): Introduce Core Model**
```python
# src/modules/core/models.py
class BillableEntity(models.Model):
    # Shared base class
    pass

# src/modules/crm/models.py
class Prospect(BillableEntity):
    pass

# src/modules/finance/models.py
class Invoice(models.Model):
    billable_entity = models.ForeignKey(BillableEntity, ...)
```

---

## 7. Benefits of Boundary Enforcement

### 7.1 Measurable Improvements

- **Test Coverage:** Services can be unit tested without Django request context
- **Refactoring Safety:** Changes to infrastructure don't break API layer
- **Code Review Efficiency:** Reviewers can quickly spot architectural violations
- **Onboarding Speed:** New developers understand flow by following layers

### 7.2 Long-Term Value

- **Migration Ready:** Can replace Celery with different task queue without touching API
- **Microservices Path:** Modules are already decoupled, making service extraction easier
- **Technical Debt Prevention:** Prevents "big ball of mud" anti-pattern

---

## 8. References

- [Coding Constitution - Section 4 (Architecture)](codingconstitution.md#4-architecture-constitution)
- [Coding Constitution - Section 15 (Enforcement)](codingconstitution.md#15-minimal-enforcement-plan-recommended)
- [Import Linter Documentation](https://import-linter.readthedocs.io/)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**Document Version:** 1.0
**Last Updated:** December 30, 2025
**Review Schedule:** Quarterly (with Constitution review)
