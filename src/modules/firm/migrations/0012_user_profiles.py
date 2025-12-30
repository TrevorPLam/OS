# Generated migration for UserProfile model

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0011_role_based_views'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_photo', models.ImageField(blank=True, help_text='Profile photo (recommended: 400x400px, max 2MB)', null=True, upload_to='profile_photos/%Y/%m/')),
                ('job_title', models.CharField(blank=True, help_text='Job title (overrides default title)', max_length=200)),
                ('bio', models.TextField(blank=True, help_text='Short bio/description (max 500 characters)', max_length=500)),
                ('email_signature_html', models.TextField(blank=True, help_text='HTML email signature')),
                ('email_signature_plain', models.TextField(blank=True, help_text='Plain text email signature (fallback for non-HTML emails)')),
                ('include_signature_by_default', models.BooleanField(default=True, help_text='Automatically include signature in outgoing emails')),
                ('personal_meeting_link', models.URLField(blank=True, help_text='Personal meeting link (Zoom, Teams, Google Meet, etc.)', max_length=500, validators=[django.core.validators.URLValidator()])),
                ('meeting_link_description', models.CharField(blank=True, help_text='Description for meeting link (e.g., "My Zoom Room", "Calendar Link")', max_length=100)),
                ('calendar_booking_link', models.URLField(blank=True, help_text='Personal calendar booking link (Calendly-style link for this user)', max_length=500, validators=[django.core.validators.URLValidator()])),
                ('phone_number', models.CharField(blank=True, help_text='Direct phone number', max_length=50)),
                ('phone_extension', models.CharField(blank=True, help_text='Phone extension', max_length=20)),
                ('mobile_number', models.CharField(blank=True, help_text='Mobile/cell phone number', max_length=50)),
                ('office_location', models.CharField(blank=True, help_text='Office location or address', max_length=200)),
                ('linkedin_url', models.URLField(blank=True, help_text='LinkedIn profile URL', max_length=500, validators=[django.core.validators.URLValidator()])),
                ('twitter_handle', models.CharField(blank=True, help_text='Twitter/X handle (without @)', max_length=50)),
                ('website_url', models.URLField(blank=True, help_text='Personal or professional website', max_length=500, validators=[django.core.validators.URLValidator()])),
                ('timezone_preference', models.CharField(blank=True, help_text='Preferred timezone (e.g., "America/New_York")', max_length=100)),
                ('language_preference', models.CharField(default='en', help_text='Preferred language code (e.g., "en", "es", "fr")', max_length=10)),
                ('notification_preferences', models.JSONField(blank=True, default=dict, help_text='Notification preferences (email, SMS, push, etc.)')),
                ('show_phone_in_directory', models.BooleanField(default=True, help_text='Show phone number in team directory')),
                ('show_email_in_directory', models.BooleanField(default=True, help_text='Show email in team directory')),
                ('show_availability_to_clients', models.BooleanField(default=False, help_text='Allow clients to see availability and book meetings directly')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm_membership', models.OneToOneField(help_text='FirmMembership this profile extends', on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='firm.firmmembership')),
            ],
            options={
                'db_table': 'user_profiles',
                'ordering': ['firm_membership'],
            },
        ),
    ]
