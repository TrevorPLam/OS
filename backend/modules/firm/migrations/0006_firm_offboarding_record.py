from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0005_firm_kms_key_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='FirmOffboardingRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('exporting', 'Exporting'),
                            ('exported', 'Exported'),
                            ('purge_pending', 'Purge Pending'),
                            ('purged', 'Purged'),
                            ('failed', 'Failed'),
                        ],
                        default='exporting',
                        max_length=20,
                    ),
                ),
                ('retention_days', models.PositiveIntegerField(default=30)),
                ('purge_grace_days', models.PositiveIntegerField(default=7)),
                ('export_started_at', models.DateTimeField(auto_now_add=True)),
                ('export_completed_at', models.DateTimeField(blank=True, null=True)),
                ('retention_expires_at', models.DateTimeField(blank=True, null=True)),
                ('purge_scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('purge_completed_at', models.DateTimeField(blank=True, null=True)),
                ('export_manifest', models.JSONField(blank=True, default=dict)),
                ('integrity_report', models.JSONField(blank=True, default=dict)),
                ('export_checksum', models.CharField(blank=True, max_length=64)),
                (
                    'firm',
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='offboarding_records', to='firm.firm'),
                ),
                (
                    'requested_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name='firm_offboarding_requests',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'firm_offboarding_record',
                'ordering': ['-export_started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='firmoffboardingrecord',
            index=models.Index(fields=['firm', '-export_started_at'], name='firm_offbo_firm_id_31c9ee_idx'),
        ),
        migrations.AddIndex(
            model_name='firmoffboardingrecord',
            index=models.Index(fields=['status', '-export_started_at'], name='firm_offbo_status_3a9f79_idx'),
        ),
    ]
