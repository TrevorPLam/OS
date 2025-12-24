from django.db import migrations, models
import django.db.models.deletion


def copy_content_to_tables(apps, schema_editor):
    Document = apps.get_model('documents', 'Document')
    DocumentContent = apps.get_model('documents', 'DocumentContent')
    Version = apps.get_model('documents', 'Version')
    VersionContent = apps.get_model('documents', 'VersionContent')

    for document in Document.objects.all().iterator():
        if document.s3_key and document.s3_bucket:
            DocumentContent.objects.create(
                document=document,
                s3_key=document.s3_key,
                s3_bucket=document.s3_bucket,
            )

    for version in Version.objects.all().iterator():
        if version.s3_key and version.s3_bucket:
            VersionContent.objects.create(
                version=version,
                s3_key=version.s3_key,
                s3_bucket=version.s3_bucket,
            )


def copy_content_back(apps, schema_editor):
    Document = apps.get_model('documents', 'Document')
    DocumentContent = apps.get_model('documents', 'DocumentContent')
    Version = apps.get_model('documents', 'Version')
    VersionContent = apps.get_model('documents', 'VersionContent')

    content_by_document = {
        content.document_id: content
        for content in DocumentContent.objects.all().iterator()
    }
    for document in Document.objects.all().iterator():
        content = content_by_document.get(document.id)
        if content:
            document.s3_key = content.s3_key
            document.s3_bucket = content.s3_bucket
            document.save(update_fields=['s3_key', 's3_bucket'])

    content_by_version = {
        content.version_id: content
        for content in VersionContent.objects.all().iterator()
    }
    for version in Version.objects.all().iterator():
        content = content_by_version.get(version.id)
        if content:
            version.s3_key = content.s3_key
            version.s3_bucket = content.s3_bucket
            version.save(update_fields=['s3_key', 's3_bucket'])


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('s3_key', models.CharField(help_text='S3 object key (path in bucket)', max_length=500, unique=True)),
                ('s3_bucket', models.CharField(help_text='S3 bucket name', max_length=255)),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='content', to='documents.document')),
            ],
            options={
                'db_table': 'documents_document_content',
            },
        ),
        migrations.CreateModel(
            name='VersionContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('s3_key', models.CharField(help_text='S3 object key for this version', max_length=500, unique=True)),
                ('s3_bucket', models.CharField(max_length=255)),
                ('version', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='content', to='documents.version')),
            ],
            options={
                'db_table': 'documents_version_content',
            },
        ),
        migrations.RunPython(copy_content_to_tables, reverse_code=copy_content_back),
        migrations.RemoveIndex(
            model_name='document',
            name='documents__firm_s_4ca969_idx',
        ),
        migrations.RemoveField(
            model_name='document',
            name='s3_bucket',
        ),
        migrations.RemoveField(
            model_name='document',
            name='s3_key',
        ),
        migrations.RemoveField(
            model_name='version',
            name='s3_bucket',
        ),
        migrations.RemoveField(
            model_name='version',
            name='s3_key',
        ),
    ]
