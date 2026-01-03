# Generated manually for CRM-INT-4: Consent Chain Tracking

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modules.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0010_add_contact_bulk_operations'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsentRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consent_type', models.CharField(choices=[
                    ('marketing', 'Marketing Communications'),
                    ('email', 'Email Communications'),
                    ('sms', 'SMS Communications'),
                    ('phone', 'Phone Communications'),
                    ('data_processing', 'Data Processing'),
                    ('data_sharing', 'Data Sharing with Third Parties'),
                    ('analytics', 'Analytics & Tracking'),
                    ('profiling', 'Profiling & Automated Decision Making'),
                    ('terms_of_service', 'Terms of Service'),
                    ('privacy_policy', 'Privacy Policy'),
                ], help_text='Type of consent being tracked', max_length=50)),
                ('action', models.CharField(choices=[
                    ('granted', 'Consent Granted'),
                    ('revoked', 'Consent Revoked'),
                    ('updated', 'Consent Updated'),
                ], help_text='Action taken (granted/revoked/updated)', max_length=20)),
                ('legal_basis', models.CharField(choices=[
                    ('consent', 'Consent (GDPR Art. 6.1.a)'),
                    ('contract', 'Contract Performance (GDPR Art. 6.1.b)'),
                    ('legal_obligation', 'Legal Obligation (GDPR Art. 6.1.c)'),
                    ('vital_interests', 'Vital Interests (GDPR Art. 6.1.d)'),
                    ('public_task', 'Public Task (GDPR Art. 6.1.e)'),
                    ('legitimate_interests', 'Legitimate Interests (GDPR Art. 6.1.f)'),
                ], default='consent', help_text='Legal basis for processing (GDPR Article 6)', max_length=50)),
                ('data_categories', models.JSONField(default=list, help_text='List of data categories this consent applies to')),
                ('consent_text', models.TextField(blank=True, help_text='The exact consent text shown to the user')),
                ('consent_version', models.CharField(blank=True, help_text="Version of the consent text (e.g., 'v1.2', '2024-01-01')", max_length=50)),
                ('source', models.CharField(help_text="Source of consent (e.g., 'signup_form', 'email_campaign', 'portal_settings')", max_length=100)),
                ('source_url', models.URLField(blank=True, help_text='URL where consent was captured (if applicable)', validators=[modules.core.validators.validate_safe_url])),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When this consent action occurred (immutable)')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address from which consent was given/revoked', null=True)),
                ('user_agent', models.TextField(blank=True, help_text='User agent string from the browser/client')),
                ('previous_record_hash', models.CharField(blank=True, help_text='SHA-256 hash of the previous consent record for this contact+type (chain verification)', max_length=64)),
                ('record_hash', models.CharField(db_index=True, help_text='SHA-256 hash of this record for chain verification (computed on save)', max_length=64)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata (e.g., campaign_id, form_id, referrer)')),
                ('notes', models.TextField(blank=True, help_text='Internal notes about this consent record')),
                ('actor', models.ForeignKey(blank=True, help_text='User who created this record (if action was performed by staff)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consent_records_created', to=settings.AUTH_USER_MODEL)),
                ('contact', models.ForeignKey(help_text='Contact this consent record belongs to', on_delete=django.db.models.deletion.PROTECT, related_name='consent_records', to='clients.contact')),
            ],
            options={
                'db_table': 'clients_consent_record',
                'ordering': ['-timestamp'],
                'permissions': [
                    ('view_consent_chain', 'Can view consent chain verification'),
                    ('export_consent_proof', 'Can export consent proof'),
                ],
            },
        ),
        migrations.AddIndex(
            model_name='consentrecord',
            index=models.Index(fields=['contact', 'consent_type', '-timestamp'], name='consent_contact_type_idx'),
        ),
        migrations.AddIndex(
            model_name='consentrecord',
            index=models.Index(fields=['contact', '-timestamp'], name='consent_contact_time_idx'),
        ),
        migrations.AddIndex(
            model_name='consentrecord',
            index=models.Index(fields=['consent_type', '-timestamp'], name='consent_type_time_idx'),
        ),
        migrations.AddIndex(
            model_name='consentrecord',
            index=models.Index(fields=['action', '-timestamp'], name='consent_action_time_idx'),
        ),
        migrations.AddIndex(
            model_name='consentrecord',
            index=models.Index(fields=['record_hash'], name='consent_hash_idx'),
        ),
    ]
