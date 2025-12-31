# Generated manually for ASSESS-I5.6: Fix SSRF validation gaps
# Replace URLValidator() with validate_safe_url for SSRF protection

from django.db import migrations, models
from modules.core.validators import validate_safe_url


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0012_user_profiles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='personal_meeting_link',
            field=models.URLField(
                blank=True,
                max_length=500,
                validators=[validate_safe_url],
                help_text='Personal meeting link (Zoom, Teams, Google Meet, etc.)'
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='calendar_booking_link',
            field=models.URLField(
                blank=True,
                max_length=500,
                validators=[validate_safe_url],
                help_text='Personal calendar booking link (Calendly-style link for this user)'
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='linkedin_url',
            field=models.URLField(
                blank=True,
                max_length=500,
                validators=[validate_safe_url],
                help_text='LinkedIn profile URL'
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='website_url',
            field=models.URLField(
                blank=True,
                max_length=500,
                validators=[validate_safe_url],
                help_text='Personal or professional website'
            ),
        ),
    ]
