from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0002_rename_mkt_idx_marketing_cam_sta_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailDomainAuthentication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain", models.CharField(help_text="Sending domain (e.g., example.com)", max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("verified", "Verified"), ("failed", "Failed")],
                        default="pending",
                        help_text="Overall verification status",
                        max_length=20,
                    ),
                ),
                ("spf_record", models.CharField(blank=True, help_text="Expected SPF record", max_length=500)),
                ("dkim_record", models.CharField(blank=True, help_text="Expected DKIM record", max_length=500)),
                ("dmarc_record", models.CharField(blank=True, help_text="Expected DMARC record", max_length=500)),
                ("spf_verified", models.BooleanField(default=False)),
                ("dkim_verified", models.BooleanField(default=False)),
                ("dmarc_verified", models.BooleanField(default=False)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_email_domains",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        help_text="Firm that owns this sending domain",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_domains",
                        to="firm.firm",
                    ),
                ),
            ],
            options={
                "db_table": "marketing_email_domains",
                "ordering": ["domain"],
                "unique_together": {("firm", "domain")},
            },
        ),
        migrations.AddIndex(
            model_name="emaildomainauthentication",
            index=models.Index(fields=["firm", "domain"], name="marketing_dom_fir_dom_idx"),
        ),
        migrations.AddIndex(
            model_name="emaildomainauthentication",
            index=models.Index(fields=["firm", "status"], name="marketing_dom_fir_sta_idx"),
        ),
    ]
