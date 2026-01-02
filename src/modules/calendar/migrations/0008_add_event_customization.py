# Generated migration for CAL-4: Add event customization features

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("calendar", "0007_add_rich_event_descriptions"),
    ]

    operations = [
        # Add "archived" status option
        migrations.AlterField(
            model_name="appointmenttype",
            name="status",
            field=models.CharField(
                choices=[("active", "Active"), ("inactive", "Inactive"), ("archived", "Archived")],
                default="active",
                help_text="Event status: active, inactive, or archived",
                max_length=20,
            ),
        ),
        # Add event customization fields to AppointmentType
        migrations.AddField(
            model_name="appointmenttype",
            name="url_slug",
            field=models.SlugField(
                blank=True,
                max_length=100,
                help_text="Custom URL slug for this event type (e.g., 'strategy-session'). Auto-generated if not provided.",
            ),
        ),
        migrations.AddField(
            model_name="appointmenttype",
            name="color_code",
            field=models.CharField(
                blank=True,
                default="",
                max_length=7,
                help_text="Color code for visual identification (hex format: #RRGGBB)",
            ),
        ),
        migrations.AddField(
            model_name="appointmenttype",
            name="availability_overrides",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "Event-specific availability overrides. "
                    "Can override weekly_hours, exceptions, buffer times, etc. "
                    "JSON format: {'weekly_hours': {...}, 'min_notice_minutes': 120, ...}"
                ),
            ),
        ),
        # Add index for firm + url_slug
        migrations.AddIndex(
            model_name="appointmenttype",
            index=models.Index(fields=["firm", "url_slug"], name="calendar_apt_fir_slug_idx"),
        ),
        # Add unique constraint for firm + url_slug (when url_slug is not empty)
        migrations.AddConstraint(
            model_name="appointmenttype",
            constraint=models.UniqueConstraint(
                condition=models.Q(("url_slug__gt", "")),
                fields=("firm", "url_slug"),
                name="calendar_apt_firm_slug_uniq",
            ),
        ),
    ]
