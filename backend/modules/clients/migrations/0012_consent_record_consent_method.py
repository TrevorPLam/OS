from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0011_add_consent_record_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="consentrecord",
            name="consent_method",
            field=models.CharField(
                blank=True,
                choices=[("express", "Express Consent"), ("implied", "Implied Consent")],
                help_text="Whether consent was express or implied",
                max_length=20,
                null=True,
            ),
        ),
    ]
