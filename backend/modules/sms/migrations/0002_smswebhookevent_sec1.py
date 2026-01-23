# Generated manually for SEC-1: Webhook idempotency tracking
#
# Adds SMSWebhookEvent model for Twilio webhook idempotency

from django.db import migrations, models
import django.db.models.deletion
from modules.firm.utils import FirmScopedManager


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0001_initial'),
        ('firm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSWebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('twilio_message_sid', models.CharField(help_text='Twilio message SID (unique identifier from Twilio)', max_length=255)),
                ('event_type', models.CharField(help_text='Event type (status_callback, inbound_message)', max_length=100)),
                ('webhook_type', models.CharField(help_text='Webhook type: status or inbound', max_length=50)),
                ('message_status', models.CharField(blank=True, help_text='Message status from webhook (for status callbacks)', max_length=50)),
                ('processed_at', models.DateTimeField(auto_now_add=True, help_text='When this event was processed')),
                ('processed_successfully', models.BooleanField(default=True, help_text='Whether event was processed successfully')),
                ('error_message', models.TextField(blank=True, help_text='Error message if processing failed')),
                ('event_data', models.JSONField(default=dict, help_text='Raw Twilio webhook data (for audit/debugging)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm', models.ForeignKey(help_text='Firm this webhook event belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='sms_webhook_events', to='firm.firm')),
                ('sms_message', models.ForeignKey(blank=True, help_text='SMS message related to this event (if applicable)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='webhook_events', to='sms.smsmessage')),
                ('conversation', models.ForeignKey(blank=True, help_text='Conversation related to this event (if applicable)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='webhook_events', to='sms.smsconversation')),
            ],
            options={
                'verbose_name': 'SMS Webhook Event',
                'verbose_name_plural': 'SMS Webhook Events',
                'db_table': 'sms_webhook_events',
                'ordering': ['-processed_at', '-created_at'],
            },
            managers=[
                ('objects', django.db.models.Manager()),
                ('firm_scoped', FirmScopedManager()),
            ],
        ),
        migrations.AddIndex(
            model_name='smswebhookevent',
            index=models.Index(fields=['firm', 'event_type'], name='sms_wh_fir_evt_idx'),
        ),
        migrations.AddIndex(
            model_name='smswebhookevent',
            index=models.Index(fields=['firm', 'processed_at'], name='sms_wh_fir_pro_idx'),
        ),
        migrations.AddIndex(
            model_name='smswebhookevent',
            index=models.Index(fields=['twilio_message_sid'], name='sms_wh_msg_sid_idx'),
        ),
        migrations.AddConstraint(
            model_name='smswebhookevent',
            constraint=models.UniqueConstraint(fields=['twilio_message_sid', 'webhook_type'], name='sms_webhook_event_unique'),
        ),
    ]
