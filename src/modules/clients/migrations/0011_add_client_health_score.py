# Generated migration for CRM-INT-2: Dynamic Client Health Score

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0010_add_contact_bulk_operations'),
        ('firm', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientHealthScoreConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('engagement_weight', models.IntegerField(
                    default=25,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Weight for engagement factor (0-100)'
                )),
                ('payment_weight', models.IntegerField(
                    default=30,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Weight for payment factor (0-100)'
                )),
                ('communication_weight', models.IntegerField(
                    default=20,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Weight for communication factor (0-100)'
                )),
                ('project_delivery_weight', models.IntegerField(
                    default=25,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Weight for project delivery factor (0-100)'
                )),
                ('alert_threshold', models.IntegerField(
                    default=20,
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(50)
                    ],
                    help_text='Alert when score drops by this many points'
                )),
                ('at_risk_threshold', models.IntegerField(
                    default=50,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Score below this is considered at-risk'
                )),
                ('lookback_days', models.IntegerField(
                    default=90,
                    validators=[
                        django.core.validators.MinValueValidator(30),
                        django.core.validators.MaxValueValidator(365)
                    ],
                    help_text='Days to look back for historical data'
                )),
                ('is_active', models.BooleanField(default=True, help_text='Whether this configuration is active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_health_score_configs',
                    to=settings.AUTH_USER_MODEL,
                    help_text='User who created this configuration'
                )),
                ('firm', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='health_score_configs',
                    to='firm.firm',
                    help_text='Firm this configuration belongs to'
                )),
            ],
            options={
                'db_table': 'clients_health_score_config',
                'ordering': ['-created_at'],
                'unique_together': {('firm', 'is_active')},
            },
        ),
        migrations.CreateModel(
            name='ClientHealthScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Overall health score (0-100)'
                )),
                ('engagement_score', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Engagement factor score (0-100)'
                )),
                ('payment_score', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Payment factor score (0-100)'
                )),
                ('communication_score', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Communication factor score (0-100)'
                )),
                ('project_delivery_score', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Project delivery factor score (0-100)'
                )),
                ('calculation_metadata', models.JSONField(
                    default=dict,
                    help_text='Detailed calculation breakdown for audit trail'
                )),
                ('previous_score', models.IntegerField(
                    blank=True,
                    null=True,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Previous health score for comparison'
                )),
                ('score_change', models.IntegerField(
                    default=0,
                    help_text='Change from previous score (negative = decline)'
                )),
                ('is_at_risk', models.BooleanField(default=False, help_text='True if score is below at-risk threshold')),
                ('triggered_alert', models.BooleanField(
                    default=False,
                    help_text='True if score drop triggered an alert'
                )),
                ('calculated_at', models.DateTimeField(
                    auto_now_add=True,
                    db_index=True,
                    help_text='When this score was calculated'
                )),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='health_scores',
                    to='clients.client',
                    help_text='Client this score belongs to'
                )),
                ('firm', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='client_health_scores',
                    to='firm.firm',
                    help_text='Firm this score belongs to'
                )),
            ],
            options={
                'db_table': 'clients_health_score',
                'ordering': ['-calculated_at'],
            },
        ),
        migrations.CreateModel(
            name='ClientHealthScoreAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending Review'),
                        ('acknowledged', 'Acknowledged'),
                        ('resolved', 'Resolved'),
                        ('dismissed', 'Dismissed')
                    ],
                    default='pending',
                    max_length=20,
                    help_text='Current status of this alert'
                )),
                ('score_drop', models.IntegerField(help_text='How many points the score dropped')),
                ('previous_score', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Score before the drop'
                )),
                ('current_score', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    help_text='Score after the drop'
                )),
                ('acknowledged_at', models.DateTimeField(
                    blank=True,
                    null=True,
                    help_text='When this alert was acknowledged'
                )),
                ('resolution_notes', models.TextField(
                    blank=True,
                    help_text='Notes about how this alert was resolved'
                )),
                ('resolved_at', models.DateTimeField(
                    blank=True,
                    null=True,
                    help_text='When this alert was resolved'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('acknowledged_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='acknowledged_health_alerts',
                    to=settings.AUTH_USER_MODEL,
                    help_text='User who acknowledged this alert'
                )),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='health_alerts',
                    to='clients.client',
                    help_text='Client this alert is for'
                )),
                ('firm', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='client_health_alerts',
                    to='firm.firm',
                    help_text='Firm this alert belongs to'
                )),
                ('health_score', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='alerts',
                    to='clients.clienthealthscore',
                    help_text='Health score that triggered this alert'
                )),
                ('resolved_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='resolved_health_alerts',
                    to=settings.AUTH_USER_MODEL,
                    help_text='User who resolved this alert'
                )),
            ],
            options={
                'db_table': 'clients_health_score_alert',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='clienthealthscoreconfig',
            index=models.Index(fields=['firm', 'is_active'], name='clients_hsc_fir_act_idx'),
        ),
        migrations.AddIndex(
            model_name='clienthealthscore',
            index=models.Index(fields=['firm', 'client', '-calculated_at'], name='clients_hs_fir_cli_cal_idx'),
        ),
        migrations.AddIndex(
            model_name='clienthealthscore',
            index=models.Index(fields=['firm', 'is_at_risk'], name='clients_hs_fir_risk_idx'),
        ),
        migrations.AddIndex(
            model_name='clienthealthscore',
            index=models.Index(fields=['firm', 'triggered_alert'], name='clients_hs_fir_alert_idx'),
        ),
        migrations.AddIndex(
            model_name='clienthealthscore',
            index=models.Index(fields=['client', '-calculated_at'], name='clients_hs_cli_cal_idx'),
        ),
        migrations.AddIndex(
            model_name='clienthealthscorealert',
            index=models.Index(fields=['firm', 'status', '-created_at'], name='clients_hsa_fir_sta_cre_idx'),
        ),
        migrations.AddIndex(
            model_name='clienthealthscorealert',
            index=models.Index(fields=['client', 'status'], name='clients_hsa_cli_sta_idx'),
        ),
    ]
