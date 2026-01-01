# Generated migration for CPQ (Configure-Price-Quote) system (Task 3.5)

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0005_intake_forms'),
        ('firm', '0012_user_profiles'),
        ('pricing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Unique product code/SKU', max_length=100)),
                ('name', models.CharField(help_text='Product name', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Product description')),
                ('product_type', models.CharField(
                    choices=[('service', 'Service'), ('product', 'Product'), ('subscription', 'Subscription'), ('bundle', 'Bundle')],
                    default='service',
                    max_length=20
                )),
                ('status', models.CharField(
                    choices=[('active', 'Active'), ('inactive', 'Inactive'), ('archived', 'Archived')],
                    default='active',
                    max_length=20
                )),
                ('base_price', models.DecimalField(
                    decimal_places=2,
                    help_text='Base price before configuration',
                    max_digits=12,
                    validators=[MinValueValidator(Decimal('0.00'))]
                )),
                ('currency', models.CharField(default='USD', help_text='Currency code (ISO 4217)', max_length=3)),
                ('is_configurable', models.BooleanField(default=False, help_text='Whether this product has configurable options')),
                ('configuration_schema', models.JSONField(blank=True, default=dict, help_text='JSON schema defining configuration rules and dependencies')),
                ('category', models.CharField(blank=True, help_text='Product category', max_length=100)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Product tags for filtering')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm', models.ForeignKey(
                    help_text='Firm (workspace) this product belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='cpq_products',
                    to='firm.firm'
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_products',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'crm_product',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProductOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Option code', max_length=100)),
                ('label', models.CharField(help_text='Display label', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Option description')),
                ('option_type', models.CharField(
                    choices=[
                        ('single_select', 'Single Select'),
                        ('multi_select', 'Multi Select'),
                        ('text', 'Text Input'),
                        ('number', 'Number Input'),
                        ('boolean', 'Boolean')
                    ],
                    default='single_select',
                    max_length=20
                )),
                ('required', models.BooleanField(default=False, help_text='Whether this option is required')),
                ('display_order', models.IntegerField(default=0, help_text='Display order in UI')),
                ('values', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Available values for select options: [{value, label, price_modifier}]'
                )),
                ('price_modifier', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('0.00'),
                    help_text='Fixed price modifier (added to base price)',
                    max_digits=12
                )),
                ('price_multiplier', models.DecimalField(
                    decimal_places=4,
                    default=Decimal('1.0000'),
                    help_text='Price multiplier (applied to base price)',
                    max_digits=6,
                    validators=[MinValueValidator(Decimal('0.0000'))]
                )),
                ('dependency_rules', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Rules defining when this option is available based on other options'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(
                    help_text='Product this option belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='options',
                    to='crm.product'
                )),
            ],
            options={
                'db_table': 'crm_product_option',
                'ordering': ['display_order', 'label'],
            },
        ),
        migrations.CreateModel(
            name='ProductConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('configuration_name', models.CharField(
                    blank=True,
                    help_text='Optional name for this configuration',
                    max_length=255
                )),
                ('selected_options', models.JSONField(
                    default=dict,
                    help_text='Selected options: {option_code: value}'
                )),
                ('base_price', models.DecimalField(
                    decimal_places=2,
                    help_text='Base price at time of configuration',
                    max_digits=12
                )),
                ('configuration_price', models.DecimalField(
                    decimal_places=2,
                    help_text='Total price after applying configuration',
                    max_digits=12
                )),
                ('price_breakdown', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Detailed price breakdown: {base, options, discounts, total}'
                )),
                ('discount_percentage', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('0.00'),
                    help_text='Discount percentage applied to configuration',
                    max_digits=5,
                    validators=[MinValueValidator(Decimal('0.00'))]
                )),
                ('discount_amount', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('0.00'),
                    help_text='Calculated discount amount',
                    max_digits=12
                )),
                ('status', models.CharField(
                    choices=[('draft', 'Draft'), ('validated', 'Validated'), ('quoted', 'Quoted')],
                    default='draft',
                    max_length=20
                )),
                ('validation_errors', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Validation errors if configuration is invalid'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(
                    help_text='Product being configured',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='configurations',
                    to='crm.product'
                )),
                ('quote', models.ForeignKey(
                    blank=True,
                    help_text='Quote created from this configuration',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='product_configurations',
                    to='pricing.quote'
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_configurations',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'crm_product_configuration',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['firm', 'status'], name='crm_prod_firm_status_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['firm', 'code'], name='crm_prod_firm_code_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['firm', 'product_type'], name='crm_prod_firm_type_idx'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=('firm', 'code'), name='crm_product_firm_code_uniq'),
        ),
        migrations.AddIndex(
            model_name='productoption',
            index=models.Index(fields=['product', 'display_order'], name='crm_prod_opt_prod_ord_idx'),
        ),
        migrations.AddIndex(
            model_name='productoption',
            index=models.Index(fields=['product', 'code'], name='crm_prod_opt_prod_code_idx'),
        ),
        migrations.AddConstraint(
            model_name='productoption',
            constraint=models.UniqueConstraint(fields=('product', 'code'), name='crm_product_option_prod_code_uniq'),
        ),
        migrations.AddIndex(
            model_name='productconfiguration',
            index=models.Index(fields=['product', '-created_at'], name='crm_prod_cfg_prod_cre_idx'),
        ),
        migrations.AddIndex(
            model_name='productconfiguration',
            index=models.Index(fields=['product', 'status'], name='crm_prod_cfg_prod_sta_idx'),
        ),
        migrations.AddIndex(
            model_name='productconfiguration',
            index=models.Index(fields=['quote'], name='crm_prod_cfg_quote_idx'),
        ),
    ]
