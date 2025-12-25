from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_organization_client_organization'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='clientcomment',
            name='is_purged',
            field=models.BooleanField(default=False, help_text='Whether this comment content has been purged'),
        ),
        migrations.AddField(
            model_name='clientcomment',
            name='purged_at',
            field=models.DateTimeField(blank=True, help_text='When the comment was purged', null=True),
        ),
        migrations.AddField(
            model_name='clientcomment',
            name='purged_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who purged the comment',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='purged_client_comments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='clientcomment',
            name='purge_reason',
            field=models.TextField(blank=True, help_text='Reason for purge (required for legal/compliance)'),
        ),
        migrations.AddField(
            model_name='clientmessage',
            name='is_purged',
            field=models.BooleanField(default=False, help_text='Whether this message content has been purged'),
        ),
        migrations.AddField(
            model_name='clientmessage',
            name='purged_at',
            field=models.DateTimeField(blank=True, help_text='When the message was purged', null=True),
        ),
        migrations.AddField(
            model_name='clientmessage',
            name='purged_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who purged the message',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='purged_client_messages',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='clientmessage',
            name='purge_reason',
            field=models.TextField(blank=True, help_text='Reason for purge (required for legal/compliance)'),
        ),
    ]
