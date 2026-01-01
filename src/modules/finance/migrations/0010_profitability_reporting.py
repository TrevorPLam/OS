# Generated migration for profitability reporting (Task 3.3)

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0009_payment_payment_allocation'),
        ('firm', '0012_user_profiles'),
        ('projects', '0004_add_resource_planning_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectProfitability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_revenue', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total revenue from invoices and payments', max_digits=12, validators=[MinValueValidator(Decimal('0.00'))])),
                ('recognized_revenue', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Revenue recognized based on completion percentage', max_digits=12, validators=[MinValueValidator(Decimal('0.00'))])),
                ('labor_cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total cost of labor (time entries × rates)', max_digits=12, validators=[MinValueValidator(Decimal('0.00'))])),
                ('expense_cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total project expenses (travel, materials, etc.)', max_digits=12, validators=[MinValueValidator(Decimal('0.00'))])),
                ('overhead_cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Allocated overhead costs (facility, admin, etc.)', max_digits=12, validators=[MinValueValidator(Decimal('0.00'))])),
                ('gross_margin', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Revenue minus direct costs (labor + expenses)', max_digits=12)),
                ('gross_margin_percentage', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Gross margin as percentage of revenue', max_digits=5)),
                ('net_margin', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Gross margin minus overhead costs', max_digits=12)),
                ('net_margin_percentage', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Net margin as percentage of revenue', max_digits=5)),
                ('estimated_completion_cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Estimated total cost to complete project', max_digits=12, validators=[MinValueValidator(Decimal('0.00'))])),
                ('estimated_final_margin', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Projected final margin at completion', max_digits=12)),
                ('hours_logged', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total hours logged on project', max_digits=10, validators=[MinValueValidator(Decimal('0.00'))])),
                ('billable_utilization', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Percentage of billable hours vs total hours', max_digits=5)),
                ('last_calculated_at', models.DateTimeField(auto_now=True, help_text='When profitability was last calculated')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('firm', models.ForeignKey(help_text='Firm this profitability record belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='project_profitability_records', to='firm.firm')),
                ('project', models.OneToOneField(help_text='Project being analyzed', on_delete=django.db.models.deletion.CASCADE, related_name='profitability', to='projects.project')),
            ],
            options={
                'verbose_name': 'Project Profitability',
                'verbose_name_plural': 'Project Profitability Records',
                'db_table': 'finance_project_profitability',
                'indexes': [
                    models.Index(fields=['firm', 'last_calculated_at'], name='finance_proj_prof_calc_idx'),
                    models.Index(fields=['firm', 'gross_margin_percentage'], name='finance_proj_prof_gm_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ServiceLineProfitability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Service line name (e.g., 'Management Consulting', 'IT Advisory')", max_length=200)),
                ('description', models.TextField(blank=True, help_text='Description of this service line')),
                ('period_start', models.DateField(help_text='Start of reporting period')),
                ('period_end', models.DateField(help_text='End of reporting period')),
                ('total_revenue', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total revenue across all projects in service line', max_digits=12, validators=[MinValueValidator(Decimal('0.00'))])),
                ('total_cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total costs (labor + expenses + overhead)', max_digits=12, validators=[MinValueValidator(Decimal('0.00'))])),
                ('gross_margin', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total revenue minus total costs', max_digits=12)),
                ('margin_percentage', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Margin as percentage of revenue', max_digits=5)),
                ('project_count', models.IntegerField(default=0, help_text='Number of projects in this service line')),
                ('active_project_count', models.IntegerField(default=0, help_text='Number of active projects')),
                ('last_calculated_at', models.DateTimeField(auto_now=True, help_text='When metrics were last calculated')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('firm', models.ForeignKey(help_text='Firm this service line belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='service_line_profitability', to='firm.firm')),
            ],
            options={
                'verbose_name': 'Service Line Profitability',
                'verbose_name_plural': 'Service Line Profitability Records',
                'db_table': 'finance_service_line_profitability',
                'indexes': [
                    models.Index(fields=['firm', 'period_start', 'period_end'], name='finance_svc_line_period_idx'),
                    models.Index(fields=['firm', 'margin_percentage'], name='finance_svc_line_margin_idx'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='servicelineprofitability',
            constraint=models.UniqueConstraint(fields=('firm', 'name', 'period_start', 'period_end'), name='finance_service_line_profitability_firm_name_period_start_period_end_uniq'),
        ),
    ]
