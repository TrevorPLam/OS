# Generated manually for Medium Feature 2.10 - Cash Application Matching

from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('firm', '0007_provisioninglog'),
        ('clients', '0003_initial'),
        ('finance', '0008_billing_ledger'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_number', models.CharField(help_text='Unique payment reference number', max_length=50)),
                ('payment_date', models.DateField(help_text='Date payment was received')),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    help_text='Total payment amount received',
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]
                )),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('payment_method', models.CharField(
                    choices=[
                        ('credit_card', 'Credit Card'),
                        ('bank_transfer', 'Bank Transfer'),
                        ('check', 'Check'),
                        ('cash', 'Cash'),
                        ('stripe', 'Stripe'),
                        ('other', 'Other'),
                    ],
                    default='stripe',
                    max_length=20
                )),
                ('reference_number', models.CharField(
                    blank=True,
                    help_text='Check number, transaction ID, or other reference',
                    max_length=255
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('cleared', 'Cleared'),
                        ('failed', 'Failed'),
                        ('refunded', 'Refunded'),
                    ],
                    default='pending',
                    max_length=20
                )),
                ('cleared_date', models.DateField(
                    blank=True,
                    help_text='Date when payment cleared/posted',
                    null=True
                )),
                ('amount_allocated', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('0.00'),
                    help_text='Total amount allocated to invoices',
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]
                )),
                ('amount_unallocated', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('0.00'),
                    help_text='Remaining unallocated amount (for overpayments or credits)',
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]
                )),
                ('notes', models.TextField(blank=True, help_text='Internal notes about this payment')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm', models.ForeignKey(
                    help_text='Firm (workspace) this payment belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payments',
                    to='firm.firm'
                )),
                ('client', models.ForeignKey(
                    help_text='The client who made this payment',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payments',
                    to='clients.client'
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='recorded_payments',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'finance_payments',
                'ordering': ['-payment_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentAllocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    help_text='Amount allocated from payment to invoice',
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]
                )),
                ('allocation_date', models.DateField(
                    help_text='Date when allocation was made'
                )),
                ('notes', models.TextField(
                    blank=True,
                    help_text='Notes about this allocation (e.g., partial payment reason)'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('firm', models.ForeignKey(
                    help_text='Firm (workspace) this allocation belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment_allocations',
                    to='firm.firm'
                )),
                ('payment', models.ForeignKey(
                    help_text='The payment being allocated',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='allocations',
                    to='finance.payment'
                )),
                ('invoice', models.ForeignKey(
                    help_text='The invoice receiving the allocation',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment_allocations',
                    to='finance.invoice'
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_allocations',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'finance_payment_allocations',
                'ordering': ['-allocation_date', '-created_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['firm', 'client', '-payment_date'], name='finance_fir_cli_pay_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['firm', 'status'], name='finance_fir_sta_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['firm', 'payment_number'], name='finance_fir_pay_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentallocation',
            index=models.Index(fields=['firm', 'payment'], name='finance_fir_pay_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentallocation',
            index=models.Index(fields=['firm', 'invoice'], name='finance_fir_inv_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentallocation',
            index=models.Index(fields=['allocation_date'], name='finance_all_idx'),
        ),
        # Add unique constraints
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.UniqueConstraint(
                fields=['firm', 'payment_number'],
                name='finance_payment_firm_number_unique'
            ),
        ),
    ]
