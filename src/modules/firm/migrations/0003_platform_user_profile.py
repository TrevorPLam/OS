from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('firm', '0002_break_glass_session'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformUserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform_role', models.CharField(
                    choices=[
                        ('platform_operator', 'Platform Operator (Metadata Only)'),
                        ('break_glass_operator', 'Break-Glass Operator (Rare, Audited Access)'),
                    ],
                    default='platform_operator',
                    help_text='Platform access level: operator (metadata) or break-glass (rare content access)',
                    max_length=50
                )),
                ('is_platform_active', models.BooleanField(
                    default=True,
                    help_text='Whether platform access is currently active'
                )),
                ('can_activate_break_glass', models.BooleanField(
                    default=False,
                    help_text='Explicit flag: can this user activate break-glass sessions? (separate from role)'
                )),
                ('granted_at', models.DateTimeField(
                    auto_now_add=True,
                    help_text='When platform access was granted'
                )),
                ('revoked_at', models.DateTimeField(
                    blank=True,
                    help_text='When platform access was revoked (if applicable)',
                    null=True
                )),
                ('notes', models.TextField(
                    blank=True,
                    help_text='Internal notes about this platform user (e.g., reason for access)'
                )),
                ('granted_by', models.ForeignKey(
                    blank=True,
                    help_text='Who granted this platform access',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='granted_platform_profiles',
                    to=settings.AUTH_USER_MODEL
                )),
                ('revoked_by', models.ForeignKey(
                    blank=True,
                    help_text='Who revoked this platform access',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='revoked_platform_profiles',
                    to=settings.AUTH_USER_MODEL
                )),
                ('user', models.OneToOneField(
                    help_text='Link to Django User',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='platform_profile',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'firm_platform_user_profile',
                'ordering': ['-granted_at'],
            },
        ),
        migrations.AddIndex(
            model_name='platformuserprofile',
            index=models.Index(fields=['platform_role', 'is_platform_active'], name='firm_plat_role_active_idx'),
        ),
        migrations.AddIndex(
            model_name='platformuserprofile',
            index=models.Index(fields=['can_activate_break_glass'], name='firm_plat_bg_perm_idx'),
        ),
    ]
