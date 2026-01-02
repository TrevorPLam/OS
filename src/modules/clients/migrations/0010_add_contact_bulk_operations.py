# Generated manually for contact bulk operations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('firm', '0001_initial'),
        ('clients', '0009_add_contact_lifecycle_states'),
    ]

    operations = [
        # Create ContactImport model
        migrations.CreateModel(
            name='ContactImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('processing', 'Processing'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                        ('partially_completed', 'Partially Completed'),
                    ],
                    default='pending',
                    help_text='Current status of the import',
                    max_length=30,
                )),
                ('filename', models.CharField(help_text='Original filename of the imported file', max_length=255)),
                ('file_path', models.CharField(blank=True, help_text='Storage path of the uploaded file', max_length=500)),
                ('total_rows', models.IntegerField(default=0, help_text='Total number of rows in the import file')),
                ('successful_imports', models.IntegerField(default=0, help_text='Number of contacts successfully imported')),
                ('failed_imports', models.IntegerField(default=0, help_text='Number of contacts that failed to import')),
                ('skipped_rows', models.IntegerField(default=0, help_text='Number of rows skipped (headers, duplicates, etc.)')),
                ('duplicates_found', models.IntegerField(default=0, help_text='Number of duplicate contacts detected')),
                ('field_mapping', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Field mapping configuration from CSV columns to Contact model fields',
                )),
                ('duplicate_strategy', models.CharField(
                    choices=[
                        ('skip', 'Skip Duplicates'),
                        ('update', 'Update Existing'),
                        ('create_new', 'Create New'),
                    ],
                    default='skip',
                    help_text='How to handle duplicate contacts',
                    max_length=20,
                )),
                ('error_message', models.TextField(blank=True, help_text='General error message if import failed')),
                ('error_details', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Detailed error information per row',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(
                    blank=True,
                    help_text='When the import was completed',
                    null=True,
                )),
                ('firm', models.ForeignKey(
                    help_text='Firm this import belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='contact_imports',
                    to='firm.firm',
                )),
                ('created_by', models.ForeignKey(
                    help_text='User who initiated this import',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_contact_imports',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'clients_contact_import',
                'ordering': ['-created_at'],
            },
        ),
        # Create ContactBulkUpdate model
        migrations.CreateModel(
            name='ContactBulkUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('processing', 'Processing'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                    ],
                    default='pending',
                    help_text='Current status of the bulk update',
                    max_length=30,
                )),
                ('operation_type', models.CharField(
                    help_text="Type of bulk operation (e.g., 'update_status', 'assign_tags')",
                    max_length=50,
                )),
                ('update_data', models.JSONField(
                    default=dict,
                    help_text='Data to be updated (field: value pairs)',
                )),
                ('filter_criteria', models.JSONField(
                    default=dict,
                    help_text='Criteria used to filter contacts for update',
                )),
                ('total_contacts', models.IntegerField(default=0, help_text='Total number of contacts to be updated')),
                ('successful_updates', models.IntegerField(default=0, help_text='Number of contacts successfully updated')),
                ('failed_updates', models.IntegerField(default=0, help_text='Number of contacts that failed to update')),
                ('error_message', models.TextField(blank=True, help_text='General error message if update failed')),
                ('error_details', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Detailed error information per contact',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(
                    blank=True,
                    help_text='When the bulk update was completed',
                    null=True,
                )),
                ('firm', models.ForeignKey(
                    help_text='Firm this bulk update belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='contact_bulk_updates',
                    to='firm.firm',
                )),
                ('created_by', models.ForeignKey(
                    help_text='User who initiated this bulk update',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_contact_bulk_updates',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'clients_contact_bulk_update',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes for ContactImport
        migrations.AddIndex(
            model_name='contactimport',
            index=models.Index(
                fields=['firm', 'status'],
                name='clients_cimp_fir_sta_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='contactimport',
            index=models.Index(
                fields=['firm', '-created_at'],
                name='clients_cimp_fir_cre_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='contactimport',
            index=models.Index(
                fields=['created_by'],
                name='clients_cimp_cby_idx',
            ),
        ),
        # Add indexes for ContactBulkUpdate
        migrations.AddIndex(
            model_name='contactbulkupdate',
            index=models.Index(
                fields=['firm', 'status'],
                name='clients_cbup_fir_sta_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='contactbulkupdate',
            index=models.Index(
                fields=['firm', '-created_at'],
                name='clients_cbup_fir_cre_idx',
            ),
        ),
    ]
