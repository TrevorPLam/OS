# Generated migration for DOC-15.2: IngestionAttempt retry-safety

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_ingestion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingestionattempt',
            name='error_class',
            field=models.CharField(
                blank=True,
                choices=[
                    ('transient', 'Transient'),
                    ('retryable', 'Retryable'),
                    ('non_retryable', 'Non-Retryable'),
                    ('rate_limited', 'Rate Limited'),
                ],
                help_text='Error classification for retry logic (DOC-15.2)',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='ingestionattempt',
            name='retry_count',
            field=models.IntegerField(
                default=0,
                help_text='Number of times this operation has been retried',
            ),
        ),
        migrations.AddField(
            model_name='ingestionattempt',
            name='next_retry_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Scheduled time for next retry (if applicable)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='ingestionattempt',
            name='max_retries_reached',
            field=models.BooleanField(
                default=False,
                help_text='Whether max retry attempts have been exhausted',
            ),
        ),
        migrations.AddIndex(
            model_name='ingestionattempt',
            index=models.Index(fields=['status', 'error_class'], name='email_inges_status_idx'),
        ),
        migrations.AddIndex(
            model_name='ingestionattempt',
            index=models.Index(fields=['next_retry_at'], name='email_inges_next_re_idx'),
        ),
        migrations.AddIndex(
            model_name='ingestionattempt',
            index=models.Index(fields=['max_retries_reached'], name='email_inges_max_ret_idx'),
        ),
    ]
