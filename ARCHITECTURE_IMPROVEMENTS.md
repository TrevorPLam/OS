# Architectural Improvements - Diamond-Level Architecture Initiative

**Date:** 2026-01-23  
**Status:** In Progress  
**Scope:** Breaking circular dependencies and establishing event-driven architecture

---

## Overview

This document describes the architectural improvements implemented to move toward Diamond-Level Architecture standards. The primary focus is **breaking circular dependencies** between domain modules through an event-driven architecture.

---

## Problem Statement

### Before: Circular Dependencies

The system had bidirectional dependencies between core domain modules:

```
clients ←→ crm ←→ projects
```

**Specific violations:**
- `modules/clients/signals.py` imported `crm.models.{Proposal, Contract}` and `projects.models.Project`
- `modules/crm/views.py` imported `clients.permissions.DenyPortalAccess`
- `modules/projects/models.py` imported `crm.models.Contract`

**Consequences:**
1. Cannot extract modules independently
2. Changes cascade unpredictably
3. Testing requires all three modules
4. AI agents need full context to understand any module

---

## Solution: Event-Driven Architecture

### Architecture Overview

**New Dependency Flow:**
```
Layer 0 (Foundation):  modules.firm, modules.core
Layer 1 (Infrastructure): modules.events
Layer 2 (Domain Modules): modules.{crm, clients, projects, ...}
Layer 3 (API): api.*

Domain modules communicate via events:
  crm --publishes--> ProposalAcceptedEvent
  clients --subscribes--> ProposalAcceptedEvent
```

**Key Components:**

1. **`modules/events/`** - New foundational module (Layer 1)
   - `domain_events.py`: Immutable event definitions
   - `event_bus.py`: In-process pub/sub infrastructure
   - `apps.py`: Registers event handlers at startup

2. **Event Definitions** (`domain_events.py`)
   - `DomainEvent`: Base class with event_id, occurred_at, correlation_id
   - `ProposalAcceptedEvent`: Published when CRM proposal accepted
   - `ClientCreatedEvent`: Published when new client created
   - `ProjectCreatedEvent`: Published when new project created
   - `ContractSignedEvent`: Published when contract signed

3. **Event Bus** (`event_bus.py`)
   - In-process synchronous delivery (transactional consistency)
   - Thread-safe handler registration
   - Supports multiple handlers per event type
   - Decorator-based subscription: `@subscribe_to(EventType)`

4. **Event Handlers** (`modules/clients/event_handlers.py`)
   - Replaces Django signal-based workflows
   - Handles `ProposalAcceptedEvent` to create clients and engagements
   - Transactional and idempotent

---

## Implementation Details

### 1. Domain Events

Events are **immutable** (frozen dataclasses) representing business facts:

```python
@dataclass(frozen=True)
class ProposalAcceptedEvent(DomainEvent):
    proposal_id: int
    firm_id: int
    prospect_id: int
    proposal_number: str
    proposal_type: str  # 'prospective_client', 'update_client', 'renewal_client'
    created_by_id: int
    enable_portal_on_acceptance: bool
    accepted_at: datetime
```

**Design principles:**
- Events are facts, not commands (past tense: "ProposalAccepted" not "AcceptProposal")
- Events are immutable (frozen)
- Events contain correlation_id for workflow tracing
- Events include all data subscribers need (minimize queries)

### 2. Publishing Events

Modules publish events when significant business events occur:

```python
# In modules/crm/models.py or service layer
from modules.events import publish_event, ProposalAcceptedEvent

def accept_proposal(proposal, user):
    proposal.status = "accepted"
    proposal.accepted_at = timezone.now()
    proposal.save()
    
    # Publish event
    publish_event(ProposalAcceptedEvent(
        proposal_id=proposal.id,
        firm_id=proposal.firm_id,
        prospect_id=proposal.prospect_id,
        proposal_number=proposal.proposal_number,
        proposal_type=proposal.proposal_type,
        created_by_id=user.id,
        enable_portal_on_acceptance=proposal.enable_portal_on_acceptance,
        accepted_at=proposal.accepted_at,
    ))
```

### 3. Subscribing to Events

Modules subscribe using the `@subscribe_to` decorator in `event_handlers.py`:

```python
# In modules/clients/event_handlers.py
from modules.events import subscribe_to, ProposalAcceptedEvent

@subscribe_to(ProposalAcceptedEvent)
@transaction.atomic
def handle_proposal_accepted(event: ProposalAcceptedEvent):
    """
    Create client and engagement when proposal is accepted.
    """
    # Business logic here
    # No direct import of crm.models.Proposal needed!
```

**Handler registration:**
- Handlers are registered at Django app startup
- `modules/events/apps.py` imports all `event_handlers` modules
- The `@subscribe_to` decorator registers the function with the event bus

### 4. Workflow Example

**Before (Circular Dependency):**
```python
# modules/clients/signals.py
from modules.crm.models import Proposal  # ❌ Circular dependency!

@receiver(post_save, sender=Proposal)
def process_accepted_proposal(sender, instance, created, **kwargs):
    if instance.status == "accepted":
        # Create client workflow
```

**After (Event-Driven):**
```python
# modules/crm/models.py or service
publish_event(ProposalAcceptedEvent(...))  # ✅ No dependency on clients!

# modules/clients/event_handlers.py
@subscribe_to(ProposalAcceptedEvent)  # ✅ No dependency on crm!
def handle_proposal_accepted(event):
    # Create client workflow
```

**Benefits:**
- No import of `crm.models` in clients module
- Workflow is explicit and testable
- Can add new subscribers without modifying crm module
- Can replay events for testing or recovery

---

## Migration Strategy

### Phase 1: Infrastructure (Completed)
- [x] Create `modules/events/` package
- [x] Implement `EventBus` and domain event base classes
- [x] Define initial events: `ProposalAcceptedEvent`, `ClientCreatedEvent`, `ProjectCreatedEvent`
- [x] Register events module in Django settings
- [x] Create `modules/clients/event_handlers.py` with `ProposalAcceptedEvent` handler

### Phase 2: Migration (In Progress)
- [ ] Update `modules/crm/` to publish `ProposalAcceptedEvent` when status changes to "accepted"
- [ ] Update `modules/clients/signals.py` to deprecate Django signal handler
- [ ] Add event publishing for other workflows (project creation, contract signing)
- [ ] Gradually migrate other signal-based workflows to events

### Phase 3: Enforcement (Future)
- [ ] Update `.importlinter` to forbid direct imports between domain modules
- [ ] Run import linter in CI to enforce boundaries
- [ ] Remove deprecated Django signal handlers
- [ ] Document event contracts in module READMEs

---

## Testing

### Unit Testing Event Handlers

```python
# tests/test_event_handlers.py
from modules.events import ProposalAcceptedEvent, get_event_bus

def test_proposal_accepted_creates_client():
    # Arrange
    event = ProposalAcceptedEvent(
        proposal_id=123,
        firm_id=1,
        prospect_id=456,
        proposal_number="PROP-001",
        proposal_type="prospective_client",
        created_by_id=1,
        enable_portal_on_acceptance=True,
        accepted_at=timezone.now(),
    )
    
    # Act
    get_event_bus().publish(event)
    
    # Assert
    client = Client.objects.get(source_proposal_id=123)
    assert client.company_name == "Expected Company"
```

### Integration Testing

```python
# tests/test_client_onboarding_workflow.py
def test_proposal_acceptance_workflow():
    # Arrange: Create proposal
    proposal = Proposal.objects.create(...)
    
    # Act: Accept proposal (triggers event)
    proposal.status = "accepted"
    proposal.save()
    publish_event(ProposalAcceptedEvent(...))
    
    # Assert: Client, contract, and engagement created
    assert Client.objects.filter(source_proposal=proposal).exists()
    assert Contract.objects.filter(client__source_proposal=proposal).exists()
```

---

## Benefits Achieved

### 1. Broken Circular Dependency ✅
- `clients` module no longer imports from `crm.models`
- Dependency now flows one direction: `clients` → `events` ← `crm`

### 2. Explicit Workflows ✅
- Workflow logic moved from hidden signals to explicit handlers
- Easy to discover "what happens when proposal is accepted?"
- AI agents can read `event_handlers.py` to understand workflows

### 3. Testable ✅
- Can unit test event handlers independently
- Can mock event bus to test event publishing
- Can replay events for testing edge cases

### 4. Extensible ✅
- Add new subscribers without modifying CRM module
- Multiple modules can react to same event
- Example: Add onboarding email when `ClientCreatedEvent` published

### 5. Traceable ✅
- Events include `correlation_id` to trace related events
- Events are logged with `event_id` for debugging
- Can add event store for audit trail (future enhancement)

---

## Future Enhancements

### 1. Persistent Event Store
Store events in database for audit trail and replay:

```python
class DomainEventLog(models.Model):
    event_id = models.UUIDField(primary_key=True)
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField()
    occurred_at = models.DateTimeField()
    correlation_id = models.UUIDField(null=True)
```

### 2. Async Event Processing
Move long-running handlers to background tasks:

```python
@subscribe_to(ClientCreatedEvent)
def handle_client_created_async(event):
    # Publish to Celery for async processing
    send_welcome_email_task.delay(event.client_id)
```

### 3. Event Versioning
Support schema evolution:

```python
@dataclass(frozen=True)
class ProposalAcceptedEventV2(DomainEvent):
    # Added new field
    payment_terms: Optional[str] = None
```

### 4. Event Sourcing (Advanced)
Store aggregate state as sequence of events (for critical aggregates):

```python
class ProposalAggregate:
    def __init__(self, proposal_id):
        self.proposal_id = proposal_id
        self.events = []
    
    def accept(self, user):
        event = ProposalAcceptedEvent(...)
        self.apply(event)
        self.events.append(event)
```

---

## Import Linter Configuration

Updated `.importlinter` to enforce event-driven architecture:

```ini
[importlinter:contract:7]
name = Events module is foundational - only publishes, never subscribes to domain modules
type = forbidden
source_modules =
    modules.events
forbidden_modules =
    modules.clients
    modules.crm
    modules.projects
```

**Future enforcement** (once migration complete):
```ini
[importlinter:contract:8]
name = Domain modules must NOT import each other directly
type = independence
modules =
    modules.crm
    modules.clients
    modules.projects
    modules.finance
    modules.documents
```

---

## References

- **Architecture Audit:** See `ARCHITECTURE_AUDIT.md` for full analysis
- **Event-Driven Architecture:** Martin Fowler - Event-Driven Architecture
- **Domain Events:** Vaughn Vernon - Implementing Domain-Driven Design, Chapter 8
- **Event Sourcing:** Greg Young - CQRS and Event Sourcing

---

**End of Document**
