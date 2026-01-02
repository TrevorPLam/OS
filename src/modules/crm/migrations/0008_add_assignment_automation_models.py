# Generated manually for DEAL-5: Assignment Automation

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crm', '0007_add_pipeline_and_deal_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='DealAssignmentRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Rule name', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Rule description')),
                ('assignment_type', models.CharField(choices=[('round_robin', 'Round Robin'), ('territory', 'Territory-Based'), ('lead_source', 'Lead Source'), ('deal_value', 'Deal Value'), ('load_balance', 'Load Balanced')], default='round_robin', help_text='Type of assignment logic', max_length=50)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this rule is active')),
                ('priority', models.IntegerField(default=0, help_text='Rule priority (higher = evaluated first)')),
                ('territory_field', models.CharField(blank=True, help_text="Field to use for territory matching (e.g., 'account.state', 'account.country')", max_length=100)),
                ('territory_mapping', models.JSONField(blank=True, default=dict, help_text='Territory to user mapping {territory: user_id}')),
                ('min_deal_value', models.DecimalField(blank=True, decimal_places=2, help_text='Minimum deal value to trigger this rule', max_digits=15, null=True)),
                ('max_deal_value', models.DecimalField(blank=True, decimal_places=2, help_text='Maximum deal value to trigger this rule', max_digits=15, null=True)),
                ('lead_sources', models.JSONField(blank=True, default=list, help_text='List of lead sources to trigger this rule')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_assignment_rules', to=settings.AUTH_USER_MODEL)),
                ('firm', models.ForeignKey(help_text='Firm (workspace) this rule belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='deal_assignment_rules', to='firm.firm')),
                ('last_assigned_user', models.ForeignKey(blank=True, help_text='Last user assigned (for round-robin)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='last_assigned_rules', to=settings.AUTH_USER_MODEL)),
                ('pipeline', models.ForeignKey(blank=True, help_text='Apply rule to specific pipeline (null = all pipelines)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assignment_rules', to='crm.pipeline')),
                ('stage', models.ForeignKey(blank=True, help_text='Apply rule when deal enters this stage (null = any stage)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assignment_rules', to='crm.pipelinestage')),
                ('target_users', models.ManyToManyField(help_text='Users to assign deals to', related_name='deal_assignment_rules', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'crm_deal_assignment_rule',
                'ordering': ['-priority', 'name'],
                'indexes': [
                    models.Index(fields=['firm', 'is_active'], name='crm_assign_rule_firm_active_idx'),
                    models.Index(fields=['pipeline', 'is_active'], name='crm_assign_rule_pipe_active_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='DealStageAutomation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Automation name', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Automation description')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this automation is active')),
                ('trigger_type', models.CharField(choices=[('enter', 'On Enter Stage'), ('exit', 'On Exit Stage')], default='enter', help_text='When to trigger', max_length=10)),
                ('action_type', models.CharField(choices=[('assign_user', 'Assign to User'), ('create_task', 'Create Task'), ('send_notification', 'Send Notification'), ('update_field', 'Update Field')], help_text='Type of action to perform', max_length=50)),
                ('action_config', models.JSONField(default=dict, help_text='Action configuration parameters')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_stage_automations', to=settings.AUTH_USER_MODEL)),
                ('firm', models.ForeignKey(help_text='Firm (workspace) this automation belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='deal_stage_automations', to='firm.firm')),
                ('pipeline', models.ForeignKey(help_text='Pipeline to monitor', on_delete=django.db.models.deletion.CASCADE, related_name='stage_automations', to='crm.pipeline')),
                ('stage', models.ForeignKey(help_text='Stage that triggers this automation', on_delete=django.db.models.deletion.CASCADE, related_name='stage_automations', to='crm.pipelinestage')),
            ],
            options={
                'db_table': 'crm_deal_stage_automation',
                'ordering': ['pipeline', 'stage', 'name'],
                'indexes': [
                    models.Index(fields=['firm', 'is_active'], name='crm_stage_auto_firm_active_idx'),
                    models.Index(fields=['pipeline', 'stage', 'is_active'], name='crm_stage_auto_pipe_stage_idx'),
                ],
            },
        ),
    ]
