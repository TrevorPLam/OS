# Generated manually for Task 3.6: Gantt Chart/Timeline View

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_add_resource_planning_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectTimeline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('planned_start_date', models.DateField(blank=True, help_text='Planned project start date', null=True)),
                ('planned_end_date', models.DateField(blank=True, help_text='Planned project end date', null=True)),
                ('actual_start_date', models.DateField(blank=True, help_text='Actual project start date', null=True)),
                ('actual_end_date', models.DateField(blank=True, help_text='Actual project end date', null=True)),
                ('critical_path_task_ids', models.JSONField(blank=True, default=list, help_text='List of task IDs on the critical path')),
                ('critical_path_duration_days', models.IntegerField(default=0, help_text='Duration of critical path in days')),
                ('total_tasks', models.IntegerField(default=0, help_text='Total number of tasks')),
                ('completed_tasks', models.IntegerField(default=0, help_text='Number of completed tasks')),
                ('milestone_count', models.IntegerField(default=0, help_text='Number of milestones')),
                ('last_calculated_at', models.DateTimeField(blank=True, help_text='When timeline was last calculated', null=True)),
                ('calculation_metadata', models.JSONField(blank=True, default=dict, help_text='Metadata about timeline calculation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.OneToOneField(help_text='Project this timeline belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='timeline', to='projects.project')),
            ],
            options={
                'db_table': 'projects_timeline',
                'ordering': ['project'],
            },
        ),
        migrations.CreateModel(
            name='TaskSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('planned_start_date', models.DateField(blank=True, help_text='Planned start date', null=True)),
                ('planned_end_date', models.DateField(blank=True, help_text='Planned end date', null=True)),
                ('planned_duration_days', models.IntegerField(default=1, help_text='Planned duration in days', validators=[django.core.validators.MinValueValidator(1)])),
                ('actual_start_date', models.DateField(blank=True, help_text='Actual start date', null=True)),
                ('actual_end_date', models.DateField(blank=True, help_text='Actual end date', null=True)),
                ('actual_duration_days', models.IntegerField(blank=True, help_text='Actual duration in days', null=True)),
                ('constraint_type', models.CharField(choices=[('asap', 'As Soon As Possible'), ('alap', 'As Late As Possible'), ('must_start_on', 'Must Start On'), ('must_finish_on', 'Must Finish On'), ('start_no_earlier', 'Start No Earlier Than'), ('start_no_later', 'Start No Later Than'), ('finish_no_earlier', 'Finish No Earlier Than'), ('finish_no_later', 'Finish No Later Than')], default='asap', help_text='Scheduling constraint type', max_length=20)),
                ('constraint_date', models.DateField(blank=True, help_text='Date for constraint (if applicable)', null=True)),
                ('is_on_critical_path', models.BooleanField(default=False, help_text='Whether this task is on the critical path')),
                ('total_slack_days', models.IntegerField(default=0, help_text='Total slack/float in days (can delay without affecting project)')),
                ('free_slack_days', models.IntegerField(default=0, help_text='Free slack in days (can delay without affecting successor tasks)')),
                ('early_start_date', models.DateField(blank=True, help_text='Earliest possible start date', null=True)),
                ('early_finish_date', models.DateField(blank=True, help_text='Earliest possible finish date', null=True)),
                ('late_start_date', models.DateField(blank=True, help_text='Latest possible start date without delaying project', null=True)),
                ('late_finish_date', models.DateField(blank=True, help_text='Latest possible finish date without delaying project', null=True)),
                ('completion_percentage', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Task completion percentage (0-100)', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('is_milestone', models.BooleanField(default=False, help_text='Whether this task is a milestone (zero duration marker)')),
                ('milestone_date', models.DateField(blank=True, help_text='Date for milestone', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('task', models.OneToOneField(help_text='Task this schedule belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='schedule', to='projects.task')),
            ],
            options={
                'db_table': 'projects_task_schedule',
                'ordering': ['planned_start_date', 'task'],
            },
        ),
        migrations.CreateModel(
            name='TaskDependency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dependency_type', models.CharField(choices=[('finish_to_start', 'Finish-to-Start (FS)'), ('start_to_start', 'Start-to-Start (SS)'), ('finish_to_finish', 'Finish-to-Finish (FF)'), ('start_to_finish', 'Start-to-Finish (SF)')], default='finish_to_start', help_text='Type of dependency relationship', max_length=20)),
                ('lag_days', models.IntegerField(default=0, help_text='Lag time in days (positive = delay, negative = lead)')),
                ('notes', models.TextField(blank=True, help_text='Notes about this dependency')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('predecessor', models.ForeignKey(help_text='Task that must be completed first (or started first, depending on type)', on_delete=django.db.models.deletion.CASCADE, related_name='successor_dependencies', to='projects.task')),
                ('successor', models.ForeignKey(help_text='Task that depends on the predecessor', on_delete=django.db.models.deletion.CASCADE, related_name='predecessor_dependencies', to='projects.task')),
            ],
            options={
                'db_table': 'projects_task_dependency',
                'ordering': ['predecessor', 'successor'],
                'unique_together': {('predecessor', 'successor')},
            },
        ),
        migrations.AddIndex(
            model_name='taskschedule',
            index=models.Index(fields=['task'], name='proj_sch_task_idx'),
        ),
        migrations.AddIndex(
            model_name='taskschedule',
            index=models.Index(fields=['is_on_critical_path'], name='proj_sch_crit_idx'),
        ),
        migrations.AddIndex(
            model_name='taskschedule',
            index=models.Index(fields=['is_milestone'], name='proj_sch_mile_idx'),
        ),
        migrations.AddIndex(
            model_name='taskschedule',
            index=models.Index(fields=['planned_start_date'], name='proj_sch_start_idx'),
        ),
        migrations.AddIndex(
            model_name='taskdependency',
            index=models.Index(fields=['predecessor'], name='proj_dep_pred_idx'),
        ),
        migrations.AddIndex(
            model_name='taskdependency',
            index=models.Index(fields=['successor'], name='proj_dep_succ_idx'),
        ),
    ]
