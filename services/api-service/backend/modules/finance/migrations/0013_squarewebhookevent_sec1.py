# Generated manually for SEC-1: Webhook idempotency tracking
# 
# Adds SquareWebhookEvent model for Square payment webhook idempotency

from django.db import migrations, models
import django.db.models.deletion
from modules.firm.utils import FirmScopedManager


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0012_revenue_reporting_materialized_view'),
        ('firm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SquareWebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('square_event_id', models.CharField(help_text='Square webhook event ID (unique identifier from Square)', max_length=255)),
                ('event_type', models.CharField(help_text='Square event type (e.g., payment.created, invoice.published)', max_length=100)),
                ('processed_at', models.DateTimeField(auto_now_add=True, help_text='When this event was processed')),
                ('processed_successfully', models.BooleanField(default=True, help_text='Whether event was processed successfully')),
                ('error_message', models.TextField(blank=True, help_text='Error message if processing failed')),
                ('event_data', models.JSONField(default=dict, help_text='Raw Square event data (for audit/debugging)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm', models.ForeignKey(help_text='Firm this webhook event belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='square_webhook_events', to='firm.firm')),
                ('invoice', models.ForeignKey(blank=True, help_text='Invoice related to this event (if applicable)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='square_webhook_events', to='finance.invoice')),
                ('payment', models.ForeignKey(blank=True, help_text='Payment related to this event (if applicable)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='square_webhook_events', to='finance.payment')),
            ],
            options={
                'verbose_name': 'Square Webhook Event',
                'verbose_name_plural': 'Square Webhook Events',
                'db_table': 'finance_square_webhook_events',
                'ordering': ['-processed_at', '-created_at'],
            },
            managers=[
                ('objects', django.db.models.Manager()),
                ('firm_scoped', FirmScopedManager()),
            ],
        ),
        migrations.AddIndex(
            model_name='squarewebhookevent',
            index=models.Index(fields=['firm', 'event_type'], name='finance_sq_evt_idx'),
        ),
        migrations.AddIndex(
            model_name='squarewebhookevent',
            index=models.Index(fields=['firm', 'processed_at'], name='finance_sq_pro_idx'),
        ),
        migrations.AddIndex(
            model_name='squarewebhookevent',
            index=models.Index(fields=['square_event_id'], name='finance_sq_evt_id_idx'),
        ),
        migrations.AddConstraint(
            model_name='squarewebhookevent',
            constraint=models.UniqueConstraint(fields=['square_event_id'], name='finance_square_event_unique'),
        ),
    ]
