"""
Client Signals - Automated workflows for client management.

Key workflow: When a Proposal is accepted in CRM, automatically:
1. Create a new Client record
2. Create a Contract
3. Optionally create initial Project
4. Setup document folders
5. Enable portal access (if configured)
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from modules.crm.models import Proposal, Contract
from modules.clients.models import Client, ClientEngagement
from modules.projects.models import Project
from modules.documents.models import Folder


@receiver(post_save, sender=Proposal)
def convert_prospect_to_client(sender, instance, created, **kwargs):
    """
    Automatically convert Prospect to Client when Proposal is accepted.

    This signal is the bridge between pre-sale (CRM) and post-sale (Clients).
    """
    # Only process if status changed to 'accepted' and not already converted
    if instance.status == 'accepted' and not instance.converted_to_client:
        # 1. Create Client from Prospect
        client = Client.objects.create(
            source_prospect=instance.prospect,
            source_proposal=instance,
            company_name=instance.prospect.company_name,
            industry=instance.prospect.industry,
            primary_contact_name=instance.prospect.primary_contact_name,
            primary_contact_email=instance.prospect.primary_contact_email,
            primary_contact_phone=instance.prospect.primary_contact_phone,
            street_address=instance.prospect.street_address,
            city=instance.prospect.city,
            state=instance.prospect.state,
            postal_code=instance.prospect.postal_code,
            country=instance.prospect.country,
            website=instance.prospect.website,
            employee_count=instance.prospect.employee_count,
            account_manager=instance.created_by,  # Assign proposal creator as account manager
            client_since=timezone.now().date(),
            status='active',
            portal_enabled=instance.enable_portal_on_acceptance,
            notes=f"Converted from Prospect #{instance.prospect.id} via Proposal #{instance.proposal_number}"
        )

        # Add proposal creator to assigned team
        client.assigned_team.add(instance.created_by)

        # 2. Create Contract
        contract = Contract.objects.create(
            client=client,
            proposal=instance,
            contract_number=f"CNT-{instance.proposal_number}",
            title=instance.title,
            description=instance.description,
            status='active',
            total_value=instance.total_value,
            currency=instance.currency,
            payment_terms='net_30',  # Default, can be customized
            start_date=instance.estimated_start_date or timezone.now().date(),
            end_date=instance.estimated_end_date or (timezone.now().date() + timezone.timedelta(days=90)),
            signed_date=timezone.now().date(),
            signed_by=instance.created_by,
            notes=f"Auto-generated from Proposal #{instance.proposal_number}"
        )

        # 3. Create ClientEngagement record for tracking
        ClientEngagement.objects.create(
            client=client,
            contract=contract,
            status='current',
            version=1,
            start_date=contract.start_date,
            end_date=contract.end_date,
            contracted_value=contract.total_value,
            actual_revenue=0,
            notes="Initial engagement"
        )

        # 4. Create initial Project (if configured)
        if instance.auto_create_project:
            Project.objects.create(
                client=client,
                contract=contract,
                project_manager=instance.created_by,
                project_code=f"PROJ-{instance.proposal_number}",
                name=f"{instance.title} - Implementation",
                description=instance.description,
                status='planning',
                billing_type='time_and_materials',  # Default, can be customized
                budget=instance.total_value,
                start_date=contract.start_date,
                end_date=contract.end_date,
                notes=f"Auto-created from Proposal #{instance.proposal_number}"
            )

        # 5. Setup Document Folders
        # Create root folder for client
        root_folder = Folder.objects.create(
            client=client,
            parent=None,
            name="Root",
            description="Client root folder",
            visibility='internal',
            created_by=instance.created_by
        )

        # Create subfolder for client-readable documents
        Folder.objects.create(
            client=client,
            parent=root_folder,
            name="Shared Documents",
            description="Documents shared with client portal",
            visibility='client',
            created_by=instance.created_by
        )

        # Create subfolder for client uploads
        Folder.objects.create(
            client=client,
            parent=root_folder,
            name="Client Uploads",
            description="Documents uploaded by client",
            visibility='client',
            created_by=instance.created_by
        )

        # Create internal folder
        Folder.objects.create(
            client=client,
            parent=root_folder,
            name="Internal Only",
            description="Internal team documents",
            visibility='internal',
            created_by=instance.created_by
        )

        # 6. Mark Prospect as won
        instance.prospect.pipeline_stage = 'won'
        instance.prospect.won_date = timezone.now().date()
        instance.prospect.save()

        # 7. Update Proposal timestamps and conversion flag
        instance.accepted_at = timezone.now()
        instance.converted_to_client = True
        instance.save()

        # TODO: Send welcome email to client contact
        # TODO: Send portal invitation if portal_enabled
        # TODO: Create notification for account manager

        print(f"✅ Successfully converted Proposal {instance.proposal_number} to Client: {client.company_name}")
