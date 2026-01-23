# Generated migration for CAL-2: Add multiple duration options

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0005_add_event_categories'),
    ]

    operations = [
        # Add multiple duration fields to AppointmentType
        migrations.AddField(
            model_name='appointmenttype',
            name='enable_multiple_durations',
            field=models.BooleanField(
                default=False,
                help_text='Allow bookers to choose from multiple duration options',
            ),
        ),
        migrations.AddField(
            model_name='appointmenttype',
            name='duration_options',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Array of duration options in minutes (e.g., [15, 30, 60]). "
                    "If enabled, booker can select from these options. Each option can optionally include "
                    "pricing if duration-based pricing is used: "
                    "[{\"minutes\": 30, \"price\": 50.00, \"label\": \"30 min session\"}, ...]"
                ),
            ),
        ),
        
        # Add selected duration fields to Appointment
        migrations.AddField(
            model_name='appointment',
            name='selected_duration_minutes',
            field=models.IntegerField(
                blank=True,
                help_text='Duration selected by booker (if multiple options were available)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='selected_duration_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Price for selected duration (if duration-based pricing is used)',
                max_digits=10,
                null=True,
            ),
        ),
    ]
