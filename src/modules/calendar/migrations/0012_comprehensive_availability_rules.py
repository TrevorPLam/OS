# Generated manually for AVAIL-2: Build comprehensive availability rules

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0011_expand_calendar_integrations'),
    ]

    operations = [
        # Add recurring unavailability blocks
        migrations.AddField(
            model_name='availabilityprofile',
            name='recurring_unavailability',
            field=models.JSONField(
                default=list,
                help_text="Recurring unavailability blocks (JSON array of {day_of_week: 'monday', start: '12:00', end: '13:00', reason: 'Lunch'})"
            ),
        ),
        # Add auto-detect holidays flag
        migrations.AddField(
            model_name='availabilityprofile',
            name='auto_detect_holidays',
            field=models.BooleanField(
                default=False,
                help_text='Automatically block common holidays based on timezone/country'
            ),
        ),
        # Add custom holidays
        migrations.AddField(
            model_name='availabilityprofile',
            name='custom_holidays',
            field=models.JSONField(
                default=list,
                help_text="Custom holiday dates (JSON array of {date: 'YYYY-MM-DD', name: 'Company Holiday'})"
            ),
        ),
        # Add minimum gap between meetings
        migrations.AddField(
            model_name='availabilityprofile',
            name='min_gap_between_meetings_minutes',
            field=models.IntegerField(
                default=0,
                help_text='Minimum gap between meetings (minutes). 0 means back-to-back allowed.'
            ),
        ),
        # Add maximum gap between meetings
        migrations.AddField(
            model_name='availabilityprofile',
            name='max_gap_between_meetings_minutes',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='Maximum gap between meetings (minutes). Null means no limit.'
            ),
        ),
    ]
