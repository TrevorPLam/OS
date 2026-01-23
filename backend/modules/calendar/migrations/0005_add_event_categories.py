# Generated migration for CAL-1: Implement event type categories

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('calendar', '0004_meetingpoll_meetingpollvote_meetingworkflow_and_more'),
    ]

    operations = [
        # Add event_category field
        migrations.AddField(
            model_name='appointmenttype',
            name='event_category',
            field=models.CharField(
                choices=[
                    ('one_on_one', 'One-on-One'),
                    ('group', 'Group Event (one-to-many)'),
                    ('collective', 'Collective Event (multiple hosts, overlapping availability)'),
                    ('round_robin', 'Round Robin (distribute across team)'),
                ],
                default='one_on_one',
                help_text='Event type category (one-on-one, group, collective, or round robin)',
                max_length=20,
            ),
        ),
        
        # Add group event fields
        migrations.AddField(
            model_name='appointmenttype',
            name='max_attendees',
            field=models.IntegerField(
                blank=True,
                help_text='Maximum number of attendees for group events (2-1000). Required for group events.',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='appointmenttype',
            name='enable_waitlist',
            field=models.BooleanField(
                default=False,
                help_text='Enable waitlist when group event reaches max capacity',
            ),
        ),
        
        # Add collective event fields (ManyToMany)
        migrations.AddField(
            model_name='appointmenttype',
            name='required_hosts',
            field=models.ManyToManyField(
                blank=True,
                help_text='Required hosts for collective events (all must be available)',
                related_name='collective_required_appointments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='appointmenttype',
            name='optional_hosts',
            field=models.ManyToManyField(
                blank=True,
                help_text='Optional hosts for collective events',
                related_name='collective_optional_appointments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        
        # Add round robin field (ManyToMany)
        migrations.AddField(
            model_name='appointmenttype',
            name='round_robin_pool',
            field=models.ManyToManyField(
                blank=True,
                help_text='Pool of staff members for round robin distribution',
                related_name='round_robin_appointments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        
        # Add index for event_category
        migrations.AddIndex(
            model_name='appointmenttype',
            index=models.Index(fields=['firm', 'event_category'], name='calendar_apt_fir_cat_idx'),
        ),
    ]
