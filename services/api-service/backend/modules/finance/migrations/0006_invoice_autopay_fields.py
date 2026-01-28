from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('finance', '0005_add_performance_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='autopay_cadence',
            field=models.CharField(
                default='due_date',
                help_text='Cadence for recurring autopay (monthly/quarterly/due_date)',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='autopay_last_attempt_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When autopay was last attempted',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='autopay_next_charge_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the next autopay attempt is scheduled',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='autopay_opt_in',
            field=models.BooleanField(
                default=False,
                help_text='Whether this invoice should be automatically charged',
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='autopay_payment_method_id',
            field=models.CharField(
                blank=True,
                help_text='Payment method to use for autopay (defaults to client setting)',
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='autopay_status',
            field=models.CharField(
                default='idle',
                help_text='Autopay lifecycle status (idle, scheduled, processing, succeeded, failed, cancelled)',
                max_length=20,
            ),
        ),
    ]
