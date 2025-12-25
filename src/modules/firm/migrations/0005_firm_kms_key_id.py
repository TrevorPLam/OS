from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0004_auditevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='firm',
            name='kms_key_id',
            field=models.CharField(
                blank=True,
                help_text='Firm-scoped KMS key or alias for content encryption',
                max_length=255,
            ),
        ),
    ]
