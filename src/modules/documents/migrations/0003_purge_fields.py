from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='s3_bucket',
            field=models.CharField(blank=True, help_text='S3 bucket name', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='s3_key',
            field=models.CharField(blank=True, help_text='S3 object key (path in bucket, unique per firm)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='is_purged',
            field=models.BooleanField(default=False, help_text='Whether this document content has been purged'),
        ),
        migrations.AddField(
            model_name='document',
            name='purged_at',
            field=models.DateTimeField(blank=True, help_text='When the document was purged', null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='purged_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who purged the document',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='purged_documents',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='document',
            name='purge_reason',
            field=models.TextField(blank=True, help_text='Reason for purge (required for legal/compliance)'),
        ),
        migrations.AlterField(
            model_name='version',
            name='s3_bucket',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='version',
            name='s3_key',
            field=models.CharField(blank=True, help_text='S3 object key for this version (unique per firm)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='version',
            name='is_purged',
            field=models.BooleanField(default=False, help_text='Whether this version content has been purged'),
        ),
        migrations.AddField(
            model_name='version',
            name='purged_at',
            field=models.DateTimeField(blank=True, help_text='When the version was purged', null=True),
        ),
        migrations.AddField(
            model_name='version',
            name='purged_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who purged the version',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='purged_document_versions',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='version',
            name='purge_reason',
            field=models.TextField(blank=True, help_text='Reason for purge (required for legal/compliance)'),
        ),
    ]
