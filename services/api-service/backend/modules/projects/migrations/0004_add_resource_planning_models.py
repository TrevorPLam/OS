# Generated manually for Task 3.2: Resource planning & allocation system

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_add_performance_indexes'),
        ('firm', '0012_user_profiles'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create ResourceAllocation model
        migrations.CreateModel(
            name='ResourceAllocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allocation_type', models.CharField(choices=[('dedicated', 'Dedicated (100%)'), ('part_time', 'Part-Time'), ('as_needed', 'As Needed'), ('backup', 'Backup Resource')], default='part_time', help_text='Type of allocation', max_length=20)),
                ('allocation_percentage', models.DecimalField(decimal_places=2, help_text='Percentage of resource\'s time allocated (0-100)', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.00')), django.core.validators.MinValueValidator(Decimal('100.00'))])),
                ('hourly_rate', models.DecimalField(blank=True, decimal_places=2, help_text='Hourly billing rate for this resource on this project', max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('start_date', models.DateField(help_text='When this allocation starts')),
                ('end_date', models.DateField(help_text='When this allocation ends')),
                ('role', models.CharField(blank=True, help_text='Role of this resource on the project (e.g., \'Lead Consultant\', \'Analyst\')', max_length=100)),
                ('is_billable', models.BooleanField(default=True, help_text='Whether this resource\'s time is billable to the client')),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='planned', max_length=20)),
                ('notes', models.TextField(blank=True, help_text='Notes about this allocation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(help_text='User who created this allocation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_allocations', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(help_text='Project this resource is allocated to', on_delete=django.db.models.deletion.CASCADE, related_name='resource_allocations', to='projects.project')),
                ('resource', models.ForeignKey(help_text='Team member allocated to this project', on_delete=django.db.models.deletion.CASCADE, related_name='allocations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'projects_resource_allocation',
                'ordering': ['start_date', 'project'],
            },
        ),
        
        # Add indexes for ResourceAllocation
        migrations.AddIndex(
            model_name='resourceallocation',
            index=models.Index(fields=['project', 'status'], name='proj_res_alloc_proj_status_idx'),
        ),
        migrations.AddIndex(
            model_name='resourceallocation',
            index=models.Index(fields=['resource', 'status', 'start_date'], name='proj_res_alloc_res_status_idx'),
        ),
        migrations.AddIndex(
            model_name='resourceallocation',
            index=models.Index(fields=['start_date', 'end_date'], name='proj_res_alloc_dates_idx'),
        ),
        
        # Create ResourceCapacity model
        migrations.CreateModel(
            name='ResourceCapacity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(help_text='Date of capacity entry')),
                ('available_hours', models.DecimalField(decimal_places=2, default=Decimal('8.00'), help_text='Available hours for this date (default 8 hours)', max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('unavailable_hours', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Hours unavailable due to leave, holiday, etc.', max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('unavailability_type', models.CharField(blank=True, choices=[('vacation', 'Vacation'), ('sick_leave', 'Sick Leave'), ('holiday', 'Public Holiday'), ('training', 'Training/Conference'), ('administrative', 'Administrative Time'), ('other', 'Other')], help_text='Reason for unavailability', max_length=20)),
                ('notes', models.TextField(blank=True, help_text='Notes about capacity on this date')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm', models.ForeignKey(help_text='Firm this capacity entry belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='resource_capacities', to='firm.firm')),
                ('resource', models.ForeignKey(help_text='Team member this capacity entry applies to', on_delete=django.db.models.deletion.CASCADE, related_name='capacity_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'projects_resource_capacity',
                'ordering': ['date', 'resource'],
            },
        ),
        
        # Add indexes for ResourceCapacity
        migrations.AddIndex(
            model_name='resourcecapacity',
            index=models.Index(fields=['firm', 'resource', 'date'], name='proj_res_cap_firm_res_date_idx'),
        ),
        migrations.AddIndex(
            model_name='resourcecapacity',
            index=models.Index(fields=['firm', 'date'], name='proj_res_cap_firm_date_idx'),
        ),
        
        # Add unique constraint for ResourceCapacity
        migrations.AddConstraint(
            model_name='resourcecapacity',
            constraint=models.UniqueConstraint(fields=['resource', 'date'], name='projects_resourcecapacity_resource_date_unique'),
        ),
    ]
