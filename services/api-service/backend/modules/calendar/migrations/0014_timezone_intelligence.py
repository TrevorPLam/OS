# Generated manually for AVAIL-4: Implement timezone intelligence

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0013_advanced_availability_features'),
    ]

    operations = [
        # Appointment: Add invitee timezone tracking
        migrations.AddField(
            model_name='appointment',
            name='invitee_timezone',
            field=models.CharField(
                blank=True,
                help_text='Auto-detected timezone of the invitee/booker',
                max_length=100
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='invitee_timezone_offset_minutes',
            field=models.IntegerField(
                blank=True,
                help_text='Browser timezone offset in minutes (for DST handling)',
                null=True
            ),
        ),
    ]
