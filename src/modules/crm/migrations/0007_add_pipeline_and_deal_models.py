# Generated manually for DEAL-1: Pipeline and Deal Management

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('firm', '0001_initial'),
        ('projects', '0001_initial'),
        ('crm', '0006_add_cpq_models'),
    ]

    operations = [
        # Create Pipeline model
        migrations.CreateModel(
            name='Pipeline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Pipeline name (e.g., 'Sales', 'Consulting', 'Enterprise')", max_length=255)),
                ('description', models.TextField(blank=True, help_text='Pipeline description and purpose')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this pipeline is currently active')),
                ('is_default', models.BooleanField(default=False, help_text='Whether this is the default pipeline for new deals')),
                ('display_order', models.IntegerField(default=0, help_text='Display order for sorting pipelines')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(help_text='User who created this pipeline', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_pipelines', to=settings.AUTH_USER_MODEL)),
                ('firm', models.ForeignKey(help_text='Firm (workspace) this pipeline belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='pipelines', to='firm.firm')),
            ],
            options={
                'db_table': 'crm_pipelines',
                'ordering': ['display_order', 'name'],
                'unique_together': {('firm', 'name')},
            },
        ),
        
        # Create PipelineStage model
        migrations.CreateModel(
            name='PipelineStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Stage name (e.g., 'Discovery', 'Proposal', 'Negotiation')", max_length=100)),
                ('description', models.TextField(blank=True, help_text='Stage description')),
                ('probability', models.IntegerField(default=0, help_text='Default win probability percentage (0-100) for deals in this stage', validators=[django.core.validators.MinValueValidator(0)])),
                ('is_active', models.BooleanField(default=True, help_text='Whether this stage is currently active')),
                ('is_closed_won', models.BooleanField(default=False, help_text='Mark as won stage')),
                ('is_closed_lost', models.BooleanField(default=False, help_text='Mark as lost stage')),
                ('display_order', models.IntegerField(default=0, help_text='Display order within the pipeline')),
                ('auto_tasks', models.JSONField(blank=True, default=list, help_text='Tasks to auto-create when deal enters this stage')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pipeline', models.ForeignKey(help_text='Pipeline this stage belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='stages', to='crm.pipeline')),
            ],
            options={
                'db_table': 'crm_pipeline_stages',
                'ordering': ['pipeline', 'display_order', 'name'],
                'unique_together': {('pipeline', 'name')},
            },
        ),
        
        # Create Deal model
        migrations.CreateModel(
            name='Deal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Deal name/title', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Deal description and notes')),
                ('value', models.DecimalField(decimal_places=2, help_text='Deal value/amount', max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('probability', models.IntegerField(default=50, help_text='Win probability percentage (0-100)', validators=[django.core.validators.MinValueValidator(0)])),
                ('weighted_value', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Auto-calculated: value * probability / 100', max_digits=12)),
                ('expected_close_date', models.DateField(help_text='Expected close date')),
                ('actual_close_date', models.DateField(blank=True, help_text='Actual close date when won/lost', null=True)),
                ('split_percentage', models.JSONField(blank=True, default=dict, help_text='Split percentages for multiple owners {user_id: percentage}')),
                ('source', models.CharField(blank=True, help_text="Lead source (e.g., 'Website', 'Referral', 'Cold Call')", max_length=100)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this deal is active')),
                ('is_won', models.BooleanField(default=False, help_text='Deal was won')),
                ('is_lost', models.BooleanField(default=False, help_text='Deal was lost')),
                ('lost_reason', models.CharField(blank=True, help_text='Reason for losing the deal', max_length=255)),
                ('last_activity_date', models.DateField(blank=True, help_text='Date of last activity on this deal', null=True)),
                ('is_stale', models.BooleanField(default=False, help_text='Deal has had no activity for extended period')),
                ('stale_days_threshold', models.IntegerField(default=30, help_text='Days without activity before marked stale')),
                ('converted_to_project', models.BooleanField(default=False, help_text='Deal converted to project')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags for categorizing deals')),
                ('account', models.ForeignKey(blank=True, help_text='Associated account/company', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deals', to='crm.account')),
                ('campaign', models.ForeignKey(blank=True, help_text='Marketing campaign that generated this deal', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deals', to='crm.campaign')),
                ('contact', models.ForeignKey(blank=True, help_text='Primary contact for this deal', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deals', to='crm.accountcontact')),
                ('created_by', models.ForeignKey(help_text='User who created this deal', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_deals', to=settings.AUTH_USER_MODEL)),
                ('firm', models.ForeignKey(help_text='Firm (workspace) this deal belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='deals', to='firm.firm')),
                ('owner', models.ForeignKey(help_text='Primary deal owner', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_deals', to=settings.AUTH_USER_MODEL)),
                ('pipeline', models.ForeignKey(help_text='Pipeline this deal belongs to', on_delete=django.db.models.deletion.PROTECT, related_name='deals', to='crm.pipeline')),
                ('project', models.ForeignKey(blank=True, help_text='Project created from this deal', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_deals', to='projects.project')),
                ('stage', models.ForeignKey(help_text='Current stage in the pipeline', on_delete=django.db.models.deletion.PROTECT, related_name='deals', to='crm.pipelinestage')),
                ('team_members', models.ManyToManyField(blank=True, help_text='Additional team members working on this deal', related_name='team_deals', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'crm_deals',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create DealTask model
        migrations.CreateModel(
            name='DealTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Task title', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Task description')),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('due_date', models.DateField(blank=True, help_text='Task due date', null=True)),
                ('completed_at', models.DateTimeField(blank=True, help_text='When task was completed', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, help_text='User assigned to this task', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deal_tasks', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(help_text='User who created this task', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_deal_tasks', to=settings.AUTH_USER_MODEL)),
                ('deal', models.ForeignKey(help_text='Deal this task belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='crm.deal')),
            ],
            options={
                'db_table': 'crm_deal_tasks',
                'ordering': ['due_date', '-priority', 'title'],
            },
        ),
        
        # Add indexes for Pipeline
        migrations.AddIndex(
            model_name='pipeline',
            index=models.Index(fields=['firm', 'is_active'], name='crm_pip_firm_active_idx'),
        ),
        migrations.AddIndex(
            model_name='pipeline',
            index=models.Index(fields=['firm', 'is_default'], name='crm_pip_firm_default_idx'),
        ),
        
        # Add indexes for PipelineStage
        migrations.AddIndex(
            model_name='pipelinestage',
            index=models.Index(fields=['pipeline', 'display_order'], name='crm_pip_stg_pip_ord_idx'),
        ),
        migrations.AddIndex(
            model_name='pipelinestage',
            index=models.Index(fields=['pipeline', 'is_active'], name='crm_pip_stg_pip_act_idx'),
        ),
        
        # Add indexes for Deal
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['firm', 'pipeline', 'stage'], name='crm_deal_firm_pip_stg_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['firm', 'owner'], name='crm_deal_firm_owner_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['firm', 'is_active'], name='crm_deal_firm_active_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['firm', 'expected_close_date'], name='crm_deal_firm_close_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['firm', 'is_stale'], name='crm_deal_firm_stale_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['account'], name='crm_deal_account_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['contact'], name='crm_deal_contact_idx'),
        ),
        
        # Add indexes for DealTask
        migrations.AddIndex(
            model_name='dealtask',
            index=models.Index(fields=['deal', 'status'], name='crm_deal_task_deal_status_idx'),
        ),
        migrations.AddIndex(
            model_name='dealtask',
            index=models.Index(fields=['assigned_to', 'status'], name='crm_deal_task_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='dealtask',
            index=models.Index(fields=['due_date'], name='crm_deal_task_due_idx'),
        ),
    ]
