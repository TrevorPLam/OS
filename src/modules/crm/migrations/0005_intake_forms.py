# Generated migration for intake forms (Task 3.4)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modules.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0004_add_account_contact_relationship_models'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IntakeForm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Internal name for this form', max_length=200)),
                ('title', models.CharField(help_text='Form title shown to users', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Form description/instructions')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('inactive', 'Inactive'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('qualification_enabled', models.BooleanField(default=True, help_text='Enable automatic lead qualification based on responses')),
                ('qualification_threshold', models.IntegerField(default=50, help_text='Minimum score (0-100) to qualify as a prospect')),
                ('auto_create_lead', models.BooleanField(default=True, help_text='Automatically create Lead record from submission')),
                ('auto_create_prospect', models.BooleanField(default=False, help_text='Automatically create Prospect record if qualified')),
                ('notify_on_submission', models.BooleanField(default=True, help_text='Send notification when form is submitted')),
                ('notification_emails', models.TextField(blank=True, help_text='Comma-separated list of emails to notify (in addition to owner)')),
                ('thank_you_title', models.CharField(default='Thank You!', help_text='Title shown after submission', max_length=255)),
                ('thank_you_message', models.TextField(default="We've received your information and will be in touch soon.", help_text='Message shown after submission')),
                ('redirect_url', models.URLField(blank=True, help_text='Optional URL to redirect to after submission', validators=[modules.core.validators.validate_safe_url])),
                ('submission_count', models.IntegerField(default=0, help_text='Total number of submissions')),
                ('qualified_count', models.IntegerField(default=0, help_text='Number of qualified submissions')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(help_text='User who created this form', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_intake_forms', to=settings.AUTH_USER_MODEL)),
                ('default_owner', models.ForeignKey(blank=True, help_text='Default owner for leads created from this form', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_intake_forms', to=settings.AUTH_USER_MODEL)),
                ('firm', models.ForeignKey(help_text='Firm this form belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='intake_forms', to='firm.firm')),
            ],
            options={
                'verbose_name': 'Intake Form',
                'verbose_name_plural': 'Intake Forms',
                'db_table': 'crm_intake_forms',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['firm', 'status'], name='crm_intake_firm_status_idx'),
                    models.Index(fields=['firm', 'created_at'], name='crm_intake_firm_created_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='IntakeFormField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Field label shown to users', max_length=255)),
                ('field_type', models.CharField(choices=[('text', 'Short Text'), ('textarea', 'Long Text'), ('email', 'Email'), ('phone', 'Phone'), ('url', 'URL'), ('number', 'Number'), ('select', 'Single Select'), ('multiselect', 'Multi Select'), ('checkbox', 'Checkbox'), ('date', 'Date'), ('file', 'File Upload')], default='text', max_length=20)),
                ('placeholder', models.CharField(blank=True, help_text='Placeholder text', max_length=255)),
                ('help_text', models.TextField(blank=True, help_text='Help text shown below field')),
                ('required', models.BooleanField(default=False, help_text='Is this field required?')),
                ('order', models.IntegerField(default=0, help_text='Display order (lower numbers first)')),
                ('options', models.JSONField(blank=True, default=list, help_text='Options for select/multiselect fields (list of strings)')),
                ('scoring_enabled', models.BooleanField(default=False, help_text='Enable qualification scoring for this field')),
                ('scoring_rules', models.JSONField(blank=True, default=dict, help_text='Scoring rules: {value: points, ...}')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('form', models.ForeignKey(help_text='Form this field belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='crm.intakeform')),
            ],
            options={
                'verbose_name': 'Intake Form Field',
                'verbose_name_plural': 'Intake Form Fields',
                'db_table': 'crm_intake_form_fields',
                'ordering': ['form', 'order', 'id'],
                'indexes': [
                    models.Index(fields=['form', 'order'], name='crm_intake_field_order_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='IntakeFormSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('responses', models.JSONField(default=dict, help_text='Field responses: {field_id: value, ...}')),
                ('qualification_score', models.IntegerField(default=0, help_text='Calculated qualification score (0-100)')),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('qualified', 'Qualified'), ('disqualified', 'Disqualified'), ('converted', 'Converted to Lead/Prospect'), ('spam', 'Marked as Spam')], default='pending', max_length=20)),
                ('is_qualified', models.BooleanField(default=False, help_text='Whether submission meets qualification threshold')),
                ('submitter_email', models.EmailField(blank=True, help_text='Email address from submission', max_length=254)),
                ('submitter_name', models.CharField(blank=True, help_text='Name from submission', max_length=255)),
                ('submitter_phone', models.CharField(blank=True, help_text='Phone number from submission', max_length=50)),
                ('submitter_company', models.CharField(blank=True, help_text='Company name from submission', max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of submitter', null=True)),
                ('user_agent', models.TextField(blank=True, help_text='User agent string')),
                ('referrer', models.URLField(blank=True, help_text='Referring URL', validators=[modules.core.validators.validate_safe_url])),
                ('reviewed_at', models.DateTimeField(blank=True, help_text='When submission was reviewed', null=True)),
                ('review_notes', models.TextField(blank=True, help_text='Internal notes from review')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('form', models.ForeignKey(help_text='Form that was submitted', on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='crm.intakeform')),
                ('lead', models.ForeignKey(blank=True, help_text='Lead created from this submission (if applicable)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='intake_submissions', to='crm.lead')),
                ('prospect', models.ForeignKey(blank=True, help_text='Prospect created from this submission (if qualified)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='intake_submissions', to='crm.prospect')),
                ('reviewed_by', models.ForeignKey(blank=True, help_text='User who reviewed this submission', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_intake_submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Intake Form Submission',
                'verbose_name_plural': 'Intake Form Submissions',
                'db_table': 'crm_intake_form_submissions',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['form', 'status'], name='crm_intake_sub_status_idx'),
                    models.Index(fields=['form', 'created_at'], name='crm_intake_sub_created_idx'),
                    models.Index(fields=['form', 'is_qualified'], name='crm_intake_sub_qualified_idx'),
                    models.Index(fields=['submitter_email'], name='crm_intake_sub_email_idx'),
                ],
            },
        ),
    ]
