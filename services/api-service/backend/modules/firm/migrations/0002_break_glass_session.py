from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BreakGlassSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(help_text='Required reason string for break-glass activation')),
                ('status', models.CharField(choices=[('active', 'Active'), ('expired', 'Expired'), ('revoked', 'Revoked')], default='active', max_length=20)),
                ('activated_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(help_text='Auto-expiration timestamp for break-glass')),
                ('revoked_at', models.DateTimeField(blank=True, help_text='When break-glass was revoked early (if applicable)', null=True)),
                ('revoked_reason', models.TextField(blank=True, help_text='Optional: why break-glass was revoked early')),
                ('reviewed_at', models.DateTimeField(blank=True, help_text='When break-glass usage was reviewed by platform ops', null=True)),
                ('firm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='break_glass_sessions', to='firm.firm')),
                ('impersonated_user', models.ForeignKey(blank=True, help_text='Optional: firm user being impersonated during break-glass', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='impersonated_by_break_glass_sessions', to=settings.AUTH_USER_MODEL)),
                ('operator', models.ForeignKey(help_text='Platform operator who activated break-glass', on_delete=django.db.models.deletion.PROTECT, related_name='break_glass_sessions', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, help_text='Reviewer for break-glass session audit', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_break_glass_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'firm_break_glass_session',
                'ordering': ['-activated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='breakglasssession',
            index=models.Index(fields=['firm', 'status'], name='firm_bg_firm_status_idx'),
        ),
        migrations.AddIndex(
            model_name='breakglasssession',
            index=models.Index(fields=['operator', 'status'], name='firm_bg_operator_status_idx'),
        ),
        migrations.AddIndex(
            model_name='breakglasssession',
            index=models.Index(fields=['expires_at'], name='firm_bg_expires_at_idx'),
        ),
    ]
