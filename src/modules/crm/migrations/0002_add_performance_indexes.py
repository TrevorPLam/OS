# Generated manually for TIER 5.2 performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        # Lead performance indexes
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(
                fields=['firm', 'status', '-created_at'],
                name='crm_lead_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(
                fields=['firm', 'assigned_to', 'status'],
                name='crm_lead_assigned_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(
                fields=['firm', 'source', '-created_at'],
                name='crm_lead_source_idx'
            ),
        ),

        # Prospect performance indexes
        migrations.AddIndex(
            model_name='prospect',
            index=models.Index(
                fields=['firm', 'pipeline_stage', '-created_at'],
                name='crm_prospect_stage_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='prospect',
            index=models.Index(
                fields=['firm', '-last_activity_date'],
                name='crm_prospect_contact_idx'
            ),
        ),

        # Proposal performance indexes
        migrations.AddIndex(
            model_name='proposal',
            index=models.Index(
                fields=['firm', 'status', '-sent_at'],
                name='crm_proposal_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='proposal',
            index=models.Index(
                fields=['firm', 'prospect', '-created_at'],
                name='crm_proposal_prospect_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='proposal',
            index=models.Index(
                fields=['-valid_until'],
                name='crm_proposal_expires_idx'
            ),
        ),

        # Campaign performance indexes
        migrations.AddIndex(
            model_name='campaign',
            index=models.Index(
                fields=['firm', 'status', '-start_date'],
                name='crm_campaign_status_idx'
            ),
        ),

        # Contract performance indexes
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(
                fields=['firm', 'status', '-signed_date'],
                name='crm_contract_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(
                fields=['firm', '-end_date'],
                name='crm_contract_end_date_idx'
            ),
        ),
    ]
