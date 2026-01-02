# Generated manually for TEAM-3: Implement Group Events

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0016_add_advanced_round_robin'),
        ('clients', '0001_initial'),  # Assuming clients app exists
    ]

    operations = [
        # GroupEventAttendee model
        migrations.CreateModel(
            name='GroupEventAttendee',
            fields=[
                ('attendee_id', models.BigAutoField(help_text='', primary_key=True, serialize=False)),
                ('attendee_name', models.CharField(blank=True, help_text='Name of attendee (if not a contact)', max_length=255)),
                ('attendee_email', models.EmailField(blank=True, help_text='Email of attendee (if not a contact)', max_length=254)),
                ('status', models.CharField(choices=[('registered', 'Registered'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('no_show', 'No Show'), ('attended', 'Attended')], default='registered', help_text='Attendee status', max_length=20)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment', models.ForeignKey(help_text='Group event appointment', on_delete=django.db.models.deletion.CASCADE, related_name='group_attendees', to='calendar.appointment')),
                ('contact', models.ForeignKey(blank=True, help_text='Contact attending the group event', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group_event_attendances', to='clients.contact')),
            ],
            options={
                'db_table': 'calendar_group_event_attendees',
                'ordering': ['registered_at'],
            },
        ),
        
        # GroupEventWaitlist model
        migrations.CreateModel(
            name='GroupEventWaitlist',
            fields=[
                ('waitlist_id', models.BigAutoField(help_text='', primary_key=True, serialize=False)),
                ('waitlist_name', models.CharField(blank=True, help_text='Name of person on waitlist (if not a contact)', max_length=255)),
                ('waitlist_email', models.EmailField(blank=True, help_text='Email of person on waitlist (if not a contact)', max_length=254)),
                ('status', models.CharField(choices=[('waiting', 'Waiting'), ('promoted', 'Promoted to Attendee'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], default='waiting', help_text='Waitlist entry status', max_length=20)),
                ('priority', models.IntegerField(default=0, help_text='Priority for promotion (higher = promoted first). Default is based on join order.')),
                ('promoted_at', models.DateTimeField(blank=True, help_text='When this entry was promoted to attendee', null=True)),
                ('notified_at', models.DateTimeField(blank=True, help_text='When promotion notification was sent', null=True)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment', models.ForeignKey(help_text='Group event appointment', on_delete=django.db.models.deletion.CASCADE, related_name='waitlist_entries', to='calendar.appointment')),
                ('contact', models.ForeignKey(blank=True, help_text='Contact on the waitlist', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group_event_waitlist', to='clients.contact')),
            ],
            options={
                'db_table': 'calendar_group_event_waitlist',
                'ordering': ['-priority', 'joined_at'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='groupeventattendee',
            index=models.Index(fields=['appointment', 'status'], name='calendar_att_app_sta_idx'),
        ),
        migrations.AddIndex(
            model_name='groupeventattendee',
            index=models.Index(fields=['contact'], name='calendar_att_con_idx'),
        ),
        migrations.AddIndex(
            model_name='groupeventwaitlist',
            index=models.Index(fields=['appointment', 'status'], name='calendar_wai_app_sta_idx'),
        ),
        migrations.AddIndex(
            model_name='groupeventwaitlist',
            index=models.Index(fields=['contact'], name='calendar_wai_con_idx'),
        ),
        migrations.AddIndex(
            model_name='groupeventwaitlist',
            index=models.Index(fields=['status', 'priority', 'joined_at'], name='calendar_wai_sta_pri_joi_idx'),
        ),
    ]
