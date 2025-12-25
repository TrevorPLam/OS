# Generated manually for TIER 5.2 performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_client_autopay_activated_at_and_more'),
    ]

    operations = [
        # Client performance indexes
        migrations.AddIndex(
            model_name='client',
            index=models.Index(
                fields=['firm', 'organization', 'status'],
                name='clients_client_org_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(
                fields=['firm', 'autopay_enabled', 'status'],
                name='clients_client_autopay_idx'
            ),
        ),

        # ClientEngagement performance indexes
        migrations.AddIndex(
            model_name='clientengagement',
            index=models.Index(
                fields=['client', 'status', '-start_date'],
                name='clients_eng_client_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='clientengagement',
            index=models.Index(
                fields=['firm', 'pricing_mode', '-start_date'],
                name='clients_eng_pricing_idx'
            ),
        ),

        # Organization performance indexes
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(
                fields=['firm', 'enable_cross_client_visibility'],
                name='clients_org_visibility_idx'
            ),
        ),
    ]
