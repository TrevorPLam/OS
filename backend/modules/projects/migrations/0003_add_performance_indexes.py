# Generated manually for TIER 5.2 performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_timeentry_approved_timeentry_approved_at_and_more'),
    ]

    operations = [
        # TimeEntry performance indexes for billing queries
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(
                fields=['project', 'approved', 'invoiced'],
                name='projects_time_bill_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(
                fields=['user', 'date', 'approved'],
                name='projects_time_user_idx'
            ),
        ),
        # Task performance indexes for Kanban queries
        migrations.AddIndex(
            model_name='task',
            index=models.Index(
                fields=['project', 'status', 'position'],
                name='projects_task_kanban_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(
                fields=['assigned_to', 'status', '-due_date'],
                name='projects_task_assigned_idx'
            ),
        ),
    ]
