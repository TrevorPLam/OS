"""
Client Signals - Automated workflows for client management.

Key workflows when Proposal is accepted:
1. prospective_client: Create new Client + Contract + Engagement
2. update_client: Create new Contract/Engagement for existing client
3. renewal_client: Create new Contract/Engagement version (renewal)
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from modules.crm.models import Proposal, Contract
from modules.clients.models import Client, ClientEngagement
from modules.projects.models import Project
from modules.documents.models import Folder


@receiver(post_save, sender=Proposal)
def process_accepted_proposal(sender, instance, created, **kwargs):
    """
    Process accepted proposals based on type.

    Handles 3 scenarios:
    - prospective_client: New business (creates Client)
    - update_client: Expansion/upsell (creates new Engagement)
    - renewal_client: Renewal (creates new Engagement version)
    """
    # Only process if status changed to 'accepted' and not already converted
    if instance.status != 'accepted' or instance.converted_to_engagement:
        return

    # Route based on proposal type
    if instance.proposal_type == 'prospective_client':
        _handle_new_client(instance)
    elif instance.proposal_type in ['update_client', 'renewal_client']:
        _handle_client_engagement(instance)


def _handle_new_client(proposal):
    """
    Handle prospective_client proposals - Create new Client.

    This is the bridge from pre-sale (Prospect) to post-sale (Client).
    """
    # 1. Create Client from Prospect
    client = Client.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        source_prospect=proposal.prospect,
        source_proposal=proposal,
        company_name=proposal.prospect.company_name,
        industry=proposal.prospect.industry,
        primary_contact_name=proposal.prospect.primary_contact_name,
        primary_contact_email=proposal.prospect.primary_contact_email,
        primary_contact_phone=proposal.prospect.primary_contact_phone,
        street_address=proposal.prospect.street_address,
        city=proposal.prospect.city,
        state=proposal.prospect.state,
        postal_code=proposal.prospect.postal_code,
        country=proposal.prospect.country,
        website=proposal.prospect.website,
        employee_count=proposal.prospect.employee_count,
        account_manager=proposal.created_by,
        client_since=timezone.now().date(),
        status='active',
        portal_enabled=proposal.enable_portal_on_acceptance,
        notes=f"Converted from Prospect #{proposal.prospect.id} via Proposal #{proposal.proposal_number}"
    )

    # Add proposal creator to assigned team
    client.assigned_team.add(proposal.created_by)

    # 2. Create Contract (Engagement Letter)
    contract = Contract.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
        proposal=proposal,
        contract_number=f"ENG-{proposal.proposal_number}",
        title=proposal.title,
        description=proposal.description,
        status='active',
        total_value=proposal.total_value,
        currency=proposal.currency,
        payment_terms='net_30',
        start_date=proposal.estimated_start_date or timezone.now().date(),
        end_date=proposal.estimated_end_date or (timezone.now().date() + timezone.timedelta(days=90)),
        signed_date=timezone.now().date(),
        signed_by=proposal.created_by,
        notes=f"Initial engagement from Proposal #{proposal.proposal_number}"
    )

    # 3. Create ClientEngagement record (version 1)
    ClientEngagement.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
        contract=contract,
        status='current',
        version=1,
        parent_engagement=None,  # No parent for initial engagement
        start_date=contract.start_date,
        end_date=contract.end_date,
        contracted_value=contract.total_value,
        actual_revenue=0,
        notes="Initial engagement - new client"
    )

    # 4. Create initial Project (if configured)
    if proposal.auto_create_project:
        Project.objects.create(
            firm=proposal.firm,  # TIER 2: Explicit tenant context
            client=client,
            contract=contract,
            project_manager=proposal.created_by,
            project_code=f"PROJ-{proposal.proposal_number}",
            name=f"{proposal.title} - Implementation",
            description=proposal.description,
            status='planning',
            billing_type='time_and_materials',
            budget=proposal.total_value,
            start_date=contract.start_date,
            end_date=contract.end_date,
            notes=f"Auto-created from Proposal #{proposal.proposal_number}"
        )

    # 5. Setup Document Folders
    root_folder = Folder.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
        parent=None,
        name="Root",
        description="Client root folder",
        visibility='internal',
        created_by=proposal.created_by
    )

    Folder.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
        parent=root_folder,
        name="Shared Documents",
        description="Documents shared with client portal",
        visibility='client',
        created_by=proposal.created_by
    )

    Folder.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
        parent=root_folder,
        name="Client Uploads",
        description="Documents uploaded by client",
        visibility='client',
        created_by=proposal.created_by
    )

    Folder.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
        parent=root_folder,
        name="Internal Only",
        description="Internal team documents",
        visibility='internal',
        created_by=proposal.created_by
    )

    # 6. Mark Prospect as won
    proposal.prospect.pipeline_stage = 'won'
    proposal.prospect.won_date = timezone.now().date()
    proposal.prospect.save()

    # 7. Update Proposal
    proposal.accepted_at = timezone.now()
    proposal.converted_to_engagement = True
    proposal.save()

    print(f"✅ New Client: {client.company_name} (Proposal {proposal.proposal_number})")


def _handle_client_engagement(proposal):
    """
    Handle update_client and renewal_client proposals.

    Creates new Contract/Engagement for existing client.
    For renewals, links to previous engagement as parent.
    """
    client = proposal.client

    # Determine version number
    if proposal.proposal_type == 'renewal_client':
        # Get latest engagement to determine version
        latest_engagement = ClientEngagement.objects.filter(
            client=client
        ).order_by('-version').first()

        version = (latest_engagement.version + 1) if latest_engagement else 1
        parent_engagement = latest_engagement

        # Mark previous engagement as renewed
        if latest_engagement:
            latest_engagement.status = 'renewed'
            latest_engagement.save()
    else:  # update_client (expansion/upsell)
        # For expansions, don't increment version, just create parallel engagement
        latest_engagement = ClientEngagement.objects.filter(
            client=client
        ).order_by('-version').first()
        version = (latest_engagement.version + 1) if latest_engagement else 1
        parent_engagement = None  # Expansions don't link to parent

    # 1. Create Contract (Engagement Letter)
    contract = Contract.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
        proposal=proposal,
        contract_number=f"ENG-{proposal.proposal_number}",
        title=proposal.title,
        description=proposal.description,
        status='active',
        total_value=proposal.total_value,
        currency=proposal.currency,
        payment_terms='net_30',
        start_date=proposal.estimated_start_date or timezone.now().date(),
        end_date=proposal.estimated_end_date or (timezone.now().date() + timezone.timedelta(days=365)),
        signed_date=timezone.now().date(),
        signed_by=proposal.created_by,
        notes=f"{proposal.get_proposal_type_display()} from Proposal #{proposal.proposal_number}"
    )

    # 2. Create ClientEngagement record
    ClientEngagement.objects.create(
        firm=proposal.firm,  # TIER 2: Explicit tenant context
        client=client,
        contract=contract,
        status='current',
        version=version,
        parent_engagement=parent_engagement,
        start_date=contract.start_date,
        end_date=contract.end_date,
        contracted_value=contract.total_value,
        actual_revenue=0,
        notes=f"{proposal.get_proposal_type_display()} - Version {version}"
    )

    # 3. Create Project (if configured)
    if proposal.auto_create_project:
        Project.objects.create(
            firm=proposal.firm,  # TIER 2: Explicit tenant context
            client=client,
            contract=contract,
            project_manager=proposal.created_by,
            project_code=f"PROJ-{proposal.proposal_number}",
            name=proposal.title,
            description=proposal.description,
            status='planning',
            billing_type='time_and_materials',
            budget=proposal.total_value,
            start_date=contract.start_date,
            end_date=contract.end_date,
            notes=f"Auto-created from {proposal.get_proposal_type_display()} Proposal #{proposal.proposal_number}"
        )

    # 4. Update client metrics
    client.total_lifetime_value += proposal.total_value
    if proposal.auto_create_project:
        client.active_projects_count += 1
    client.save()

    # 5. Update Proposal
    proposal.accepted_at = timezone.now()
    proposal.converted_to_engagement = True
    proposal.save()

    engagement_type = "Renewal" if proposal.proposal_type == 'renewal_client' else "Expansion"
    print(f"✅ {engagement_type} for {client.company_name} - v{version} (Proposal {proposal.proposal_number})")
