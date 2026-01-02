# Generated migration for CAL-5: Implement scheduling constraints

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calendar", "0008_add_event_customization"),
    ]

    operations = [
        # Add scheduling constraint fields to AppointmentType
        migrations.AddField(
            model_name="appointmenttype",
            name="daily_meeting_limit",
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text="Maximum number of this event type that can be booked per day (null = unlimited)",
            ),
        ),
        migrations.AddField(
            model_name="appointmenttype",
            name="min_notice_hours",
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text="Minimum notice required before booking (hours, 1-720). Overrides profile default if set.",
            ),
        ),
        migrations.AddField(
            model_name="appointmenttype",
            name="max_notice_days",
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text="Maximum days in advance for booking (1-365). Overrides profile default if set.",
            ),
        ),
        migrations.AddField(
            model_name="appointmenttype",
            name="rolling_window_days",
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text=(
                    "Rolling availability window in days (e.g., 30 = only show next 30 days). "
                    "If set, overrides max_notice_days with a rolling window."
                ),
            ),
        ),
    ]
