# Generated by Django 3.2.20 on 2023-07-26 13:43

import django.utils.translation
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("djangocms_alias", "0003_auto_20230725_1547"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aliascontent",
            name="language",
            field=models.CharField(default=django.utils.translation.get_language, max_length=10),
        ),
    ]
