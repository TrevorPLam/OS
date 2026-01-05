import uuid

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("firm", "0013_remove_provisioninglog_firm_and_more"),
        ("clients", "0014_add_contact_location_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackingSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visitor_id", models.UUIDField(default=uuid.uuid4, help_text="Stable visitor identifier")),
                ("session_id", models.UUIDField(default=uuid.uuid4, help_text="Session identifier (rotates after inactivity window)")),
                ("consent_state", models.CharField(choices=[("pending", "Pending"), ("granted", "Granted"), ("denied", "Denied")], default="pending", max_length=20)),
                ("user_agent_hash", models.CharField(blank=True, help_text="Hashed user agent for analytics grouping", max_length=64)),
                ("first_seen_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("firm", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="tracking_sessions", to="firm.firm")),
            ],
            options={
                "db_table": "tracking_session",
            },
        ),
        migrations.CreateModel(
            name="TrackingEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("page_view", "Page View"), ("custom_event", "Custom Event"), ("identity", "Identity")], max_length=30)),
                ("name", models.CharField(max_length=255)),
                ("url", models.TextField(blank=True)),
                ("referrer", models.TextField(blank=True)),
                ("properties", models.JSONField(blank=True, default=dict)),
                ("consent_state", models.CharField(default="pending", max_length=20)),
                ("ip_truncated", models.CharField(blank=True, help_text="Anonymized IP (CIDR truncated)", max_length=64)),
                ("occurred_at", models.DateTimeField(default=timezone.now)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("user_agent_hash", models.CharField(blank=True, max_length=64)),
                ("contact", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="tracking_events", to="clients.contact")),
                ("firm", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="tracking_events", to="firm.firm")),
                ("session", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="events", to="tracking.trackingsession")),
            ],
            options={
                "db_table": "tracking_event",
                "ordering": ["-occurred_at"],
            },
        ),
        migrations.AddIndex(
            model_name="trackingevent",
            index=models.Index(fields=["firm", "event_type"], name="tracking_event_type_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingevent",
            index=models.Index(fields=["firm", "occurred_at"], name="tracking_event_occurred_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingevent",
            index=models.Index(fields=["firm", "url"], name="tracking_event_url_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingsession",
            index=models.Index(fields=["firm", "visitor_id"], name="tracking_session_visitor_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingsession",
            index=models.Index(fields=["firm", "session_id"], name="tracking_session_session_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="trackingsession",
            unique_together={("firm", "session_id")},
        ),
    ]
