# Generated manually for TIER 5.2 performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_invoice_period_and_dispute_model'),
    ]

    operations = [
        # Invoice performance indexes for common queries
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(
                fields=['firm', 'client', '-issue_date'],
                name='finance_inv_firm_client_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(
                fields=['firm', '-due_date'],
                name='finance_inv_due_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(
                fields=['engagement', '-issue_date'],
                name='finance_inv_engagement_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(
                fields=['client', 'status', '-issue_date'],
                name='finance_inv_client_status_idx'
            ),
        ),

        # CreditLedgerEntry performance indexes
        migrations.AddIndex(
            model_name='creditledgerentry',
            index=models.Index(
                fields=['firm', 'client', '-created_at'],
                name='finance_credit_firm_client_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='creditledgerentry',
            index=models.Index(
                fields=['firm', 'credit_type', '-created_at'],
                name='finance_credit_type_idx'
            ),
        ),

        # PaymentFailure performance indexes
        migrations.AddIndex(
            model_name='paymentfailure',
            index=models.Index(
                fields=['client', 'resolved', '-failed_at'],
                name='finance_failure_client_idx'
            ),
        ),

        # Bill performance indexes
        migrations.AddIndex(
            model_name='bill',
            index=models.Index(
                fields=['firm', '-due_date'],
                name='finance_bill_due_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='bill',
            index=models.Index(
                fields=['firm', 'status', '-issue_date'],
                name='finance_bill_status_idx'
            ),
        ),
    ]
