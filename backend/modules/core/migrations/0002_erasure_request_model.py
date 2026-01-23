# Generated manually for DOC-07.2: Erasure request workflow

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErasureRequest',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending Review'),
                        ('evaluating', 'Evaluating Constraints'),
                        ('approved', 'Approved for Execution'),
                        ('rejected', 'Rejected'),
                        ('executing', 'Executing'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                    ],
                    db_index=True,
                    default='pending',
                    help_text='Current status of erasure request',
                    max_length=20,
                )),
                ('legal_basis', models.CharField(
                    choices=[
                        ('gdpr_article_17', 'GDPR Article 17 (Right to Erasure)'),
                        ('ccpa_deletion', 'CCPA Deletion Request'),
                        ('contractual_end', 'Contractual Retention Period Ended'),
                        ('consent_withdrawn', 'Consent Withdrawn'),
                        ('firm_offboarding', 'Firm Offboarding'),
                        ('other_legal', 'Other Legal Basis'),
                    ],
                    help_text='Legal basis for erasure/anonymization',
                    max_length=30,
                )),
                ('scope_type', models.CharField(
                    choices=[
                        ('contact', 'Contact (Individual)'),
                        ('account', 'Account (Company)'),
                        ('document', 'Specific Document'),
                        ('engagement', 'Engagement (and related data)'),
                    ],
                    help_text='Type of entity to erase/anonymize',
                    max_length=20,
                )),
                ('scope_entity_id', models.CharField(
                    db_index=True,
                    help_text='ID of entity to erase (e.g., Contact.id, Account.id)',
                    max_length=255,
                )),
                ('scope_entity_model', models.CharField(
                    help_text="Django model name (e.g., 'clients.Contact', 'clients.Client')",
                    max_length=100,
                )),
                ('requested_at', models.DateTimeField(
                    db_index=True,
                    default=django.utils.timezone.now,
                    help_text='When request was created',
                )),
                ('request_reason', models.TextField(
                    help_text='Detailed reason for erasure/anonymization request',
                )),
                ('legal_reference', models.CharField(
                    blank=True,
                    help_text='Reference to legal documentation (case number, request ID)',
                    max_length=500,
                )),
                ('evaluation_completed_at', models.DateTimeField(
                    blank=True,
                    help_text='When constraint evaluation was completed',
                    null=True,
                )),
                ('evaluation_result', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Evaluation results: constraints, blockers, plan',
                )),
                ('approved_at', models.DateTimeField(
                    blank=True,
                    help_text='When request was approved',
                    null=True,
                )),
                ('rejection_reason', models.TextField(
                    blank=True,
                    help_text='Reason for rejection (if status=rejected)',
                )),
                ('executed_at', models.DateTimeField(
                    blank=True,
                    help_text='When anonymization/erasure was executed',
                    null=True,
                )),
                ('execution_result', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Execution results: what was anonymized/erased',
                )),
                ('error_message', models.TextField(
                    blank=True,
                    help_text='Error message if execution failed',
                )),
                ('audit_events', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='List of audit event IDs related to this request',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firm', models.ForeignKey(
                    help_text='Firm this request belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='erasure_requests',
                    to='firm.firm',
                )),
                ('requested_by', models.ForeignKey(
                    help_text='User who created this request',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='erasure_requests_created',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    help_text='Master admin who approved execution',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='erasure_requests_approved',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'core_erasure_request',
                'ordering': ['-requested_at'],
                'permissions': [
                    ('can_approve_erasure', 'Can approve erasure requests (Master Admin only)'),
                ],
            },
        ),
        migrations.AddIndex(
            model_name='erasurerequest',
            index=models.Index(
                fields=['firm', 'status', '-requested_at'],
                name='core_erasur_firm_id_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='erasurerequest',
            index=models.Index(
                fields=['scope_entity_model', 'scope_entity_id'],
                name='core_erasur_scope_entity_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='erasurerequest',
            index=models.Index(
                fields=['requested_by', '-requested_at'],
                name='core_erasur_requested_by_idx',
            ),
        ),
    ]
