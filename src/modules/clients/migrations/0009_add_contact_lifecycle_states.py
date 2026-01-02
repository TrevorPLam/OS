# Generated manually for contact lifecycle states

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0008_contact_engagementline_and_more'),
    ]

    operations = [
        # Add new status field
        migrations.AddField(
            model_name='contact',
            name='status',
            field=models.CharField(
                choices=[
                    ('active', 'Active'),
                    ('unsubscribed', 'Unsubscribed'),
                    ('bounced', 'Bounced'),
                    ('unconfirmed', 'Unconfirmed'),
                    ('inactive', 'Inactive'),
                ],
                default='active',
                help_text="Current lifecycle state of the contact",
                max_length=20,
            ),
        ),
        # Add status tracking fields
        migrations.AddField(
            model_name='contact',
            name='status_changed_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the status was last changed',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='contact',
            name='status_changed_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who last changed the status',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contact_status_changes',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='contact',
            name='status_reason',
            field=models.TextField(
                blank=True,
                help_text='Reason for status change (e.g., bounce reason, unsubscribe reason)',
            ),
        ),
        # Update is_active field help text
        migrations.AlterField(
            model_name='contact',
            name='is_active',
            field=models.BooleanField(
                default=True,
                help_text='Whether this contact is active (deprecated, use status)',
            ),
        ),
        # Add indexes for status field
        migrations.AddIndex(
            model_name='contact',
            index=models.Index(
                fields=['client', 'status'],
                name='clients_contact_cli_sta_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='contact',
            index=models.Index(
                fields=['status'],
                name='clients_contact_status_idx',
            ),
        ),
    ]
