from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("firm", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GoogleAnalyticsConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("measurement_id", models.CharField(max_length=50)),
                ("api_secret", models.CharField(max_length=120)),
                ("property_id", models.CharField(blank=True, max_length=50)),
                ("stream_id", models.CharField(blank=True, max_length=50)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("disabled", "Disabled"), ("error", "Error")],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("last_event_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "integrations_google_analytics",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SalesforceConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("client_id", models.CharField(max_length=255)),
                ("client_secret", models.TextField(blank=True)),
                ("access_token", models.TextField(blank=True)),
                ("refresh_token", models.TextField(blank=True)),
                ("instance_url", models.CharField(blank=True, max_length=255)),
                ("scopes", models.JSONField(blank=True, default=list)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("disconnected", "Disconnected"),
                            ("active", "Active"),
                            ("expired", "Expired"),
                            ("error", "Error"),
                        ],
                        default="disconnected",
                        max_length=20,
                    ),
                ),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="salesforce_connections",
                        to="firm.firm",
                    ),
                ),
            ],
            options={
                "db_table": "integrations_salesforce_connection",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SlackIntegration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bot_token", models.TextField(blank=True)),
                ("signing_secret", models.TextField(blank=True)),
                ("default_channel", models.CharField(blank=True, max_length=120)),
                ("webhook_url", models.URLField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("disabled", "Disabled"), ("error", "Error")],
                        default="disabled",
                        max_length=20,
                    ),
                ),
                ("last_health_check", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="slack_integrations",
                        to="firm.firm",
                    ),
                ),
            ],
            options={
                "db_table": "integrations_slack",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SlackMessageLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("channel", models.CharField(max_length=120)),
                ("status", models.CharField(choices=[("sent", "Sent"), ("error", "Error")], max_length=20)),
                ("message", models.CharField(max_length=500)),
                ("response_code", models.IntegerField(blank=True, null=True)),
                ("response_body", models.TextField(blank=True)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="slack_message_logs",
                        to="firm.firm",
                    ),
                ),
                (
                    "integration",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="message_logs",
                        to="integrations.slackintegration",
                    ),
                ),
            ],
            options={
                "db_table": "integrations_slack_message_log",
                "ordering": ["-occurred_at"],
            },
        ),
        migrations.CreateModel(
            name="SalesforceSyncLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("object_type", models.CharField(max_length=50)),
                ("direction", models.CharField(help_text="push|pull", max_length=20)),
                ("status", models.CharField(help_text="success|error", max_length=20)),
                ("message", models.CharField(blank=True, max_length=500)),
                ("payload_snippet", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "connection",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sync_logs",
                        to="integrations.salesforceconnection",
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="salesforce_sync_logs",
                        to="firm.firm",
                    ),
                ),
            ],
            options={
                "db_table": "integrations_salesforce_sync_log",
                "ordering": ["-occurred_at"],
            },
        ),
        migrations.AddIndex(
            model_name="salesforceconnection",
            index=models.Index(fields=["firm", "status"], name="salesforce_conn_status_idx"),
        ),
        migrations.AddIndex(
            model_name="salesforceconnection",
            index=models.Index(fields=["firm", "created_at"], name="salesforce_conn_created_idx"),
        ),
        migrations.AddIndex(
            model_name="salesforcesynclog",
            index=models.Index(fields=["firm", "object_type"], name="salesforce_sync_object_idx"),
        ),
        migrations.AddIndex(
            model_name="slackintegration",
            index=models.Index(fields=["firm", "status"], name="slack_integration_status_idx"),
        ),
        migrations.AddIndex(
            model_name="slackmessagelog",
            index=models.Index(fields=["firm", "channel"], name="slack_log_channel_idx"),
        ),
        migrations.AddIndex(
            model_name="googleanalyticsconfig",
            index=models.Index(fields=["firm", "status"], name="ga_config_status_idx"),
        ),
    ]
