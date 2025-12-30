# Generated manually for DOC-10.2: Backfill support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recurrence', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurrencegeneration',
            name='backfilled',
            field=models.BooleanField(
                default=False,
                help_text='Whether this generation was created via backfill operation',
            ),
        ),
        migrations.AddField(
            model_name='recurrencegeneration',
            name='backfill_reason',
            field=models.TextField(
                blank=True,
                help_text='Reason for backfill (if backfilled=True)',
            ),
        ),
        migrations.AddIndex(
            model_name='recurrencegeneration',
            index=models.Index(
                fields=['backfilled', '-created_at'],
                name='recurrence_backfilled_idx',
            ),
        ),
    ]
