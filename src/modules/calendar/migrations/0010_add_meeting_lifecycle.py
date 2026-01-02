# Generated migration for CAL-6: Build meeting lifecycle management

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calendar", "0009_add_scheduling_constraints"),
    ]

    operations = [
        # Update status field max_length and add new status choices
        migrations.AlterField(
            model_name="appointment",
            name="status",
            field=models.CharField(
                choices=[
                    ("requested", "Requested (Needs Approval)"),
                    ("confirmed", "Confirmed"),
                    ("rescheduled", "Rescheduled"),
                    ("cancelled", "Cancelled"),
                    ("completed", "Completed"),
                    ("no_show", "No Show"),
                    ("awaiting_confirmation", "Awaiting Confirmation"),
                ],
                default="confirmed",
                help_text="Appointment status",
                max_length=30,
            ),
        ),
        # Add lifecycle tracking fields
        migrations.AddField(
            model_name="appointment",
            name="rescheduled_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="When this appointment was rescheduled",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="rescheduled_from",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="rescheduled_to",
                to="calendar.appointment",
                help_text="Original appointment that this was rescheduled from",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="cancelled_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="When this appointment was cancelled",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="completed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="When this appointment was marked as completed",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="no_show_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="When this appointment was marked as no-show",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="no_show_party",
            field=models.CharField(
                blank=True,
                max_length=20,
                choices=[
                    ("client", "Client No-Show"),
                    ("staff", "Staff No-Show"),
                    ("both", "Both No-Show"),
                ],
                help_text="Which party didn't show up",
            ),
        ),
    ]
