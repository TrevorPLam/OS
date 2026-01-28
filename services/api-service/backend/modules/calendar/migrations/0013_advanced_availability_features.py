# Generated manually for AVAIL-3: Add advanced availability features

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0012_comprehensive_availability_rules'),
    ]

    operations = [
        # BookingLink: Add secret event support
        migrations.AddField(
            model_name='bookinglink',
            name='is_secret',
            field=models.BooleanField(
                default=False,
                help_text='Secret events are only accessible via direct link, not listed publicly'
            ),
        ),
        # BookingLink: Add password protection
        migrations.AddField(
            model_name='bookinglink',
            name='password_protected',
            field=models.BooleanField(
                default=False,
                help_text='Require password to book'
            ),
        ),
        migrations.AddField(
            model_name='bookinglink',
            name='password_hash',
            field=models.CharField(
                blank=True,
                help_text='Hashed password for protected booking links',
                max_length=255
            ),
        ),
        # BookingLink: Add email domain restrictions
        migrations.AddField(
            model_name='bookinglink',
            name='allowed_email_domains',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Whitelist of allowed email domains (e.g., ['example.com', 'partner.com']). Empty means all allowed."
            ),
        ),
        migrations.AddField(
            model_name='bookinglink',
            name='blocked_email_domains',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Blacklist of blocked email domains (e.g., ['spam.com'])"
            ),
        ),
        # AvailabilityProfile: Add location-based availability
        migrations.AddField(
            model_name='availabilityprofile',
            name='location_based_schedules',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Different schedules per location (JSON: {location_name: {weekly_hours: {...}, timezone: '...'}})"
            ),
        ),
    ]
