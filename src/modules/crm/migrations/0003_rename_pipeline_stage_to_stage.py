# Generated manually for ASSESS-C3.1: Rename pipeline_stage to stage

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_add_performance_indexes'),
    ]

    operations = [
        # Remove old index on pipeline_stage
        migrations.RemoveIndex(
            model_name='prospect',
            name='crm_prospect_stage_idx',
        ),
        # Rename the field
        migrations.RenameField(
            model_name='prospect',
            old_name='pipeline_stage',
            new_name='stage',
        ),
        # Add new index on stage
        migrations.AddIndex(
            model_name='prospect',
            index=migrations.Index(
                fields=['firm', 'stage', '-created_at'],
                name='crm_prospect_stage_idx'
            ),
        ),
    ]
