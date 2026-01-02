# Generated migration for granular document permissions (SEC-2)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_document_classification_document_deprecated_at_and_more'),
        ('firm', '0012_user_profiles'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, help_text='Role with this permission (blank = user-specific)', max_length=50)),
                ('resource_type', models.CharField(choices=[('folder', 'Folder'), ('document', 'Document')], help_text='Type of resource (folder or document)', max_length=20)),
                ('action', models.CharField(choices=[('create', 'Create files/subfolders'), ('read', 'Read/View content'), ('update', 'Update/Modify'), ('delete', 'Delete'), ('share', 'Share with others'), ('download', 'Download files')], help_text='Action being permitted or denied', max_length=20)),
                ('effect', models.CharField(choices=[('allow', 'Allow'), ('deny', 'Deny (overrides allow)')], default='allow', help_text='Allow or deny this action (deny wins)', max_length=10)),
                ('apply_to_children', models.BooleanField(default=True, help_text='Apply this permission to all child folders/documents')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reason', models.TextField(blank=True, help_text='Reason for granting/denying permission (audit trail)')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_document_permissions', to=settings.AUTH_USER_MODEL)),
                ('document', models.ForeignKey(blank=True, help_text='Document this permission applies to (null if folder-level)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='documents.document')),
                ('firm', models.ForeignKey(help_text='Firm this permission belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='document_permissions', to='firm.firm')),
                ('folder', models.ForeignKey(blank=True, help_text='Folder this permission applies to (null if document-level)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='documents.folder')),
                ('user', models.ForeignKey(blank=True, help_text='User with this permission (null = role-based)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='document_permissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'documents_permissions',
                'permissions': [('manage_document_permissions', 'Can manage document permissions')],
            },
        ),
        migrations.AddIndex(
            model_name='documentpermission',
            index=models.Index(fields=['firm', 'user', 'resource_type'], name='documents_p_firm_id_user_id_res_idx'),
        ),
        migrations.AddIndex(
            model_name='documentpermission',
            index=models.Index(fields=['firm', 'role', 'resource_type'], name='documents_p_firm_id_role_res_idx'),
        ),
        migrations.AddIndex(
            model_name='documentpermission',
            index=models.Index(fields=['folder', 'action'], name='documents_p_folder_id_act_idx'),
        ),
        migrations.AddIndex(
            model_name='documentpermission',
            index=models.Index(fields=['document', 'action'], name='documents_p_doc_id_act_idx'),
        ),
        migrations.AddConstraint(
            model_name='documentpermission',
            constraint=models.CheckConstraint(check=models.Q(('user__isnull', False), _connector='OR', _negated=True) | ~models.Q(('role', '')), name='user_or_role_required'),
        ),
        migrations.AddConstraint(
            model_name='documentpermission',
            constraint=models.CheckConstraint(check=models.Q(('folder__isnull', False), _connector='OR') | models.Q(('document__isnull', False)), name='folder_or_document_required'),
        ),
    ]
