# Generated migration for calendar sync models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("calendar", "0001_initial"),
        ("firm", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add calendar_connection field to Appointment
        migrations.AddField(
            model_name="appointment",
            name="calendar_connection",
            field=models.ForeignKey(
                blank=True,
                help_text="Calendar connection for external sync (if applicable)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="synced_appointments",
                to="calendar.calendarconnection",
            ),
        ),
        # Create CalendarConnection model
        migrations.CreateModel(
            name="CalendarConnection",
            fields=[
                ("connection_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("provider", models.CharField(choices=[("google", "Google Calendar"), ("microsoft", "Microsoft Outlook")], help_text="Calendar provider", max_length=20)),
                ("credentials_encrypted", models.TextField(blank=True, help_text="Encrypted OAuth credentials")),
                ("scopes_granted", models.TextField(blank=True, help_text="Scopes granted by the provider")),
                ("last_sync_cursor", models.TextField(blank=True, help_text="Last sync cursor/token from provider")),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("revoked", "Revoked")], default="active", help_text="Connection status", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("firm", models.ForeignKey(help_text="Firm this connection belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="calendar_connections", to="firm.firm")),
                ("owner_staff_user", models.ForeignKey(help_text="Staff user who owns this connection", on_delete=django.db.models.deletion.CASCADE, related_name="calendar_connections", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "calendar_connections",
                "ordering": ["-created_at"],
            },
        ),
        # Create SyncAttemptLog model
        migrations.CreateModel(
            name="SyncAttemptLog",
            fields=[
                ("attempt_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("direction", models.CharField(choices=[("pull", "Pull (External → Internal)"), ("push", "Push (Internal → External)")], help_text="Sync direction", max_length=10)),
                ("operation", models.CharField(choices=[("list_changes", "List Changes"), ("upsert", "Upsert"), ("delete", "Delete"), ("resync", "Manual Resync")], help_text="Sync operation", max_length=20)),
                ("status", models.CharField(choices=[("success", "Success"), ("fail", "Fail")], help_text="Attempt status", max_length=10)),
                ("error_class", models.CharField(blank=True, choices=[("transient", "Transient (Retry)"), ("non_retryable", "Non-Retryable"), ("rate_limited", "Rate Limited")], help_text="Error classification (if failed)", max_length=20)),
                ("error_summary", models.TextField(blank=True, help_text="Redacted error summary (no PII, no content)")),
                ("correlation_id", models.UUIDField(blank=True, help_text="Correlation ID for tracing", null=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("duration_ms", models.IntegerField(blank=True, help_text="Operation duration in milliseconds", null=True)),
                ("appointment", models.ForeignKey(blank=True, help_text="Appointment being synced (nullable for list operations)", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="sync_attempts", to="calendar.appointment")),
                ("connection", models.ForeignKey(help_text="Calendar connection for this attempt", on_delete=django.db.models.deletion.CASCADE, related_name="sync_attempts", to="calendar.calendarconnection")),
                ("firm", models.ForeignKey(help_text="Firm for this sync attempt", on_delete=django.db.models.deletion.CASCADE, related_name="sync_attempts", to="firm.firm")),
            ],
            options={
                "db_table": "calendar_sync_attempts",
                "ordering": ["-started_at"],
            },
        ),
        # Update Appointment index for connection + external_event_id
        migrations.AlterIndexTogether(
            name="appointment",
            index_together=set(),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["calendar_connection", "external_event_id"], name="calendar_ap_calenda_3f8a2d_idx"),
        ),
        # Add unique constraint for (connection, external_event_id)
        migrations.AddConstraint(
            model_name="appointment",
            constraint=models.UniqueConstraint(
                condition=models.Q(("calendar_connection__isnull", False), ("external_event_id__gt", "")),
                fields=("calendar_connection", "external_event_id"),
                name="unique_external_event_per_connection",
            ),
        ),
        # Add indexes for CalendarConnection
        migrations.AddIndex(
            model_name="calendarconnection",
            index=models.Index(fields=["firm", "owner_staff_user", "status"], name="calendar_ca_firm_id_6d2e9a_idx"),
        ),
        migrations.AddIndex(
            model_name="calendarconnection",
            index=models.Index(fields=["provider", "status"], name="calendar_ca_provide_8b3f1c_idx"),
        ),
        # Add indexes for SyncAttemptLog
        migrations.AddIndex(
            model_name="syncattemptlog",
            index=models.Index(fields=["firm", "connection", "started_at"], name="calendar_sy_firm_id_4a7e2b_idx"),
        ),
        migrations.AddIndex(
            model_name="syncattemptlog",
            index=models.Index(fields=["status", "error_class"], name="calendar_sy_status_9c2d5e_idx"),
        ),
        migrations.AddIndex(
            model_name="syncattemptlog",
            index=models.Index(fields=["correlation_id"], name="calendar_sy_correla_7f3a8d_idx"),
        ),
    ]
