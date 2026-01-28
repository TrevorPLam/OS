# Generated manually for DEAL-6: Deal Alerts and Rotting Detection

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crm', '0008_add_assignment_automation_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='DealAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(choices=[('stale', 'Stale Deal'), ('close_date', 'Close Date Approaching'), ('value_change', 'Value Changed'), ('owner_change', 'Owner Changed'), ('stage_change', 'Stage Changed'), ('custom', 'Custom Alert')], help_text='Type of alert', max_length=50)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', help_text='Alert priority', max_length=20)),
                ('title', models.CharField(help_text='Alert title', max_length=255)),
                ('message', models.TextField(help_text='Alert message')),
                ('is_sent', models.BooleanField(default=False, help_text='Whether notification has been sent')),
                ('sent_at', models.DateTimeField(blank=True, help_text='When notification was sent', null=True)),
                ('is_acknowledged', models.BooleanField(default=False, help_text='Whether alert has been acknowledged')),
                ('acknowledged_at', models.DateTimeField(blank=True, help_text='When alert was acknowledged', null=True)),
                ('auto_dismiss_date', models.DateTimeField(blank=True, help_text='Date when alert should be auto-dismissed', null=True)),
                ('is_dismissed', models.BooleanField(default=False, help_text='Whether alert has been dismissed')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('acknowledged_by', models.ForeignKey(blank=True, help_text='User who acknowledged the alert', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acknowledged_alerts', to=settings.AUTH_USER_MODEL)),
                ('deal', models.ForeignKey(help_text='Deal this alert is for', on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='crm.deal')),
                ('recipients', models.ManyToManyField(help_text='Users to notify', related_name='deal_alerts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'crm_deal_alert',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['deal', 'is_sent'], name='crm_deal_alert_deal_sent_idx'),
                    models.Index(fields=['alert_type', 'is_sent'], name='crm_deal_alert_type_sent_idx'),
                    models.Index(fields=['is_acknowledged', 'is_dismissed'], name='crm_deal_alert_status_idx'),
                ],
            },
        ),
    ]
