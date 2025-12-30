"""
User profile customization extensions.

Extends FirmMembership with profile customization features:
- Profile photos
- Email signatures
- Meeting links
- Personal availability preferences
"""

from django.db import models
from django.conf import settings
from django.core.validators import URLValidator
from modules.firm.models import FirmMembership


class UserProfile(models.Model):
    """
    Extended user profile for firm members.

    Provides customization options for staff users:
    - Profile photo
    - Email signature (HTML)
    - Personal meeting link
    - Bio/title customization
    - Contact preferences
    """

    firm_membership = models.OneToOneField(
        FirmMembership,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='FirmMembership this profile extends'
    )

    # Visual Identity
    profile_photo = models.ImageField(
        upload_to='profile_photos/%Y/%m/',
        null=True,
        blank=True,
        help_text='Profile photo (recommended: 400x400px, max 2MB)'
    )
    job_title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Job title (overrides default title)'
    )
    bio = models.TextField(
        blank=True,
        max_length=500,
        help_text='Short bio/description (max 500 characters)'
    )

    # Email Signature
    email_signature_html = models.TextField(
        blank=True,
        help_text='HTML email signature'
    )
    email_signature_plain = models.TextField(
        blank=True,
        help_text='Plain text email signature (fallback for non-HTML emails)'
    )
    include_signature_by_default = models.BooleanField(
        default=True,
        help_text='Automatically include signature in outgoing emails'
    )

    # Meeting & Scheduling
    personal_meeting_link = models.URLField(
        blank=True,
        max_length=500,
        validators=[URLValidator()],
        help_text='Personal meeting link (Zoom, Teams, Google Meet, etc.)'
    )
    meeting_link_description = models.CharField(
        max_length=100,
        blank=True,
        help_text='Description for meeting link (e.g., "My Zoom Room", "Calendar Link")'
    )
    calendar_booking_link = models.URLField(
        blank=True,
        max_length=500,
        validators=[URLValidator()],
        help_text='Personal calendar booking link (Calendly-style link for this user)'
    )

    # Contact Information
    phone_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Direct phone number'
    )
    phone_extension = models.CharField(
        max_length=20,
        blank=True,
        help_text='Phone extension'
    )
    mobile_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Mobile/cell phone number'
    )
    office_location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Office location or address'
    )

    # Social & Professional Links
    linkedin_url = models.URLField(
        blank=True,
        max_length=500,
        validators=[URLValidator()],
        help_text='LinkedIn profile URL'
    )
    twitter_handle = models.CharField(
        max_length=50,
        blank=True,
        help_text='Twitter/X handle (without @)'
    )
    website_url = models.URLField(
        blank=True,
        max_length=500,
        validators=[URLValidator()],
        help_text='Personal or professional website'
    )

    # Preferences
    timezone_preference = models.CharField(
        max_length=100,
        blank=True,
        help_text='Preferred timezone (e.g., "America/New_York")'
    )
    language_preference = models.CharField(
        max_length=10,
        default='en',
        help_text='Preferred language code (e.g., "en", "es", "fr")'
    )
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text='Notification preferences (email, SMS, push, etc.)'
    )

    # Visibility Settings
    show_phone_in_directory = models.BooleanField(
        default=True,
        help_text='Show phone number in team directory'
    )
    show_email_in_directory = models.BooleanField(
        default=True,
        help_text='Show email in team directory'
    )
    show_availability_to_clients = models.BooleanField(
        default=False,
        help_text='Allow clients to see availability and book meetings directly'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        ordering = ['firm_membership']

    def __str__(self):
        return f"Profile for {self.firm_membership.user.get_full_name()}"

    def get_display_name(self):
        """Get display name with custom title if set."""
        name = self.firm_membership.user.get_full_name()
        if self.job_title:
            return f"{name}, {self.job_title}"
        return name

    def get_signature(self, html=True):
        """
        Get email signature.

        Args:
            html (bool): If True, return HTML signature; otherwise plain text

        Returns:
            str: Email signature
        """
        if html and self.email_signature_html:
            return self.email_signature_html
        elif self.email_signature_plain:
            return self.email_signature_plain
        else:
            # Generate default signature
            return self.generate_default_signature(html)

    def generate_default_signature(self, html=True):
        """
        Generate a default email signature.

        Args:
            html (bool): If True, generate HTML; otherwise plain text

        Returns:
            str: Generated signature
        """
        user = self.firm_membership.user
        name = user.get_full_name()
        title = self.job_title or ''
        email = user.email
        phone = self.phone_number or ''
        firm_name = self.firm_membership.firm.name

        if html:
            parts = [f'<p><strong>{name}</strong>']
            if title:
                parts.append(f'<br>{title}')
            parts.append(f'<br>{firm_name}')
            if phone:
                parts.append(f'<br>Phone: {phone}')
            parts.append(f'<br>Email: <a href="mailto:{email}">{email}</a>')
            if self.personal_meeting_link:
                parts.append(f'<br><a href="{self.personal_meeting_link}">Schedule a Meeting</a>')
            parts.append('</p>')
            return ''.join(parts)
        else:
            parts = [name]
            if title:
                parts.append(title)
            parts.append(firm_name)
            if phone:
                parts.append(f'Phone: {phone}')
            parts.append(f'Email: {email}')
            if self.personal_meeting_link:
                parts.append(f'Meeting Link: {self.personal_meeting_link}')
            return '\n'.join(parts)

    def get_profile_photo_url(self):
        """Get profile photo URL or default avatar."""
        if self.profile_photo:
            return self.profile_photo.url
        # Return gravatar or default avatar
        import hashlib
        email_hash = hashlib.md5(self.firm_membership.user.email.lower().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=mp&s=400"
