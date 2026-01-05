from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("firm", "0001_initial"),
        ("tracking", "0002_tracking_keys_and_site_messages"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteMessageImpression",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visitor_id", models.UUIDField()),
                (
                    "delivery_id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, help_text="Stable id per delivery to group events"
                    ),
                ),
                ("kind", models.CharField(choices=[("delivered", "Delivered"), ("view", "Viewed"), ("click", "Clicked")], max_length=20)),
                ("variant", models.CharField(blank=True, max_length=100)),
                ("url", models.TextField(blank=True)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="site_message_impressions",
                        to="firm.firm",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="+",
                        to="tracking.trackingsession",
                    ),
                ),
                (
                    "site_message",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, related_name="impressions", to="tracking.sitemessage"
                    ),
                ),
            ],
            options={
                "db_table": "tracking_site_message_impression",
                "ordering": ["-occurred_at"],
            },
        ),
        migrations.AddIndex(
            model_name="sitemessageimpression",
            index=models.Index(
                fields=["firm", "visitor_id", "site_message"], name="site_message_impr_freq_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="sitemessageimpression",
            index=models.Index(fields=["firm", "delivery_id"], name="site_message_impr_delivery_idx"),
        ),
    ]
