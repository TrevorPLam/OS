# Generated migration for CAL-3: Implement rich event descriptions

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("calendar", "0006_add_multiple_durations"),
    ]

    operations = [
        # Add rich event description fields to AppointmentType
        migrations.AddField(
            model_name="appointmenttype",
            name="internal_name",
            field=models.CharField(
                blank=True,
                max_length=255,
                help_text="Internal name for staff use (if different from public display name)",
            ),
        ),
        migrations.AddField(
            model_name="appointmenttype",
            name="rich_description",
            field=models.TextField(
                blank=True,
                help_text="Rich HTML description with formatting, links, and embedded content",
            ),
        ),
        migrations.AddField(
            model_name="appointmenttype",
            name="description_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="calendar/event_images/",
                help_text="Image to display in event description",
            ),
        ),
    ]
