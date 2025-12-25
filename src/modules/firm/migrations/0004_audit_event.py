from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0003_platform_user_profile'),
        ('clients', '0003_organization_client_organization'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(
                    choices=[
                        ('AUTH', 'Authentication & Authorization'),
                        ('PERMISSIONS', 'Permission Changes'),
                        ('BREAK_GLASS', 'Break-Glass Content Access'),
                        ('BILLING_METADATA', 'Billing Metadata Operations'),
                        ('PURGE', 'Data Purge/Deletion'),
                        ('CONFIG', 'Configuration Changes'),
                        ('DATA_ACCESS', 'Data Access Events'),
                        ('ROLE_CHANGE', 'Role & Membership Changes'),
                        ('EXPORT', 'Data Export Operations'),
                        ('SIGNING', 'Document Signing Events'),
                    ],
                    db_index=True,
                    help_text='Event category for filtering and retention policy',
                    max_length=50
                )),
                ('action', models.CharField(
                    db_index=True,
                    help_text="Action performed (e.g., 'user.login', 'break_glass.activate', 'document.purge')",
                    max_length=100
                )),
                ('severity', models.CharField(
                    choices=[
                        ('info', 'Informational'),
                        ('warning', 'Warning'),
                        ('critical', 'Critical'),
                    ],
                    default='info',
                    help_text='Event severity level',
                    max_length=20
                )),
                ('actor_ip', models.GenericIPAddressField(
                    blank=True,
                    help_text='IP address of actor (if available)',
                    null=True
                )),
                ('actor_user_agent', models.TextField(
                    blank=True,
                    help_text='User agent string (if available)'
                )),
                ('target_object_id', models.CharField(
                    blank=True,
                    help_text='ID of target object',
                    max_length=255
                )),
                ('target_description', models.CharField(
                    blank=True,
                    help_text='Human-readable description of target (survives target deletion)',
                    max_length=500
                )),
                ('reason', models.TextField(
                    blank=True,
                    help_text='Reason string for actions requiring justification (break-glass, purge, etc.)'
                )),
                ('metadata', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Structured metadata (MUST be content-free, operational data only)'
                )),
                ('timestamp', models.DateTimeField(
                    auto_now_add=True,
                    db_index=True,
                    help_text='When this event occurred (immutable)'
                )),
                ('retention_until', models.DateTimeField(
                    blank=True,
                    db_index=True,
                    help_text='When this event can be deleted per retention policy (null = keep forever)',
                    null=True
                )),
                ('actor', models.ForeignKey(
                    blank=True,
                    help_text='User who performed the action (null for system events)',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_events_as_actor',
                    to=settings.AUTH_USER_MODEL
                )),
                ('client', models.ForeignKey(
                    blank=True,
                    help_text='Client context (if action is client-scoped)',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_events',
                    to='clients.client'
                )),
                ('firm', models.ForeignKey(
                    help_text='Tenant context: which firm this event belongs to',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='audit_events',
                    to='firm.firm'
                )),
                ('target_content_type', models.ForeignKey(
                    blank=True,
                    help_text='Type of object this event targets',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='contenttypes.contenttype'
                )),
            ],
            options={
                'db_table': 'firm_audit_event',
                'ordering': ['-timestamp'],
                'permissions': [
                    ('view_audit_event', 'Can view audit events'),
                    ('export_audit_event', 'Can export audit events'),
                ],
            },
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['firm', 'category', '-timestamp'], name='firm_audit_firm_cat_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['firm', 'actor', '-timestamp'], name='firm_audit_firm_actor_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['category', '-timestamp'], name='firm_audit_cat_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['action', '-timestamp'], name='firm_audit_action_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['severity', '-timestamp'], name='firm_audit_severity_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['retention_until'], name='firm_audit_retention_idx'),
        ),
    ]
