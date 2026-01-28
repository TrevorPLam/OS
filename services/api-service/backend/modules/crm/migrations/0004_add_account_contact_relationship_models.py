# Generated manually for Task 3.1: Account & Contact relationship graph

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_rename_pipeline_stage_to_stage'),
        ('firm', '0012_user_profiles'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create Account model
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Company/Organization name', max_length=255)),
                ('legal_name', models.CharField(blank=True, help_text='Legal entity name if different', max_length=255)),
                ('account_type', models.CharField(choices=[('prospect', 'Prospect'), ('customer', 'Customer'), ('partner', 'Partner'), ('vendor', 'Vendor'), ('competitor', 'Competitor'), ('other', 'Other')], default='prospect', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('archived', 'Archived')], default='active', max_length=20)),
                ('industry', models.CharField(blank=True, help_text='Industry sector', max_length=100)),
                ('website', models.URLField(blank=True)),
                ('employee_count', models.IntegerField(blank=True, help_text='Number of employees', null=True)),
                ('annual_revenue', models.DecimalField(blank=True, decimal_places=2, help_text='Annual revenue (if known)', max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('billing_address_line1', models.CharField(blank=True, max_length=255)),
                ('billing_address_line2', models.CharField(blank=True, max_length=255)),
                ('billing_city', models.CharField(blank=True, max_length=100)),
                ('billing_state', models.CharField(blank=True, max_length=100)),
                ('billing_postal_code', models.CharField(blank=True, max_length=20)),
                ('billing_country', models.CharField(blank=True, max_length=100)),
                ('shipping_address_line1', models.CharField(blank=True, max_length=255)),
                ('shipping_address_line2', models.CharField(blank=True, max_length=255)),
                ('shipping_city', models.CharField(blank=True, max_length=100)),
                ('shipping_state', models.CharField(blank=True, max_length=100)),
                ('shipping_postal_code', models.CharField(blank=True, max_length=20)),
                ('shipping_country', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True, help_text='Internal notes about this account')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(help_text='User who created this account', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_accounts', to=settings.AUTH_USER_MODEL)),
                ('firm', models.ForeignKey(help_text='Firm (workspace) this account belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='firm.firm')),
                ('owner', models.ForeignKey(blank=True, help_text='Primary account owner/manager', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_accounts', to=settings.AUTH_USER_MODEL)),
                ('parent_account', models.ForeignKey(blank=True, help_text='Parent account for subsidiary relationships', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_accounts', to='crm.account')),
            ],
            options={
                'db_table': 'crm_account',
                'ordering': ['name'],
            },
        ),
        
        # Add indexes for Account
        migrations.AddIndex(
            model_name='account',
            index=models.Index(fields=['firm', 'status'], name='crm_account_firm_status_idx'),
        ),
        migrations.AddIndex(
            model_name='account',
            index=models.Index(fields=['firm', 'account_type'], name='crm_account_firm_type_idx'),
        ),
        migrations.AddIndex(
            model_name='account',
            index=models.Index(fields=['firm', 'owner'], name='crm_account_firm_owner_idx'),
        ),
        migrations.AddIndex(
            model_name='account',
            index=models.Index(fields=['parent_account'], name='crm_account_parent_idx'),
        ),
        
        # Add unique constraint for Account
        migrations.AddConstraint(
            model_name='account',
            constraint=models.UniqueConstraint(fields=['firm', 'name'], name='crm_account_firm_name_unique'),
        ),
        
        # Create AccountContact model
        migrations.CreateModel(
            name='AccountContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(help_text="Contact's first name", max_length=100)),
                ('last_name', models.CharField(help_text="Contact's last name", max_length=100)),
                ('email', models.EmailField(help_text="Contact's email address", max_length=254)),
                ('phone', models.CharField(blank=True, help_text="Contact's phone number", max_length=50)),
                ('mobile_phone', models.CharField(blank=True, help_text="Contact's mobile phone number", max_length=50)),
                ('job_title', models.CharField(blank=True, help_text='Job title at the account', max_length=200)),
                ('department', models.CharField(blank=True, help_text='Department within the organization', max_length=100)),
                ('is_primary_contact', models.BooleanField(default=False, help_text='Whether this is the primary contact for the account')),
                ('is_decision_maker', models.BooleanField(default=False, help_text='Whether this contact is a decision maker')),
                ('preferred_contact_method', models.CharField(choices=[('email', 'Email'), ('phone', 'Phone'), ('sms', 'SMS')], default='email', help_text='Preferred method of contact', max_length=20)),
                ('opt_out_marketing', models.BooleanField(default=False, help_text='Opted out of marketing communications')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this contact is active')),
                ('notes', models.TextField(blank=True, help_text='Internal notes about this contact')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(help_text='Account this contact belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to='crm.account')),
                ('created_by', models.ForeignKey(help_text='User who created this contact', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_account_contacts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'crm_account_contact',
                'ordering': ['last_name', 'first_name'],
            },
        ),
        
        # Add indexes for AccountContact
        migrations.AddIndex(
            model_name='accountcontact',
            index=models.Index(fields=['account', 'is_active'], name='crm_acc_contact_acc_act_idx'),
        ),
        migrations.AddIndex(
            model_name='accountcontact',
            index=models.Index(fields=['account', 'is_primary_contact'], name='crm_acc_contact_acc_pri_idx'),
        ),
        migrations.AddIndex(
            model_name='accountcontact',
            index=models.Index(fields=['email'], name='crm_acc_contact_email_idx'),
        ),
        
        # Add unique constraint for AccountContact
        migrations.AddConstraint(
            model_name='accountcontact',
            constraint=models.UniqueConstraint(fields=['account', 'email'], name='crm_accountcontact_account_email_unique'),
        ),
        
        # Create AccountRelationship model
        migrations.CreateModel(
            name='AccountRelationship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relationship_type', models.CharField(choices=[('parent_subsidiary', 'Parent-Subsidiary'), ('partnership', 'Partnership'), ('vendor_client', 'Vendor-Client'), ('competitor', 'Competitor'), ('referral_source', 'Referral Source'), ('strategic_alliance', 'Strategic Alliance'), ('reseller', 'Reseller'), ('other', 'Other')], help_text='Type of relationship', max_length=30)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('ended', 'Ended')], default='active', max_length=20)),
                ('start_date', models.DateField(blank=True, help_text='When the relationship started', null=True)),
                ('end_date', models.DateField(blank=True, help_text='When the relationship ended', null=True)),
                ('notes', models.TextField(blank=True, help_text='Notes about this relationship')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(help_text='User who created this relationship', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_account_relationships', to=settings.AUTH_USER_MODEL)),
                ('from_account', models.ForeignKey(help_text='Source account in the relationship', on_delete=django.db.models.deletion.CASCADE, related_name='relationships_from', to='crm.account')),
                ('to_account', models.ForeignKey(help_text='Target account in the relationship', on_delete=django.db.models.deletion.CASCADE, related_name='relationships_to', to='crm.account')),
            ],
            options={
                'db_table': 'crm_account_relationship',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add indexes for AccountRelationship
        migrations.AddIndex(
            model_name='accountrelationship',
            index=models.Index(fields=['from_account', 'status'], name='crm_acc_rel_from_status_idx'),
        ),
        migrations.AddIndex(
            model_name='accountrelationship',
            index=models.Index(fields=['to_account', 'status'], name='crm_acc_rel_to_status_idx'),
        ),
        migrations.AddIndex(
            model_name='accountrelationship',
            index=models.Index(fields=['relationship_type'], name='crm_acc_rel_type_idx'),
        ),
        
        # Add unique constraint for AccountRelationship
        migrations.AddConstraint(
            model_name='accountrelationship',
            constraint=models.UniqueConstraint(fields=['from_account', 'to_account', 'relationship_type'], name='crm_accountrelationship_from_to_type_unique'),
        ),
    ]
