# Generated manually for TEAM-2: Build advanced Round Robin

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0015_add_collective_hosts'),
    ]

    operations = [
        # AppointmentType: Add advanced round robin strategy fields
        migrations.AddField(
            model_name='appointmenttype',
            name='round_robin_strategy',
            field=models.CharField(
                blank=True,
                choices=[
                    ('strict', 'Strict Round Robin (equal distribution regardless of availability)'),
                    ('optimize_availability', 'Optimize for Availability (favor most available)'),
                    ('weighted', 'Weighted Distribution (configurable weights per team member)'),
                    ('prioritize_capacity', 'Prioritize by Capacity (route to least-booked)'),
                ],
                default='strict',
                help_text='Strategy for distributing appointments in round robin pool',
                max_length=30
            ),
        ),
        migrations.AddField(
            model_name='appointmenttype',
            name='round_robin_weights',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Weights for weighted distribution strategy. Format: {user_id: weight}, e.g. {1: 2.0, 2: 1.5, 3: 1.0}. Higher weight = more appointments assigned."
            ),
        ),
        migrations.AddField(
            model_name='appointmenttype',
            name='round_robin_capacity_per_day',
            field=models.IntegerField(
                blank=True,
                help_text='Maximum appointments per person per day in round robin pool (null = unlimited)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='appointmenttype',
            name='round_robin_enable_rebalancing',
            field=models.BooleanField(
                default=False,
                help_text='Automatically rebalance distribution when imbalanced'
            ),
        ),
        migrations.AddField(
            model_name='appointmenttype',
            name='round_robin_rebalancing_threshold',
            field=models.DecimalField(
                decimal_places=2,
                default=0.20,
                help_text='Percentage threshold for rebalancing (e.g., 0.20 = trigger rebalance if any member is more than 20% off the average)',
                max_digits=5
            ),
        ),
    ]
