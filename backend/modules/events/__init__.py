"""
Domain Events Module

Provides infrastructure for domain-driven event-based communication between modules.
This breaks circular dependencies by allowing modules to communicate through events
rather than direct imports.

Key concepts:
- Domain events are immutable data structures representing business facts
- Publishers emit events without knowledge of subscribers
- Subscribers handle events without direct dependency on publishers
- Events enable workflow orchestration without tight coupling
"""

from .domain_events import (
    DomainEvent,
    ProposalAcceptedEvent,
    ClientCreatedEvent,
    ProjectCreatedEvent,
    ContractSignedEvent,
)
from .event_bus import (
    EventBus,
    publish_event,
    subscribe_to,
    get_event_bus,
)

__all__ = [
    'DomainEvent',
    'ProposalAcceptedEvent',
    'ClientCreatedEvent',
    'ProjectCreatedEvent',
    'ContractSignedEvent',
    'EventBus',
    'publish_event',
    'subscribe_to',
    'get_event_bus',
]
