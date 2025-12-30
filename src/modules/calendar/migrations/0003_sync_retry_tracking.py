# Generated migration for DOC-16.2: SyncAttemptLog retry tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0002_calendar_sync'),
    ]

    operations = [
        migrations.AddField(
            model_name='syncattemptlog',
            name='retry_count',
            field=models.IntegerField(
                default=0,
                help_text='Number of times this operation has been retried',
            ),
        ),
        migrations.AddField(
            model_name='syncattemptlog',
            name='next_retry_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Scheduled time for next retry (if applicable)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='syncattemptlog',
            name='max_retries_reached',
            field=models.BooleanField(
                default=False,
                help_text='Whether max retry attempts have been exhausted',
            ),
        ),
        migrations.AddIndex(
            model_name='syncattemptlog',
            index=models.Index(fields=['next_retry_at'], name='calendar_sy_next_re_idx'),
        ),
        migrations.AddIndex(
            model_name='syncattemptlog',
            index=models.Index(fields=['max_retries_reached'], name='calendar_sy_max_ret_idx'),
        ),
    ]
