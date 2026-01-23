"""
Event Handlers for Clients Module

Handles domain events published by other modules (primarily CRM).
This breaks the circular dependency: clients module no longer imports from crm.models.

Key workflows:
1. ProposalAcceptedEvent → Create Client + Contract + Engagement
2. ClientCreatedEvent → Create default folders, send notifications

Architecture:
- Handlers are registered via @subscribe_to decorator
- Handlers use service layer (when available) or direct model access
- Handlers are transactional and idempotent where possible
"""

import logging

from django.db import transaction
from django.utils import timezone

from modules.events import (
    subscribe_to,
    publish_event,
    ProposalAcceptedEvent,
    ClientCreatedEvent,
    ProjectCreatedEvent,
)
from modules.clients.models import Client, ClientEngagement

logger = logging.getLogger(__name__)


@subscribe_to(ProposalAcceptedEvent)
@transaction.atomic
def handle_proposal_accepted(event: ProposalAcceptedEvent):
    """
    Create client and engagement when a proposal is accepted.
    
    Routes based on proposal_type:
    - 'prospective_client': Create new Client
    - 'update_client' or 'renewal_client': Create new Engagement for existing client
    
    This replaces the Django signal-based workflow in clients/signals.py.
    """
    logger.info(
        f"Handling ProposalAcceptedEvent: proposal_id={event.proposal_id}, "
        f"type={event.proposal_type}, firm_id={event.firm_id}"
    )
    
    if event.proposal_type == "prospective_client":
        _create_client_from_proposal(event)
    elif event.proposal_type in ["update_client", "renewal_client"]:
        _create_engagement_from_proposal(event)
    else:
        logger.warning(f"Unknown proposal_type: {event.proposal_type}")


def _create_client_from_proposal(event: ProposalAcceptedEvent):
    """
    Create a new Client from an accepted prospective_client proposal.
    
    ARCHITECTURE NOTE:
    This function currently imports crm.models.Proposal to fetch additional data
    not included in the event. This represents a TEMPORARY one-way dependency
    while we migrate from signals to events.
    
    FUTURE IMPROVEMENT (Priority 2):
    To fully eliminate this dependency, we should:
    1. Enrich ProposalAcceptedEvent with all necessary prospect/proposal data, OR
    2. Use a repository pattern with dependency injection, OR
    3. Accept this as a read-only downstream dependency (clients can query
       crm data for enrichment without creating circular coupling)
    
    The key architectural win is that CRM no longer depends on clients module.
    The dependency now flows ONE WAY: clients → crm (read-only queries).
    This enables independent CRM module evolution and testing.
    """
    # TEMPORARY: Local imports for data enrichment
    # TODO (Priority 2): Remove by enriching event with prospect data
    from modules.crm.models import Proposal, Contract
    from modules.documents.models import Folder
    from modules.projects.models import Project
    
    try:
        proposal = Proposal.objects.select_related('prospect', 'firm').get(id=event.proposal_id)
    except Proposal.DoesNotExist:
        logger.error(f"Proposal {event.proposal_id} not found, cannot create client")
        return
    
    # Check if already converted (idempotency)
    if proposal.converted_to_engagement:
        logger.info(f"Proposal {event.proposal_id} already converted, skipping")
        return
    
    prospect = proposal.prospect
    
    # 1. Create Client from Prospect
    client = Client.objects.create(
        firm_id=event.firm_id,
        source_prospect=prospect,
        source_proposal=proposal,
        company_name=prospect.company_name,
        industry=prospect.industry,
        primary_contact_name=prospect.primary_contact_name,
        primary_contact_email=prospect.primary_contact_email,
        primary_contact_phone=prospect.primary_contact_phone,
        street_address=prospect.street_address,
        city=prospect.city,
        state=prospect.state,
        postal_code=prospect.postal_code,
        country=prospect.country,
        website=prospect.website,
        employee_count=prospect.employee_count,
        account_manager_id=event.created_by_id,
        client_since=timezone.now().date(),
        status="active",
        portal_enabled=event.enable_portal_on_acceptance,
        notes=f"Converted from Prospect #{prospect.id} via Proposal #{proposal.proposal_number}",
    )
    
    # Add proposal creator to assigned team
    client.assigned_team.add(event.created_by_id)
    
    logger.info(f"Created Client {client.id} from Proposal {event.proposal_id}")
    
    # 2. Create Contract (Engagement Letter)
    contract = Contract.objects.create(
        firm_id=event.firm_id,
        prospect=prospect,
        client=client,
        contract_type="engagement_letter",
        title=f"Engagement Letter - {client.company_name}",
        effective_date=timezone.now().date(),
        status="active",
        created_by_id=event.created_by_id,
    )
    
    # 3. Create Engagement
    engagement = ClientEngagement.objects.create(
        firm_id=event.firm_id,
        client=client,
        contract=contract,
        engagement_type=proposal.proposal_type,
        start_date=timezone.now().date(),
        status="active",
        total_value=proposal.total_value or 0,
        created_by_id=event.created_by_id,
    )
    
    # 4. Link proposal to engagement
    proposal.converted_to_engagement = engagement
    proposal.save(update_fields=['converted_to_engagement'])
    
    # 5. Create default client folder structure
    root_folder = Folder.objects.create(
        firm_id=event.firm_id,
        name=client.company_name,
        parent=None,
        client=client,
        folder_type="client_root",
        created_by_id=event.created_by_id,
    )
    
    Folder.objects.bulk_create([
        Folder(
            firm_id=event.firm_id,
            name="Contracts",
            parent=root_folder,
            client=client,
            folder_type="contracts",
            created_by_id=event.created_by_id,
        ),
        Folder(
            firm_id=event.firm_id,
            name="Deliverables",
            parent=root_folder,
            client=client,
            folder_type="deliverables",
            created_by_id=event.created_by_id,
        ),
        Folder(
            firm_id=event.firm_id,
            name="Shared Files",
            parent=root_folder,
            client=client,
            folder_type="shared",
            created_by_id=event.created_by_id,
        ),
    ])
    
    # 6. Create initial project if proposal has line items
    if proposal.line_items.exists():
        project = Project.objects.create(
            firm_id=event.firm_id,
            client=client,
            contract=contract,
            name=f"{proposal.title} - Implementation",
            description="Initial project created from accepted proposal",
            start_date=timezone.now().date(),
            status="planning",
            project_manager_id=event.created_by_id,
            created_by_id=event.created_by_id,
        )
        
        logger.info(f"Created Project {project.id} for Client {client.id}")
        
        # Publish event for other modules to react
        publish_event(ProjectCreatedEvent(
            project_id=project.id,
            firm_id=event.firm_id,
            client_id=client.id,
            project_name=project.name,
            created_by_id=event.created_by_id,
            correlation_id=event.correlation_id,
        ))
    
    # 7. Publish ClientCreatedEvent for other modules to react
    publish_event(ClientCreatedEvent(
        client_id=client.id,
        firm_id=event.firm_id,
        company_name=client.company_name,
        source_proposal_id=event.proposal_id,
        account_manager_id=event.created_by_id,
        correlation_id=event.correlation_id,
    ))
    
    logger.info(
        f"Successfully processed ProposalAcceptedEvent: "
        f"Created Client {client.id}, Contract {contract.id}, Engagement {engagement.id}"
    )


def _create_engagement_from_proposal(event: ProposalAcceptedEvent):
    """
    Create new Engagement for existing client (update or renewal).
    
    For update_client or renewal_client proposals, the client already exists.
    
    ARCHITECTURE NOTE:
    See _create_client_from_proposal for explanation of temporary imports.
    This will be eliminated in Priority 2 improvements.
    """
    # TEMPORARY: Local imports for data enrichment
    # TODO (Priority 2): Remove by enriching event with prospect data
    from modules.crm.models import Proposal, Contract
    
    try:
        proposal = Proposal.objects.select_related('prospect', 'firm').get(id=event.proposal_id)
    except Proposal.DoesNotExist:
        logger.error(f"Proposal {event.proposal_id} not found, cannot create engagement")
        return
    
    # Check if already converted (idempotency)
    if proposal.converted_to_engagement:
        logger.info(f"Proposal {event.proposal_id} already converted, skipping")
        return
    
    # Find existing client (should be linked to prospect)
    prospect = proposal.prospect
    try:
        client = Client.objects.get(firm_id=event.firm_id, source_prospect=prospect)
    except Client.DoesNotExist:
        logger.error(
            f"No existing client found for prospect {prospect.id}, "
            f"cannot create engagement for {event.proposal_type}"
        )
        return
    
    # Create Contract
    contract = Contract.objects.create(
        firm_id=event.firm_id,
        prospect=prospect,
        client=client,
        contract_type="amendment" if event.proposal_type == "update_client" else "renewal",
        title=f"{event.proposal_type.replace('_', ' ').title()} - {client.company_name}",
        effective_date=timezone.now().date(),
        status="active",
        created_by_id=event.created_by_id,
    )
    
    # Create Engagement
    engagement = ClientEngagement.objects.create(
        firm_id=event.firm_id,
        client=client,
        contract=contract,
        engagement_type=event.proposal_type,
        start_date=timezone.now().date(),
        status="active",
        total_value=proposal.total_value or 0,
        created_by_id=event.created_by_id,
    )
    
    # Link proposal to engagement
    proposal.converted_to_engagement = engagement
    proposal.save(update_fields=['converted_to_engagement'])
    
    logger.info(
        f"Successfully processed {event.proposal_type} ProposalAcceptedEvent: "
        f"Created Contract {contract.id}, Engagement {engagement.id} for existing Client {client.id}"
    )
