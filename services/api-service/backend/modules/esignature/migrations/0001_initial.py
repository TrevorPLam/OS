"""Initial migration for esignature module."""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Create DocuSign integration models."""

    initial = True

    dependencies = [
        ("firm", "0001_initial"),
        ("clients", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocuSignConnection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "access_token",
                    models.TextField(help_text="Encrypted OAuth access token"),
                ),
                (
                    "refresh_token",
                    models.TextField(help_text="Encrypted OAuth refresh token"),
                ),
                (
                    "token_expires_at",
                    models.DateTimeField(help_text="When the access token expires"),
                ),
                (
                    "account_id",
                    models.CharField(
                        help_text="DocuSign account ID", max_length=255
                    ),
                ),
                (
                    "account_name",
                    models.CharField(
                        help_text="DocuSign account name", max_length=255
                    ),
                ),
                (
                    "base_uri",
                    models.URLField(
                        help_text="DocuSign API base URL for this account"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, help_text="Whether this connection is active"
                    ),
                ),
                (
                    "connected_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "last_sync_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Last successful API interaction",
                        null=True,
                    ),
                ),
                (
                    "last_error",
                    models.TextField(
                        blank=True, help_text="Last error message, if any"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "connected_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="docusign_connections_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.OneToOneField(
                        help_text="Firm that owns this DocuSign connection",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="docusign_connection",
                        to="firm.firm",
                    ),
                ),
            ],
            options={
                "verbose_name": "DocuSign Connection",
                "verbose_name_plural": "DocuSign Connections",
                "db_table": "esignature_docusign_connections",
            },
        ),
        migrations.CreateModel(
            name="Envelope",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "envelope_id",
                    models.CharField(
                        help_text="DocuSign envelope ID",
                        max_length=255,
                        unique=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("sent", "Sent"),
                            ("delivered", "Delivered"),
                            ("signed", "Signed"),
                            ("completed", "Completed"),
                            ("declined", "Declined"),
                            ("voided", "Voided"),
                            ("error", "Error"),
                        ],
                        default="created",
                        max_length=50,
                    ),
                ),
                (
                    "subject",
                    models.CharField(
                        help_text="Envelope email subject", max_length=255
                    ),
                ),
                (
                    "message",
                    models.TextField(
                        blank=True, help_text="Envelope email message"
                    ),
                ),
                (
                    "recipients",
                    models.JSONField(
                        default=list, help_text="List of recipients"
                    ),
                ),
                (
                    "sent_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When envelope was sent",
                        null=True,
                    ),
                ),
                (
                    "delivered_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When envelope was delivered",
                        null=True,
                    ),
                ),
                (
                    "signed_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When envelope was signed",
                        null=True,
                    ),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When envelope was completed",
                        null=True,
                    ),
                ),
                (
                    "voided_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When envelope was voided",
                        null=True,
                    ),
                ),
                (
                    "voided_reason",
                    models.TextField(blank=True, help_text="Reason for voiding"),
                ),
                (
                    "error_message",
                    models.TextField(
                        blank=True, help_text="Error message if status is error"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "connection",
                    models.ForeignKey(
                        help_text="DocuSign connection used for this envelope",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="envelopes",
                        to="esignature.docusignconnection",
                    ),
                ),
                (
                    "contract",
                    models.ForeignKey(
                        blank=True,
                        help_text="Contract this envelope is for",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="docusign_envelopes",
                        to="clients.contract",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="docusign_envelopes_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        help_text="Firm that owns this envelope",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="docusign_envelopes",
                        to="firm.firm",
                    ),
                ),
                (
                    "proposal",
                    models.ForeignKey(
                        blank=True,
                        help_text="Proposal this envelope is for",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="docusign_envelopes",
                        to="clients.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Envelope",
                "verbose_name_plural": "Envelopes",
                "db_table": "esignature_envelopes",
            },
        ),
        migrations.CreateModel(
            name="WebhookEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "envelope_id",
                    models.CharField(
                        help_text="DocuSign envelope ID from webhook", max_length=255
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        help_text="Type of event (e.g., envelope-completed)",
                        max_length=100,
                    ),
                ),
                (
                    "event_status",
                    models.CharField(
                        help_text="Status from event (e.g., completed)", max_length=50
                    ),
                ),
                (
                    "payload",
                    models.JSONField(help_text="Raw webhook payload"),
                ),
                (
                    "headers",
                    models.JSONField(
                        default=dict, help_text="Webhook request headers"
                    ),
                ),
                (
                    "processed",
                    models.BooleanField(
                        default=False, help_text="Whether this event has been processed"
                    ),
                ),
                (
                    "processed_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "error_message",
                    models.TextField(
                        blank=True, help_text="Error message if processing failed"
                    ),
                ),
                (
                    "received_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "envelope",
                    models.ForeignKey(
                        blank=True,
                        help_text="Envelope this event is for (null if envelope not found)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="webhook_events",
                        to="esignature.envelope",
                    ),
                ),
            ],
            options={
                "verbose_name": "Webhook Event",
                "verbose_name_plural": "Webhook Events",
                "db_table": "esignature_webhook_events",
                "ordering": ["-received_at"],
            },
        ),
        migrations.AddIndex(
            model_name="docusignconnection",
            index=models.Index(
                fields=["firm", "is_active"], name="esignature_firm_id_5a0d70_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="envelope",
            index=models.Index(
                fields=["firm", "status"], name="esignature_firm_id_c5ab36_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="envelope",
            index=models.Index(
                fields=["envelope_id"], name="esignature_envelop_ef1c7b_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="envelope",
            index=models.Index(
                fields=["proposal"], name="esignature_proposa_3a2bd9_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="envelope",
            index=models.Index(
                fields=["contract"], name="esignature_contrac_8f9c4d_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="envelope",
            index=models.Index(
                fields=["created_at"], name="esignature_created_7e9b2a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="webhookevent",
            index=models.Index(
                fields=["envelope_id"], name="esignature_envelop_a4f8c2_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="webhookevent",
            index=models.Index(
                fields=["received_at"], name="esignature_receive_2b5e9f_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="webhookevent",
            index=models.Index(
                fields=["processed"], name="esignature_process_1d3c8a_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="envelope",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("proposal__isnull", False), ("contract__isnull", True)),
                    models.Q(("proposal__isnull", True), ("contract__isnull", False)),
                    _connector="OR",
                ),
                name="envelope_linked_to_one_entity",
            ),
        ),
    ]
