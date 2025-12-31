# Generated manually for ASSESS-D4.4b: Fix company_name uniqueness scope
# Change company_name from globally unique to firm-scoped unique (via unique_together)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0007_add_performance_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='company_name',
            field=models.CharField(max_length=255),
        ),
    ]
