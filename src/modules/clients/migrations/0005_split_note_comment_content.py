from django.db import migrations, models
import django.db.models.deletion


def copy_note_comment_content(apps, schema_editor):
    ClientNote = apps.get_model('clients', 'ClientNote')
    ClientNoteContent = apps.get_model('clients', 'ClientNoteContent')
    ClientComment = apps.get_model('clients', 'ClientComment')
    ClientCommentContent = apps.get_model('clients', 'ClientCommentContent')

    for note in ClientNote.objects.all().iterator():
        ClientNoteContent.objects.create(note=note, body=note.note)

    for comment in ClientComment.objects.all().iterator():
        ClientCommentContent.objects.create(comment=comment, body=comment.comment)


def copy_note_comment_content_back(apps, schema_editor):
    ClientNote = apps.get_model('clients', 'ClientNote')
    ClientNoteContent = apps.get_model('clients', 'ClientNoteContent')
    ClientComment = apps.get_model('clients', 'ClientComment')
    ClientCommentContent = apps.get_model('clients', 'ClientCommentContent')

    note_content_by_note = {
        content.note_id: content
        for content in ClientNoteContent.objects.all().iterator()
    }
    for note in ClientNote.objects.all().iterator():
        content = note_content_by_note.get(note.id)
        if content:
            note.note = content.body
            note.save(update_fields=['note'])

    comment_content_by_comment = {
        content.comment_id: content
        for content in ClientCommentContent.objects.all().iterator()
    }
    for comment in ClientComment.objects.all().iterator():
        content = comment_content_by_comment.get(comment.id)
        if content:
            comment.comment = content.body
            comment.save(update_fields=['comment'])


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_split_message_content'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientNoteContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('note', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='content', to='clients.clientnote')),
            ],
            options={
                'db_table': 'clients_note_content',
            },
        ),
        migrations.CreateModel(
            name='ClientCommentContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('comment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='content', to='clients.clientcomment')),
            ],
            options={
                'db_table': 'clients_comment_content',
            },
        ),
        migrations.RunPython(copy_note_comment_content, reverse_code=copy_note_comment_content_back),
        migrations.RemoveField(
            model_name='clientnote',
            name='note',
        ),
        migrations.RemoveField(
            model_name='clientcomment',
            name='comment',
        ),
    ]
