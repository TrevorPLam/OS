import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("firm", "0013_remove_provisioninglog_firm_and_more"),
        ("tracking", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackingKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, help_text="Public identifier for instrumentation", unique=True)),
                ("label", models.CharField(blank=True, help_text="Human-friendly label for the key", max_length=255)),
                ("secret_hash", models.CharField(help_text="Hashed secret token for verification", max_length=128)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("rotated_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("client_config_version", models.PositiveIntegerField(default=1)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_tracking_keys", to=settings.AUTH_USER_MODEL)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tracking_keys", to="firm.firm")),
                ("rotated_from", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="rotated_children", to="tracking.trackingkey")),
            ],
            options={"db_table": "tracking_key", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TrackingKeyAudit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("created", "Created"), ("rotated", "Rotated"), ("downloaded", "Downloaded"), ("revoked", "Revoked"), ("abuse_blocked", "Abuse Blocked")], max_length=32)),
                ("detail", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tracking_key_audits", to=settings.AUTH_USER_MODEL)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tracking_key_audits", to="firm.firm")),
                ("tracking_key", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audits", to="tracking.trackingkey")),
            ],
            options={"db_table": "tracking_key_audit", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SiteMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("message_type", models.CharField(choices=[("modal", "Modal"), ("slide_in", "Slide In"), ("banner", "Banner")], max_length=20)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("archived", "Archived")], default="draft", max_length=20)),
                ("targeting_rules", models.JSONField(blank=True, default=dict, help_text="Segment and behavior targeting rules")),
                ("content", models.JSONField(blank=True, default=dict, help_text="Structured content for rendering variants")),
                ("personalization_tokens", models.JSONField(blank=True, default=list)),
                ("form_schema", models.JSONField(blank=True, default=dict, help_text="Optional embedded form definition")),
                ("frequency_cap", models.PositiveIntegerField(default=1, help_text="Max displays per visitor per day")),
                ("active_from", models.DateTimeField(blank=True, null=True)),
                ("active_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="site_messages", to=settings.AUTH_USER_MODEL)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="site_messages", to="firm.firm")),
            ],
            options={"db_table": "tracking_site_message", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TrackingAbuseEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_ip", models.CharField(blank=True, max_length=64)),
                ("user_agent_hash", models.CharField(blank=True, max_length=64)),
                ("reason", models.CharField(choices=[("rate_limited", "Rate limited"), ("invalid_key", "Invalid key")], max_length=32)),
                ("request_count", models.PositiveIntegerField(default=0)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tracking_abuse_events", to="firm.firm")),
                ("tracking_key", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="abuse_events", to="tracking.trackingkey")),
            ],
            options={"db_table": "tracking_abuse_event", "ordering": ["-occurred_at"]},
        ),
        migrations.AddField(
            model_name="trackingevent",
            name="tracking_key",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="events", to="tracking.trackingkey"),
        ),
        migrations.AddField(
            model_name="trackingevent",
            name="used_fallback_key",
            field=models.BooleanField(default=False, help_text="True when the legacy/static key was used for ingestion"),
        ),
        migrations.AddIndex(
            model_name="trackingevent",
            index=models.Index(fields=["firm", "tracking_key"], name="tracking_event_key_idx"),
        ),
        migrations.AddIndex(
            model_name="sitemessage",
            index=models.Index(fields=["firm", "status"], name="site_message_status_idx"),
        ),
        migrations.AddIndex(
            model_name="sitemessage",
            index=models.Index(fields=["firm", "message_type"], name="site_message_type_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingkey",
            index=models.Index(fields=["firm", "is_active"], name="tracking_key_active_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingkey",
            index=models.Index(fields=["firm", "public_id"], name="tracking_key_public_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingkeyaudit",
            index=models.Index(fields=["firm", "action"], name="tracking_key_audit_action_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingabuseevent",
            index=models.Index(fields=["firm", "reason"], name="tracking_abuse_reason_idx"),
        ),
    ]
