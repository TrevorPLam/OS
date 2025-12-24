from django.db import migrations, models
import django.db.models.deletion


def copy_message_content(apps, schema_editor):
    ClientMessage = apps.get_model('clients', 'ClientMessage')
    ClientMessageContent = apps.get_model('clients', 'ClientMessageContent')

    for message in ClientMessage.objects.all().iterator():
        ClientMessageContent.objects.create(
            message=message,
            content=message.content,
            attachment_url=message.attachment_url,
            attachment_filename=message.attachment_filename,
            attachment_size_bytes=message.attachment_size_bytes,
        )


def copy_message_content_back(apps, schema_editor):
    ClientMessage = apps.get_model('clients', 'ClientMessage')
    ClientMessageContent = apps.get_model('clients', 'ClientMessageContent')

    content_by_message = {
        content.message_id: content
        for content in ClientMessageContent.objects.all().iterator()
    }
    for message in ClientMessage.objects.all().iterator():
        content = content_by_message.get(message.id)
        if content:
            message.content = content.content
            message.attachment_url = content.attachment_url
            message.attachment_filename = content.attachment_filename
            message.attachment_size_bytes = content.attachment_size_bytes
            message.save(
                update_fields=[
                    'content',
                    'attachment_url',
                    'attachment_filename',
                    'attachment_size_bytes',
                ]
            )


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientMessageContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='Message text content')),
                ('attachment_url', models.URLField(blank=True, help_text='S3 URL for file attachment (if message_type=file)')),
                ('attachment_filename', models.CharField(blank=True, help_text='Original filename of attachment', max_length=255)),
                ('attachment_size_bytes', models.BigIntegerField(blank=True, help_text='File size in bytes', null=True)),
                ('message', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='content', to='clients.clientmessage')),
            ],
            options={
                'db_table': 'clients_message_content',
            },
        ),
        migrations.RunPython(copy_message_content, reverse_code=copy_message_content_back),
        migrations.RemoveField(
            model_name='clientmessage',
            name='attachment_filename',
        ),
        migrations.RemoveField(
            model_name='clientmessage',
            name='attachment_size_bytes',
        ),
        migrations.RemoveField(
            model_name='clientmessage',
            name='attachment_url',
        ),
        migrations.RemoveField(
            model_name='clientmessage',
            name='content',
        ),
    ]
