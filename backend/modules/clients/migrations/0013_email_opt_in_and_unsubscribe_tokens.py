import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0012_consent_record_consent_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="portalbranding",
            name="email_physical_address",
            field=models.TextField(blank=True, help_text="Physical mailing address for compliance footers"),
        ),
        migrations.CreateModel(
            name="EmailOptInRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(help_text="When the confirmation link expires")),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("source", models.CharField(blank=True, help_text="Source of opt-in (e.g., signup_form)", max_length=100)),
                ("source_url", models.URLField(blank=True, help_text="URL where opt-in was requested")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("consent_text", models.TextField(blank=True, help_text="Consent text shown to the contact")),
                ("consent_version", models.CharField(blank=True, max_length=50)),
                (
                    "contact",
                    models.ForeignKey(
                        help_text="Contact requesting opt-in confirmation",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_opt_in_requests",
                        to="clients.contact",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who initiated the opt-in request",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="email_opt_in_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "clients_email_opt_in_requests",
                "ordering": ["-requested_at"],
            },
        ),
        migrations.CreateModel(
            name="EmailUnsubscribeToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("unsubscribed_at", models.DateTimeField(blank=True, null=True)),
                ("source", models.CharField(blank=True, help_text="Source of unsubscribe link", max_length=100)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                (
                    "contact",
                    models.ForeignKey(
                        help_text="Contact for the unsubscribe token",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unsubscribe_tokens",
                        to="clients.contact",
                    ),
                ),
            ],
            options={
                "db_table": "clients_email_unsubscribe_tokens",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="emailoptinrequest",
            index=models.Index(fields=["contact", "-requested_at"], name="clients_optin_contact_idx"),
        ),
        migrations.AddIndex(
            model_name="emailoptinrequest",
            index=models.Index(fields=["token"], name="clients_optin_token_idx"),
        ),
        migrations.AddIndex(
            model_name="emailoptinrequest",
            index=models.Index(fields=["expires_at"], name="clients_optin_exp_idx"),
        ),
        migrations.AddIndex(
            model_name="emailunsubscribetoken",
            index=models.Index(fields=["contact", "-created_at"], name="clients_unsub_contact_idx"),
        ),
        migrations.AddIndex(
            model_name="emailunsubscribetoken",
            index=models.Index(fields=["token"], name="clients_unsub_token_idx"),
        ),
    ]
