"""
Event Bus Infrastructure

Provides in-process event publication and subscription.
Enables loose coupling between domain modules.

Architecture:
- Synchronous in-process delivery (for transactional consistency)
- Can be extended to async/persistent delivery via Celery
- Thread-safe using locks
- Supports multiple handlers per event type

Usage:
    # Publishing
    from modules.events import publish_event, ProposalAcceptedEvent
    
    event = ProposalAcceptedEvent(
        proposal_id=proposal.id,
        firm_id=proposal.firm_id,
        ...
    )
    publish_event(event)
    
    # Subscribing
    from modules.events import subscribe_to, ProposalAcceptedEvent
    
    @subscribe_to(ProposalAcceptedEvent)
    def handle_proposal_accepted(event: ProposalAcceptedEvent):
        # React to event
        pass
"""

import logging
from collections import defaultdict
from threading import Lock
from typing import Any, Callable, Dict, List, Type

from .domain_events import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-process event bus for domain event distribution.
    
    Implements the Observer pattern for domain events.
    Handlers are executed synchronously in registration order.
    """
    
    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = defaultdict(list)
        self._lock = Lock()
    
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], Any]) -> None:
        """
        Register a handler for an event type.
        
        Args:
            event_type: Class of event to handle
            handler: Callable that accepts event instance
        """
        with self._lock:
            self._handlers[event_type].append(handler)
            logger.info(f"Subscribed {handler.__name__} to {event_type.__name__}")
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all registered handlers.
        
        Handlers are executed synchronously in registration order.
        If a handler raises an exception, subsequent handlers are still executed,
        but the exception is logged and re-raised after all handlers complete.
        
        Args:
            event: Event instance to publish
        
        Raises:
            Exception: If any handler raised an exception (first exception encountered)
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        logger.info(f"Publishing {event_type.__name__} (event_id={event.event_id}) to {len(handlers)} handlers")
        
        exceptions = []
        for handler in handlers:
            try:
                logger.debug(f"Executing handler {handler.__name__} for {event_type.__name__}")
                handler(event)
            except Exception as e:
                logger.exception(f"Handler {handler.__name__} failed for {event_type.__name__}: {e}")
                exceptions.append((handler, e))
        
        # If any handler failed, raise the first exception
        if exceptions:
            handler, exception = exceptions[0]
            raise exception
    
    def clear_handlers(self, event_type: Type[DomainEvent] = None) -> None:
        """
        Clear handlers for testing purposes.
        
        Args:
            event_type: If specified, clear only handlers for this event type.
                       If None, clear all handlers.
        """
        with self._lock:
            if event_type:
                self._handlers[event_type].clear()
            else:
                self._handlers.clear()


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return _event_bus


def publish_event(event: DomainEvent) -> None:
    """
    Publish a domain event to all subscribers.
    
    Args:
        event: Event to publish
    """
    _event_bus.publish(event)


def subscribe_to(event_type: Type[DomainEvent]) -> Callable:
    """
    Decorator to subscribe a function to an event type.
    
    Usage:
        @subscribe_to(ProposalAcceptedEvent)
        def my_handler(event: ProposalAcceptedEvent):
            # Handle event
            pass
    
    Args:
        event_type: Type of event to subscribe to
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable[[DomainEvent], Any]) -> Callable:
        _event_bus.subscribe(event_type, func)
        return func
    return decorator
