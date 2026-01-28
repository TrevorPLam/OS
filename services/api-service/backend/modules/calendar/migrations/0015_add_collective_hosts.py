# Generated manually for TEAM-1: Implement Collective Events

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0014_timezone_intelligence'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Appointment: Add collective_hosts ManyToMany field
        migrations.AddField(
            model_name='appointment',
            name='collective_hosts',
            field=models.ManyToManyField(
                blank=True,
                help_text='All hosts assigned to this collective event appointment (required + available optional hosts)',
                related_name='collective_appointments',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
