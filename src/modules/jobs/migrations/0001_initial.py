# Generated migration for DOC-20.1: JobQueue and JobDLQ models

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('firm', '0001_initial'),  # Adjust based on actual firm migration
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JobQueue',
            fields=[
                ('job_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('category', models.CharField(choices=[('ingestion', 'Ingestion'), ('sync', 'Sync'), ('recurrence', 'Recurrence'), ('orchestration', 'Orchestration'), ('documents', 'Documents'), ('notifications', 'Notifications'), ('export', 'Export'), ('maintenance', 'Maintenance')], help_text='Job category per docs/20 section 1', max_length=20)),
                ('job_type', models.CharField(help_text='Specific job type (e.g., email_ingestion_fetch, calendar_sync_pull)', max_length=100)),
                ('payload_version', models.CharField(default='1.0', help_text='Payload schema version for evolution', max_length=10)),
                ('payload', models.JSONField(help_text='Job payload: MUST include tenant_id, correlation_id, idempotency_key, object refs')),
                ('idempotency_key', models.CharField(help_text='Unique key for at-most-once processing per docs/20 section 3', max_length=255)),
                ('correlation_id', models.UUIDField(help_text='Correlation ID for tracing across systems per docs/20 section 2')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('dlq', 'Dead Letter Queue')], default='pending', help_text='Current job status', max_length=20)),
                ('priority', models.IntegerField(choices=[(0, 'Critical'), (1, 'High'), (2, 'Normal'), (3, 'Low')], default=2, help_text='Job priority (0=Critical, 3=Low)')),
                ('scheduled_at', models.DateTimeField(default=django.utils.timezone.now, help_text='When job should be processed')),
                ('claimed_at', models.DateTimeField(blank=True, help_text='When job was claimed by a worker (for concurrency control)', null=True)),
                ('claimed_by_worker', models.CharField(blank=True, help_text='Worker ID that claimed this job', max_length=255)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('attempt_count', models.IntegerField(default=0, help_text='Number of execution attempts')),
                ('max_attempts', models.IntegerField(default=5, help_text='Maximum retry attempts before DLQ')),
                ('next_retry_at', models.DateTimeField(blank=True, help_text='Scheduled time for next retry', null=True)),
                ('error_class', models.CharField(blank=True, help_text='Error classification (transient, retryable, non_retryable, rate_limited)', max_length=50)),
                ('last_error', models.TextField(blank=True, help_text='Last error message (redacted, no PII/content)')),
                ('result', models.JSONField(blank=True, help_text='Job result (if applicable, minimal)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm', models.ForeignKey(help_text='Firm this job belongs to (tenant isolation)', on_delete=django.db.models.deletion.CASCADE, related_name='job_queue', to='firm.firm')),
            ],
            options={
                'db_table': 'job_queue',
                'ordering': ['priority', 'scheduled_at'],
            },
        ),
        migrations.CreateModel(
            name='JobDLQ',
            fields=[
                ('dlq_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('category', models.CharField(max_length=20)),
                ('job_type', models.CharField(max_length=100)),
                ('payload_version', models.CharField(max_length=10)),
                ('payload', models.JSONField(help_text='Original payload preserved for reprocessing')),
                ('idempotency_key', models.CharField(max_length=255)),
                ('correlation_id', models.UUIDField()),
                ('error_class', models.CharField(help_text='Error classification from original failure', max_length=50)),
                ('error_message', models.TextField(help_text='Error message from original failure (redacted)')),
                ('attempt_count', models.IntegerField(help_text='Number of attempts before DLQ')),
                ('status', models.CharField(choices=[('pending_review', 'Pending Review'), ('reprocessing', 'Reprocessing'), ('resolved', 'Resolved'), ('discarded', 'Discarded')], default='pending_review', help_text='DLQ processing status', max_length=20)),
                ('reprocessed_at', models.DateTimeField(blank=True, help_text='When item was reprocessed', null=True)),
                ('reprocessing_notes', models.TextField(blank=True, help_text='Admin notes on reprocessing (why, what was fixed, etc.)')),
                ('original_created_at', models.DateTimeField(help_text='Original job creation time (preserved)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm', models.ForeignKey(help_text='Firm this DLQ entry belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='job_dlq', to='firm.firm')),
                ('new_job', models.ForeignKey(blank=True, help_text='New job created from reprocessing', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dlq_reprocessed_from', to='jobs.jobqueue')),
                ('original_job', models.ForeignKey(blank=True, help_text='Original job that failed (nullable if job is purged)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dlq_entries', to='jobs.jobqueue')),
                ('reprocessed_by', models.ForeignKey(blank=True, help_text='Admin who initiated reprocessing', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reprocessed_dlq_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'job_dlq',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='jobqueue',
            index=models.Index(fields=['firm', 'status', 'scheduled_at'], name='job_queue_firm_id_idx'),
        ),
        migrations.AddIndex(
            model_name='jobqueue',
            index=models.Index(fields=['status', 'priority', 'scheduled_at'], name='job_queue_status_idx'),
        ),
        migrations.AddIndex(
            model_name='jobqueue',
            index=models.Index(fields=['idempotency_key'], name='job_queue_idemp_idx'),
        ),
        migrations.AddIndex(
            model_name='jobqueue',
            index=models.Index(fields=['correlation_id'], name='job_queue_corr_idx'),
        ),
        migrations.AddIndex(
            model_name='jobqueue',
            index=models.Index(fields=['category', 'status'], name='job_queue_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='jobqueue',
            index=models.Index(fields=['claimed_at'], name='job_queue_claimed_idx'),
        ),
        migrations.AddConstraint(
            model_name='jobqueue',
            constraint=models.UniqueConstraint(fields=('firm', 'idempotency_key'), name='unique_job_idempotency_key'),
        ),
        migrations.AddIndex(
            model_name='jobdlq',
            index=models.Index(fields=['firm', 'status', 'created_at'], name='job_dlq_firm_idx'),
        ),
        migrations.AddIndex(
            model_name='jobdlq',
            index=models.Index(fields=['category', 'status'], name='job_dlq_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='jobdlq',
            index=models.Index(fields=['error_class'], name='job_dlq_error_idx'),
        ),
        migrations.AddIndex(
            model_name='jobdlq',
            index=models.Index(fields=['idempotency_key'], name='job_dlq_idemp_idx'),
        ),
        migrations.AddIndex(
            model_name='jobdlq',
            index=models.Index(fields=['correlation_id'], name='job_dlq_corr_idx'),
        ),
    ]
