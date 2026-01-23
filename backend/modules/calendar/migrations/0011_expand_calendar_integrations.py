# Generated manually for AVAIL-1: Expand calendar integrations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0010_add_meeting_lifecycle'),
    ]

    operations = [
        # Add new provider choice 'ical'
        migrations.AlterField(
            model_name='oauthconnection',
            name='provider',
            field=models.CharField(
                choices=[
                    ('google', 'Google Calendar'),
                    ('microsoft', 'Microsoft Outlook/Office 365'),
                    ('apple', 'Apple Calendar (iCloud)'),
                    ('ical', 'iCal/vCal Feed (Generic)'),
                ],
                help_text='Calendar provider',
                max_length=20
            ),
        ),
        # Add iCal feed URL field
        migrations.AddField(
            model_name='oauthconnection',
            name='ical_feed_url',
            field=models.URLField(
                blank=True,
                help_text='iCal/vCal feed URL (for apple and ical providers)',
                max_length=512
            ),
        ),
        # Add all-day event handling preference
        migrations.AddField(
            model_name='oauthconnection',
            name='treat_all_day_as_busy',
            field=models.BooleanField(
                default=False,
                help_text='Whether to treat all-day events as busy (default: False)'
            ),
        ),
        # Add tentative event handling preference
        migrations.AddField(
            model_name='oauthconnection',
            name='treat_tentative_as_busy',
            field=models.BooleanField(
                default=True,
                help_text='Whether to treat tentative/optional events as busy (default: True)'
            ),
        ),
        # Remove unique_together constraint to allow multiple calendar connections
        migrations.AlterUniqueTogether(
            name='oauthconnection',
            unique_together=set(),
        ),
    ]
