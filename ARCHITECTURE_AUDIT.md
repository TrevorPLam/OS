# Diamond-Level Architecture Audit

**Repository:** TrevorPLam/OS  
**Audit Date:** 2026-01-23  
**Auditor:** Principal Software Architect  
**Scope:** System decomposition, dependency control, domain boundaries, evolution tolerance

---

## 1. Architectural Summary

This is a **Django-based modular monolith** serving the consulting/professional services vertical. The system is decomposed into 31 domain modules under `backend/modules/` with a thin REST API layer under `backend/api/`. The architecture employs a **modified three-tier pattern** where:

- **API Layer** (`api/*`) handles HTTP transport and serialization (thin)
- **Module Layer** (`modules/*`) contains Django models, business logic, and services
- **Infrastructure** (`config/*`) provides framework configuration and cross-cutting concerns

The system enforces multi-tenancy through a foundational `Firm` model (TIER 0) that every business entity must reference. An `.importlinter` configuration attempts to enforce architectural boundaries programmatically, defining layers and forbidden dependencies. However, **the actual implementation exhibits partial pattern compliance with significant structural drift**, particularly around:

1. **Cross-module coupling** through direct model imports in signals, serializers, and business logic
2. **Bidirectional dependencies** between domain modules (clients ↔ crm ↔ projects)
3. **Inconsistent service layer** usage—some modules use dedicated services (e.g., `S3Service`, `EnrichmentService`) while others embed business logic directly in models, signals, or view layers
4. **Framework-coupled domain logic** with Django ORM queries, signals, and middleware tightly integrated into business workflows

The architecture demonstrates **intent toward domain-driven boundaries** with explicit module isolation and TIER-based scoping commentary, but the boundaries are **conceptual rather than structural**—they depend on developer discipline rather than compile-time or runtime enforcement beyond import linting.

---

## 2. Architectural Strengths

### **Explicit Multi-Tenancy Foundation (TIER 0)**
- The `modules.firm` package provides a clear, mandatory tenant boundary
- All domain models explicitly reference `firm = ForeignKey('firm.Firm')` with CASCADE deletion
- `FirmScopedQuerySet` and `FirmScopedMixin` enforce tenant isolation at the query level
- This structural enforcement prevents accidental cross-tenant data leakage
- **Why it matters:** Multi-tenancy is the hardest architectural property to retrofit. Having it structural from inception prevents entire classes of security and data isolation bugs.

### **API Layer Separation**
- The `backend/api/` layer is thin and purely handles transport/serialization
- Zero business logic in ViewSets—they delegate to model methods or services
- API modules never import from each other (no `api.crm` importing `api.clients`)
- Clean unidirectional dependency: API → modules (never reverse)
- **Why it matters:** This prevents the API layer from becoming a "God layer" that orchestrates business logic. Change to API contracts (REST → GraphQL) would be localized.

### **Explicit Module Granularity**
- 31 distinct domain modules with clear business responsibilities
- Each module contains its own models, migrations, admin, views, serializers
- Module names map directly to business capabilities: `crm`, `clients`, `projects`, `finance`, `calendar`
- **Why it matters:** Fine-grained modules provide natural boundaries for future extraction (monolith → microservices) if scale demands it. Each module can evolve independently in theory.

### **Documented Architectural Intent**
- `.importlinter` configuration explicitly codifies forbidden dependencies
- In-code comments reference TIER levels and multi-tenancy requirements
- Consistent use of docstrings explaining domain concepts and workflows
- **Why it matters:** Makes architectural rules discoverable to AI agents and new developers, reducing accidental violations.

### **Service Layer Emergence**
- Several modules demonstrate proper service layer patterns:
  - `modules.documents.services.S3Service` encapsulates AWS interactions
  - `modules.crm.enrichment_service` abstracts third-party enrichment APIs
  - `modules.calendar.*_service.py` files isolate external calendar integrations
- Services are stateless, testable in isolation, and hide infrastructure details
- **Why it matters:** Services provide proper abstraction boundaries that models cannot. They enable dependency inversion and make testing/mocking feasible.

---

## 3. Architectural Violations & Risks

### **CRITICAL: Circular Cross-Module Dependencies**

**Evidence:**
```
clients/signals.py: imports crm.models.{Proposal, Contract}, projects.models.Project
clients/serializers.py: imports crm.models.{Proposal, Contract}, projects.models.{Project, Task}
clients/views.py: imports crm.models.{Proposal, Contract}, projects.models.{Project, Task}
clients/health_score_calculator.py: imports projects.models.Project
crm/views.py: imports clients.permissions.DenyPortalAccess
crm/signals.py: imports projects.models.Project
crm/models/deals.py: imports projects.models.Project
projects/models.py: imports crm.models.Contract
```

**Structural Problem:**  
Modules `clients`, `crm`, and `projects` have **bidirectional dependencies**. Specifically:
- `clients` → `crm` (imports Proposal/Contract to create clients from proposals)
- `crm` → `clients` (imports permissions, conceptually clients are "downstream" of crm)
- `clients` → `projects` (imports Project/Task for health score calculation)
- `crm` → `projects` (imports Project in signals and deal models)
- `projects` → `crm` (imports Contract to link projects to contracts)

**Long-term Risk:**
1. **Impossible Module Extraction**: Cannot decompose into microservices—circular references prevent clean boundaries
2. **Fragile Change Propagation**: A change in CRM models ripples to clients, which ripples to projects, which ripples back to CRM
3. **Merge Conflict Multiplication**: Multiple teams working on interconnected modules will collide constantly
4. **Testing Nightmare**: Cannot unit test `clients.health_score_calculator` without standing up CRM and Projects models
5. **AI Context Explosion**: AI agents must load all three modules simultaneously to understand any one of them

**Root Cause:**  
The architecture conflates **lifecycle relationships** (proposals → clients → projects) with **module dependencies**. The CRM-to-Client workflow is modeled as direct Python imports and Django signals rather than domain events or an orchestration layer.

---

### **HIGH: Business Logic Scattered Across Layers**

**Evidence:**
- `modules/clients/signals.py`: 300+ lines of workflow orchestration (proposal acceptance → client creation → project creation)
- `modules/clients/health_score_calculator.py`: Complex scoring algorithm mixing ORM queries, timedelta calculations, and business rules
- `modules/crm/lead_scoring.py`: Scoring logic directly in module root, not in services/
- `modules/clients/health_score_views.py`: ViewSet contains custom actions that duplicate logic from calculator

**Structural Problem:**  
No consistent pattern for **where business logic lives**. It's fragmented across:
1. **Signals** (workflow orchestration)
2. **Standalone calculator/scorer classes** (not in services/)
3. **Model methods** (some models have `.accept()`, `.convert()` methods)
4. **View custom actions** (some logic duplicated in API layer)

**Long-term Risk:**
1. **Duplication**: Same logic implemented multiple times (health score in calculator + view)
2. **Inconsistent Testing**: No single place to test "client conversion from proposal" workflow
3. **Hidden Side Effects**: Django signals execute implicitly—difficult to trace execution flow
4. **Impossible Replay**: Cannot re-run business logic without triggering signals/side effects

---

### **HIGH: Framework Coupling in Domain Logic**

**Evidence:**
```python
# modules/clients/signals.py - Django signal directly orchestrates business workflow
@receiver(post_save, sender=Proposal)
def process_accepted_proposal(sender, instance, created, **kwargs):
    if instance.status != "accepted":
        return
    # 150 lines of business logic here
    client = Client.objects.create(...)
    contract = Contract.objects.create(...)
    project = Project.objects.create(...)

# modules/clients/health_score_calculator.py - Direct ORM queries in business logic
def _calculate_engagement_score(self) -> int:
    from modules.projects.models import Project
    projects = Project.objects.filter(client=self.client, created_at__gte=self.lookback_date)
```

**Structural Problem:**  
Core business workflows are **tightly coupled to Django's ORM and signal framework**:
1. Proposal → Client conversion cannot be triggered outside Django's save() lifecycle
2. Health score calculation requires Django ORM (cannot test with in-memory objects)
3. Signals fire implicitly—no explicit "process proposal" entry point visible in API

**Long-term Risk:**
1. **Untestable Without Django**: Cannot unit test workflows without database
2. **Impossible Migration**: Cannot port business logic to different framework/language
3. **Performance Ceiling**: ORM abstractions prevent query optimization
4. **Unclear Entry Points**: AI agents cannot discover "how to convert a proposal" without reading signal code

---

### **MEDIUM: Missing Abstraction for Cross-Module Communication**

**Evidence:**
- Modules communicate via **direct model imports** (`from modules.crm.models import Proposal`)
- Modules communicate via **Django signals** (implicit, event-driven)
- No explicit **domain events**, **message bus**, or **orchestration layer**

**Structural Problem:**  
When `crm` needs to notify `clients` that a proposal was accepted, it uses Django signals. This creates:
1. **Implicit coupling**: `clients.signals` must know about `crm.Proposal` model structure
2. **Order dependency**: Signal handlers execute in registration order (fragile)
3. **No replay mechanism**: Cannot re-trigger workflows without saving models

**Long-term Risk:**
1. **Cannot Introduce Second Interface**: Adding a background worker or CLI tool requires duplicating signal logic
2. **Race Conditions**: Async signal processing (Celery) can cause inconsistent state
3. **Difficult Testing**: Must mock Django's signal dispatch mechanism
4. **Hidden Business Rules**: Workflow logic buried in signal handlers, not discoverable in API or services

---

### **MEDIUM: Inconsistent Service Layer Adoption**

**Evidence:**
- **Well-abstracted services exist**:
  - `modules.documents.services.S3Service` (AWS abstraction)
  - `modules.crm.enrichment_service` (data enrichment)
  - `modules.calendar.*_service.py` (multiple calendar integration services)
- **Business logic NOT in services**:
  - `modules.clients.health_score_calculator` (standalone class, not a service)
  - `modules.clients.contact_merger` (utility, not a service)
  - `modules.crm.lead_scoring` (logic in module root)

**Structural Problem:**  
No consistent convention for when to use a service vs. a utility class vs. model methods vs. signals.

**Long-term Risk:**
1. **Inconsistent Testing**: Services can be mocked/stubbed, utilities cannot
2. **Difficult Discovery**: AI agents don't know where to look for business logic
3. **Missed Abstraction Opportunities**: Calculator classes should be services to enable dependency injection

---

### **MEDIUM: Import Linter Configuration Gaps**

**Evidence from `.importlinter`:**
```ini
[importlinter:contract:4]
name = API layer must not import infrastructure directly (async tasks, signals)
source_modules = src.api
forbidden_modules =
    src.modules.*.tasks
    src.modules.*.signals
    celery
```

**Structural Problem:**
1. Configuration uses `src.*` paths but actual code is under `backend/*` (path mismatch)
2. No contract preventing `modules.clients` → `modules.crm` circular dependency
3. Contract #3 defines "independence" between crm/finance/projects/documents/clients/calendar but doesn't enforce it (all violate)
4. No enforcement of service layer boundaries (e.g., preventing model layer from importing Django ORM in services)

**Long-term Risk:**
1. **False Sense of Security**: Import linter runs but doesn't catch actual violations
2. **Drift**: As violations accumulate, linter config becomes ignored rather than updated
3. **AI Confusion**: AI agents see forbidden rules but observe code violating them

---

## 4. Diamond-Level Gaps

To achieve **Diamond-Level Architecture**, the system must address:

### **Gap 1: Non-Structural Boundaries**
- **Current State**: Module boundaries are conceptual (folder structure + import linter)
- **Required**: Boundaries must be **compile-time or runtime enforced**
- **Missing**: No plugin architecture, no explicit interfaces, no dependency injection container
- **Why it matters**: Developer discipline is insufficient for solo + AI development

### **Gap 2: Bidirectional Dependencies**
- **Current State**: Circular imports between clients ↔ crm ↔ projects
- **Required**: Strictly unidirectional dependency flow (high-level → low-level)
- **Missing**: Domain events or orchestration layer to decouple workflows
- **Why it matters**: Cannot extract modules, cannot test in isolation

### **Gap 3: Framework-Coupled Domain**
- **Current State**: Business logic embedded in Django signals, ORM queries, model methods
- **Required**: Pure domain logic in language primitives, framework at boundaries only
- **Missing**: Explicit domain model (entities, value objects, aggregates) separate from ORM models
- **Why it matters**: Cannot port logic, cannot test without database

### **Gap 4: Implicit Workflows**
- **Current State**: Business workflows triggered by Django signals (implicit)
- **Required**: Explicit entry points for workflows (e.g., `convert_proposal_to_client()` service method)
- **Missing**: Service/use case layer that orchestrates workflows explicitly
- **Why it matters**: AI agents and developers cannot discover how to trigger workflows

### **Gap 5: Inconsistent Abstraction Layers**
- **Current State**: Some modules have services (documents, crm enrichment), others don't (clients health score)
- **Required**: Consistent layering: API → Services/Use Cases → Domain → Infrastructure
- **Missing**: Service layer adoption across all modules
- **Why it matters**: Inconsistency forces developers to guess where to put new logic

### **Gap 6: No Change Impact Analysis**
- **Current State**: Cannot predict ripple effects of changes
- **Required**: Dependency graph that proves change locality
- **Missing**: Module independence (can change clients without touching crm/projects)
- **Why it matters**: Solo operator must minimize cognitive load and merge conflicts

---

## 5. High-Leverage Structural Improvements

### **Improvement 1: Introduce Domain Events to Break Circular Dependencies**

**Problem:** `clients.signals` imports `crm.models.Proposal` and `projects.models.Project` to orchestrate workflows.

**Solution:**  
1. Create `modules/events/` package with domain event classes:
   ```python
   # modules/events/domain_events.py
   @dataclass
   class ProposalAcceptedEvent:
       proposal_id: int
       firm_id: int
       prospect_id: int
       accepted_at: datetime
       enable_portal: bool
   ```

2. Replace Django signals with explicit event publishing:
   ```python
   # modules/crm/models.py
   from modules.events import publish_event, ProposalAcceptedEvent
   
   class Proposal(models.Model):
       def accept(self, user):
           self.status = "accepted"
           self.save()
           publish_event(ProposalAcceptedEvent(
               proposal_id=self.id,
               firm_id=self.firm_id,
               ...
           ))
   ```

3. Create event handlers in `clients` module that subscribe to events:
   ```python
   # modules/clients/event_handlers.py
   from modules.events import subscribe_to
   
   @subscribe_to(ProposalAcceptedEvent)
   def create_client_from_proposal(event: ProposalAcceptedEvent):
       # Business logic here - no direct import of Proposal model
   ```

**Impact:**
- **Breaks circular dependency**: `clients` no longer imports `crm.models`
- **Explicit workflows**: Event handlers are discoverable and testable
- **Enables replay**: Can re-publish events to re-run workflows
- **Change locality**: CRM changes only require updating event schema if contract changes

**Effort:** Medium (1-2 days to implement event bus, 2-3 days to migrate existing signals)

---

### **Improvement 2: Extract Service Layer for All Business Logic**

**Problem:** Business logic scattered across signals, calculators, model methods, view actions.

**Solution:**  
1. Create `services/` subfolder in each module:
   ```
   modules/clients/
       services/
           __init__.py
           client_service.py       # create_from_proposal, update_status
           health_score_service.py # calculate_health_score
           engagement_service.py   # track_engagement
   ```

2. Move logic from signals → services:
   ```python
   # modules/clients/services/client_service.py
   class ClientService:
       def create_from_proposal(self, event: ProposalAcceptedEvent) -> Client:
           # Pure business logic, testable without Django signals
           # Queries via repository pattern, not direct ORM
   ```

3. Services depend on repositories (not direct ORM):
   ```python
   # modules/clients/repositories.py
   class ClientRepository:
       def save(self, client: Client) -> Client:
           # Encapsulates Django ORM
   ```

**Impact:**
- **Testable**: Services can be unit tested with mock repositories
- **Discoverable**: All workflows visible in service methods
- **Reusable**: Can call from API, CLI, background jobs, tests
- **Framework-independent**: Services use pure Python, repositories encapsulate Django

**Effort:** High (5-7 days to extract and migrate existing logic)

---

### **Improvement 3: Enforce Unidirectional Dependencies with Dependency Layers**

**Problem:** Import linter config doesn't match actual code paths, violations ignored.

**Solution:**  
1. Define explicit dependency layers:
   ```
   Layer 0 (Foundation): firm, core
   Layer 1 (Shared Kernel): events, repositories
   Layer 2 (Domain Modules): crm, clients, projects, finance, documents (CANNOT IMPORT EACH OTHER)
   Layer 3 (Services): modules/*/services/ (can import Layer 2, cannot import other modules)
   Layer 4 (API): api/* (imports Layer 2 & 3)
   ```

2. Update `.importlinter` to enforce:
   ```ini
   [importlinter:contract:layer-independence]
   type = independence
   modules =
       modules.crm
       modules.clients
       modules.projects
       modules.finance
       modules.documents
   # These must NOT import each other
   
   [importlinter:contract:domain-no-services]
   type = forbidden
   source_modules = modules.crm.services
   forbidden_modules =
       modules.clients
       modules.projects
   ```

3. Fix path mismatch (change `src.*` → `modules.*`, `backend.*`)

**Impact:**
- **Compile-time enforcement**: CI fails if circular dependencies introduced
- **Clear rules**: AI agents can infer "where can I import from?" by layer
- **Prevents drift**: Violations blocked before merge

**Effort:** Low (1 day to update config, 2 days to fix existing violations)

---

### **Improvement 4: Introduce Orchestration Layer for Cross-Module Workflows**

**Problem:** When workflows span multiple modules (proposal → client → project), logic is split across signals.

**Solution:**  
1. Create `modules/orchestration/workflows/` for cross-cutting workflows:
   ```python
   # modules/orchestration/workflows/client_onboarding.py
   from modules.events import subscribe_to, ProposalAcceptedEvent
   from modules.clients.services import ClientService
   from modules.projects.services import ProjectService
   
   class ClientOnboardingOrchestrator:
       def __init__(self, client_service, project_service):
           self.client_service = client_service
           self.project_service = project_service
       
       def handle_proposal_accepted(self, event: ProposalAcceptedEvent):
           # Explicit orchestration
           client = self.client_service.create_from_proposal(event)
           if event.create_initial_project:
               project = self.project_service.create_onboarding_project(client)
           # Publish further events if needed
   ```

2. Orchestrators live in dedicated module, preventing circular dependencies
3. Orchestrators are explicit—no hidden signal chains

**Impact:**
- **Visible workflows**: Easy to understand "what happens when proposal accepted?"
- **Testable**: Mock services, test orchestrator in isolation
- **Flexible**: Add new steps without modifying crm/clients/projects modules
- **AI-friendly**: Single file contains entire workflow

**Effort:** Medium (3-4 days to create orchestration layer, migrate signal workflows)

---

### **Improvement 5: Separate Domain Models from Django ORM Models**

**Problem:** Domain logic tightly coupled to Django ORM (cannot test without database).

**Solution:**  
1. Create pure domain entities in `modules/*/domain/` folders:
   ```python
   # modules/clients/domain/entities.py
   @dataclass
   class ClientEntity:
       id: Optional[int]
       firm_id: int
       company_name: str
       status: ClientStatus
       
       def activate(self):
           if self.status == ClientStatus.TERMINATED:
               raise ValueError("Cannot reactivate terminated client")
           self.status = ClientStatus.ACTIVE
   ```

2. Django models become persistence layer only:
   ```python
   # modules/clients/models/clients.py
   class Client(models.Model):
       # Just field definitions, no business logic
       
       def to_entity(self) -> ClientEntity:
           return ClientEntity(id=self.id, firm_id=self.firm_id, ...)
       
       @staticmethod
       def from_entity(entity: ClientEntity) -> 'Client':
           return Client(id=entity.id, firm_id=entity.firm_id, ...)
   ```

3. Services operate on domain entities, not ORM models:
   ```python
   # modules/clients/services/client_service.py
   def activate_client(self, client_id: int) -> ClientEntity:
       client_entity = self.repository.get_by_id(client_id)
       client_entity.activate()  # Pure logic, no ORM
       return self.repository.save(client_entity)
   ```

**Impact:**
- **Framework-independent**: Domain logic is pure Python
- **Testable**: Can instantiate entities without database
- **Portable**: Can migrate to different ORM/framework
- **Clear boundaries**: Domain layer vs. persistence layer explicit

**Effort:** Very High (10-15 days per module to extract domain models)

**Note:** This is the most invasive change and should be done incrementally, starting with one high-value module (e.g., `clients` or `crm`).

---

## 6. Final Verdict

### **Not Diamond-Level**

**Justification:**

While this architecture demonstrates **strong foundational patterns** (multi-tenancy, thin API layer, explicit module boundaries), it **fails Diamond-Level standards** due to:

1. **Circular Dependencies**: The `clients ↔ crm ↔ projects` dependency cycle is an **automatic disqualifier**. These modules cannot be tested in isolation, cannot be extracted, and changes cascade unpredictably.

2. **Framework Coupling**: Business logic is **tightly coupled to Django signals and ORM**, preventing testing without a database and making framework migration impossible. Diamond-Level requires domain logic to be **framework-agnostic**.

3. **Implicit Workflows**: Critical business workflows (proposal → client conversion) are **hidden in signal handlers** rather than explicit service methods. This violates the "predictable impact of change" requirement.

4. **Inconsistent Abstraction**: The partial adoption of service layers (documents, calendar) vs. direct model methods and signals (clients, crm) creates **architectural ambiguity**. Diamond-Level requires consistent, enforced patterns.

5. **Non-Structural Boundaries**: Module boundaries rely on developer discipline and import linting rather than **compile-time or runtime enforcement**. The import linter configuration itself has path mismatches and doesn't prevent observed violations.

**Current Level: "Structured Monolith with Architectural Intent"**

The system is **significantly better than typical Django applications**:
- Explicit multi-tenancy foundation (rare)
- Thin API layer with zero business logic (excellent)
- 31 well-named domain modules (good granularity)
- Some proper service layer usage (emerging pattern)

However, it requires **3-4 high-leverage structural improvements** (domain events, service extraction, dependency enforcement, orchestration layer) to reach Diamond-Level.

**Recommendation for Solo + AI Development:**

Given the **heavy AI-assisted development** context, the highest priority is:
1. **Fix circular dependencies** (Improvement 1) - Without this, AI agents will struggle with context window management
2. **Enforce unidirectional dependencies** (Improvement 3) - This makes architectural rules machine-checkable
3. **Extract service layer** (Improvement 2) - This makes workflows explicit and discoverable to AI

These three improvements would elevate the architecture to **"Near-Diamond with Controlled Risks"** and make it sustainable for solo operation with AI assistance.

---

**End of Audit**
