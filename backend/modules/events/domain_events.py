"""
Domain Event Definitions

Immutable data structures representing significant business events.
Events are the contract between modules - they enable loose coupling.

Design principles:
1. Events are immutable (frozen dataclasses)
2. Events contain only data needed by subscribers (no behavior)
3. Events represent facts that have already occurred (past tense naming)
4. Events include timestamp and correlation ID for tracing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from django.utils import timezone


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.
    
    Attributes:
        event_id: Unique identifier for this event instance
        occurred_at: When the event occurred
        correlation_id: Links related events in a workflow
    """
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=timezone.now)
    correlation_id: Optional[UUID] = None
    
    def __str__(self):
        return f"{self.__class__.__name__}(event_id={self.event_id})"


@dataclass(frozen=True)
class ProposalAcceptedEvent(DomainEvent):
    """
    Published when a CRM proposal is accepted by a prospect.
    
    This event triggers client onboarding workflows without
    the CRM module needing to know about the clients module.
    
    Attributes:
        proposal_id: ID of the accepted proposal
        firm_id: Tenant context
        prospect_id: ID of the prospect who accepted
        proposal_number: Human-readable proposal reference
        proposal_type: 'prospective_client', 'update_client', or 'renewal_client'
        created_by_id: ID of staff member who created proposal
        enable_portal_on_acceptance: Whether to enable client portal
        accepted_at: When proposal was accepted
    """
    proposal_id: int
    firm_id: int
    prospect_id: int
    proposal_number: str
    proposal_type: str
    created_by_id: int
    enable_portal_on_acceptance: bool
    accepted_at: datetime


@dataclass(frozen=True)
class ClientCreatedEvent(DomainEvent):
    """
    Published when a new client is created.
    
    Other modules can react to new clients (e.g., send welcome email,
    create default documents, schedule onboarding).
    
    Attributes:
        client_id: ID of the created client
        firm_id: Tenant context
        company_name: Client company name
        source_proposal_id: Optional ID of originating proposal
        account_manager_id: ID of assigned account manager
    """
    client_id: int
    firm_id: int
    company_name: str
    source_proposal_id: Optional[int] = None
    account_manager_id: Optional[int] = None


@dataclass(frozen=True)
class ProjectCreatedEvent(DomainEvent):
    """
    Published when a new project is created.
    
    Allows other modules to react (e.g., create default tasks,
    send notifications, initialize project workspace).
    
    Attributes:
        project_id: ID of the created project
        firm_id: Tenant context
        client_id: ID of client this project belongs to
        project_name: Human-readable project name
        created_by_id: ID of staff member who created project
    """
    project_id: int
    firm_id: int
    client_id: int
    project_name: str
    created_by_id: int


@dataclass(frozen=True)
class ContractSignedEvent(DomainEvent):
    """
    Published when a contract is signed.
    
    Triggers billing setup, project initialization, and other workflows.
    
    Attributes:
        contract_id: ID of the signed contract
        firm_id: Tenant context
        client_id: Optional client ID if contract is post-sale
        prospect_id: Optional prospect ID if contract is pre-sale
        contract_type: Type of contract
        signed_at: When contract was signed
    """
    contract_id: int
    firm_id: int
    client_id: Optional[int] = None
    prospect_id: Optional[int] = None
    contract_type: Optional[str] = None
    signed_at: datetime
