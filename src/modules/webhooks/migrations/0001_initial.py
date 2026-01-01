# Generated manually for Task 3.7: General Webhook Platform

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modules.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('firm', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookEndpoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Descriptive name for this webhook endpoint', max_length=255)),
                ('url', models.URLField(help_text='URL to POST webhook events to', max_length=2048, validators=[modules.core.validators.validate_safe_url])),
                ('description', models.TextField(blank=True, help_text='Description of what this webhook is for')),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('disabled', 'Disabled')], default='active', help_text='Webhook status (active, paused, disabled)', max_length=20)),
                ('subscribed_events', models.JSONField(default=list, help_text="List of event types this endpoint subscribes to (e.g., ['client.created', 'project.updated'])")),
                ('secret', models.CharField(help_text='Secret key for HMAC signature verification (auto-generated)', max_length=255)),
                ('max_retries', models.IntegerField(default=3, help_text='Maximum number of retry attempts for failed deliveries')),
                ('retry_delay_seconds', models.IntegerField(default=60, help_text='Initial retry delay in seconds (exponential backoff applied)')),
                ('timeout_seconds', models.IntegerField(default=30, help_text='HTTP request timeout in seconds')),
                ('rate_limit_per_minute', models.IntegerField(blank=True, help_text='Maximum events per minute (null = no limit)', null=True)),
                ('total_deliveries', models.IntegerField(default=0, help_text='Total number of delivery attempts')),
                ('successful_deliveries', models.IntegerField(default=0, help_text='Number of successful deliveries (HTTP 2xx)')),
                ('failed_deliveries', models.IntegerField(default=0, help_text='Number of failed deliveries')),
                ('last_delivery_at', models.DateTimeField(blank=True, help_text='Timestamp of last delivery attempt', null=True)),
                ('last_success_at', models.DateTimeField(blank=True, help_text='Timestamp of last successful delivery', null=True)),
                ('last_failure_at', models.DateTimeField(blank=True, help_text='Timestamp of last failed delivery', null=True)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata for this webhook (custom fields)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, help_text='User who created this webhook', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_webhook_endpoints', to=settings.AUTH_USER_MODEL)),
                ('firm', models.ForeignKey(help_text='Firm (workspace) this webhook belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='webhook_endpoints', to='firm.firm')),
            ],
            options={
                'db_table': 'webhooks_endpoint',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WebhookDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(help_text="Event type (e.g., 'client.created', 'project.updated')", max_length=100)),
                ('event_id', models.CharField(help_text='Unique identifier for this event', max_length=255)),
                ('payload', models.JSONField(help_text='Event payload (data sent to webhook)')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sending', 'Sending'), ('success', 'Success'), ('failed', 'Failed'), ('retrying', 'Retrying')], default='pending', help_text='Current delivery status', max_length=20)),
                ('attempts', models.IntegerField(default=0, help_text='Number of delivery attempts made')),
                ('http_status_code', models.IntegerField(blank=True, help_text='HTTP response status code from webhook endpoint', null=True)),
                ('response_headers', models.JSONField(blank=True, default=dict, help_text='HTTP response headers from webhook endpoint')),
                ('response_body', models.TextField(blank=True, help_text='HTTP response body from webhook endpoint')),
                ('error_message', models.TextField(blank=True, help_text='Error message if delivery failed')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When this delivery was created')),
                ('first_attempt_at', models.DateTimeField(blank=True, help_text='Timestamp of first delivery attempt', null=True)),
                ('last_attempt_at', models.DateTimeField(blank=True, help_text='Timestamp of most recent delivery attempt', null=True)),
                ('next_retry_at', models.DateTimeField(blank=True, help_text='Timestamp of next retry attempt (if retrying)', null=True)),
                ('completed_at', models.DateTimeField(blank=True, help_text='Timestamp when delivery completed (success or final failure)', null=True)),
                ('signature', models.CharField(blank=True, help_text='HMAC signature sent in request headers', max_length=255)),
                ('webhook_endpoint', models.ForeignKey(help_text='Webhook endpoint this delivery is for', on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='webhooks.webhookendpoint')),
            ],
            options={
                'db_table': 'webhooks_delivery',
                'ordering': ['-created_at'],
                'verbose_name_plural': 'Webhook Deliveries',
            },
        ),
        migrations.AddIndex(
            model_name='webhookendpoint',
            index=models.Index(fields=['firm', 'status'], name='webhook_ep_firm_status_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookendpoint',
            index=models.Index(fields=['status'], name='webhook_ep_status_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookdelivery',
            index=models.Index(fields=['webhook_endpoint', 'status'], name='webhook_del_ep_status_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookdelivery',
            index=models.Index(fields=['event_type'], name='webhook_del_event_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookdelivery',
            index=models.Index(fields=['status', 'next_retry_at'], name='webhook_del_retry_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookdelivery',
            index=models.Index(fields=['created_at'], name='webhook_del_created_idx'),
        ),
    ]
