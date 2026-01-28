# Generated migration for email_ingestion module

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("firm", "0001_initial"),
        ("documents", "0001_initial"),
        ("crm", "0001_initial"),
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Human-readable connection name", max_length=255)),
                ("provider", models.CharField(choices=[("gmail", "Gmail"), ("outlook", "Outlook"), ("other", "Other")], max_length=20)),
                ("email_address", models.EmailField(help_text="Email address being monitored", max_length=254)),
                ("credentials_encrypted", models.TextField(blank=True, help_text="Encrypted OAuth credentials or API tokens")),
                ("is_active", models.BooleanField(default=True)),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_email_connections", to=settings.AUTH_USER_MODEL)),
                ("firm", models.ForeignKey(help_text="Firm this connection belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="email_connections", to="firm.firm")),
            ],
            options={
                "db_table": "email_ingestion_connections",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="EmailArtifact",
            fields=[
                ("email_artifact_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("provider", models.CharField(choices=[("gmail", "Gmail"), ("outlook", "Outlook"), ("other", "Other")], help_text="Email provider (gmail, outlook, other)", max_length=20)),
                ("external_message_id", models.CharField(help_text="Provider's unique message ID (required; unique per connection)", max_length=512)),
                ("thread_id", models.CharField(blank=True, help_text="Provider's thread/conversation ID (nullable)", max_length=512, null=True)),
                ("from_address", models.EmailField(help_text="Sender email address (governed: R-PII)", max_length=254)),
                ("to_addresses", models.TextField(help_text="Recipient email addresses, comma-separated (governed: R-PII)")),
                ("cc_addresses", models.TextField(blank=True, default="", help_text="CC email addresses, comma-separated (governed: R-PII)")),
                ("subject", models.TextField(help_text="Email subject line (governed)")),
                ("sent_at", models.DateTimeField(help_text="When the email was sent (per provider)")),
                ("received_at", models.DateTimeField(help_text="When the email was received (per provider)")),
                ("body_preview", models.TextField(blank=True, help_text="Bounded preview of email body (max 500 chars)", max_length=500)),
                ("status", models.CharField(choices=[("ingested", "Ingested"), ("mapped", "Mapped"), ("triage", "Needs Triage"), ("ignored", "Ignored")], default="ingested", help_text="Current processing status", max_length=20)),
                ("mapping_confidence", models.DecimalField(blank=True, decimal_places=2, help_text="Mapping confidence score (0.00 to 1.00)", max_digits=3, null=True)),
                ("mapping_reasons", models.TextField(blank=True, help_text="Human-readable reasons for mapping suggestion")),
                ("ignored_reason", models.TextField(blank=True, help_text="Reason for marking as ignored")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("confirmed_account", models.ForeignKey(blank=True, help_text="Confirmed Account mapping (after review)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="confirmed_emails", to="crm.account")),
                ("confirmed_engagement", models.ForeignKey(blank=True, help_text="Confirmed Engagement mapping (after review)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="confirmed_emails", to="crm.engagement")),
                ("confirmed_work_item", models.ForeignKey(blank=True, help_text="Confirmed WorkItem mapping (after review)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="confirmed_emails", to="projects.workitem")),
                ("connection", models.ForeignKey(help_text="Email connection that ingested this message", on_delete=django.db.models.deletion.CASCADE, related_name="artifacts", to="email_ingestion.emailconnection")),
                ("firm", models.ForeignKey(help_text="Firm this artifact belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="email_artifacts", to="firm.firm")),
                ("reviewed_by", models.ForeignKey(blank=True, help_text="Staff member who reviewed/confirmed mapping", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_emails", to=settings.AUTH_USER_MODEL)),
                ("storage_ref", models.ForeignKey(blank=True, help_text="Optional: full MIME stored as a governed document", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="email_artifacts", to="documents.document")),
                ("suggested_account", models.ForeignKey(blank=True, help_text="Suggested Account mapping", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="suggested_emails", to="crm.account")),
                ("suggested_engagement", models.ForeignKey(blank=True, help_text="Suggested Engagement mapping", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="suggested_emails", to="crm.engagement")),
                ("suggested_work_item", models.ForeignKey(blank=True, help_text="Suggested WorkItem mapping", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="suggested_emails", to="projects.workitem")),
            ],
            options={
                "db_table": "email_ingestion_artifacts",
                "ordering": ["-sent_at"],
            },
        ),
        migrations.CreateModel(
            name="IngestionAttempt",
            fields=[
                ("attempt_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("operation", models.CharField(choices=[("fetch", "Fetch"), ("parse", "Parse"), ("store", "Store"), ("map", "Map")], help_text="Operation being attempted", max_length=20)),
                ("status", models.CharField(choices=[("success", "Success"), ("fail", "Fail")], help_text="Attempt status", max_length=20)),
                ("error_summary", models.TextField(blank=True, help_text="Redacted error summary (no PII, no content)")),
                ("correlation_id", models.UUIDField(blank=True, help_text="Correlation ID for tracing across systems", null=True)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("duration_ms", models.IntegerField(blank=True, help_text="Operation duration in milliseconds", null=True)),
                ("connection", models.ForeignKey(help_text="Email connection for this attempt", on_delete=django.db.models.deletion.CASCADE, related_name="ingestion_attempts", to="email_ingestion.emailconnection")),
                ("email_artifact", models.ForeignKey(blank=True, help_text="Email artifact (nullable if failed before create)", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="ingestion_attempts", to="email_ingestion.emailartifact")),
                ("firm", models.ForeignKey(help_text="Firm this attempt belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="ingestion_attempts", to="firm.firm")),
            ],
            options={
                "db_table": "email_ingestion_attempts",
                "ordering": ["-occurred_at"],
            },
        ),
        migrations.CreateModel(
            name="EmailAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_filename", models.CharField(help_text="Original attachment filename", max_length=255)),
                ("content_type", models.CharField(help_text="MIME type from email", max_length=100)),
                ("size_bytes", models.BigIntegerField(help_text="Attachment size in bytes")),
                ("attachment_index", models.IntegerField(help_text="Index of this attachment in the email (0-indexed)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(help_text="Governed document storing this attachment", on_delete=django.db.models.deletion.CASCADE, related_name="email_attachments", to="documents.document")),
                ("email_artifact", models.ForeignKey(help_text="Email this attachment belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="email_ingestion.emailartifact")),
            ],
            options={
                "db_table": "email_ingestion_attachments",
                "ordering": ["email_artifact", "attachment_index"],
            },
        ),
        # Indexes
        migrations.AddIndex(
            model_name="emailconnection",
            index=models.Index(fields=["firm", "is_active"], name="email_inges_firm_id_c0d5e6_idx"),
        ),
        migrations.AddIndex(
            model_name="emailartifact",
            index=models.Index(fields=["firm", "status"], name="email_inges_firm_id_f3a8b2_idx"),
        ),
        migrations.AddIndex(
            model_name="emailartifact",
            index=models.Index(fields=["firm", "sent_at"], name="email_inges_firm_id_4e2c9a_idx"),
        ),
        migrations.AddIndex(
            model_name="emailartifact",
            index=models.Index(fields=["connection", "external_message_id"], name="email_inges_connect_7b3d1f_idx"),
        ),
        migrations.AddIndex(
            model_name="emailartifact",
            index=models.Index(fields=["suggested_account"], name="email_inges_suggest_5a2e8c_idx"),
        ),
        migrations.AddIndex(
            model_name="emailartifact",
            index=models.Index(fields=["confirmed_account"], name="email_inges_confirm_9f4b3e_idx"),
        ),
        migrations.AddIndex(
            model_name="ingestionattempt",
            index=models.Index(fields=["firm", "occurred_at"], name="email_inges_firm_id_6c8a4d_idx"),
        ),
        migrations.AddIndex(
            model_name="ingestionattempt",
            index=models.Index(fields=["connection", "status"], name="email_inges_connect_3e7f2b_idx"),
        ),
        migrations.AddIndex(
            model_name="ingestionattempt",
            index=models.Index(fields=["email_artifact"], name="email_inges_email_a_8d1c5e_idx"),
        ),
        migrations.AddIndex(
            model_name="ingestionattempt",
            index=models.Index(fields=["correlation_id"], name="email_inges_correla_2a9f6b_idx"),
        ),
        migrations.AddIndex(
            model_name="emailattachment",
            index=models.Index(fields=["email_artifact"], name="email_inges_email_a_4b3e8f_idx"),
        ),
        migrations.AddIndex(
            model_name="emailattachment",
            index=models.Index(fields=["document"], name="email_inges_documen_7e2a5c_idx"),
        ),
        # Unique constraints
        migrations.AlterUniqueTogether(
            name="emailartifact",
            unique_together={("connection", "external_message_id")},
        ),
        migrations.AlterUniqueTogether(
            name="emailattachment",
            unique_together={("email_artifact", "attachment_index")},
        ),
    ]
