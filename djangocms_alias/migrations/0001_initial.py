# Generated by Django 2.1.1 on 2018-09-07 11:12

import cms.utils.i18n
import django.db.models.deletion
import parler.models
from django.conf import settings
from django.db import migrations, models

from djangocms_alias.models import TEMPLATE_DEFAULT, get_templates


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cms", "0034_remove_pagecontent_placeholders"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alias",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "position",
                    models.PositiveIntegerField(default=0, verbose_name="position"),
                ),
            ],
            options={
                "verbose_name": "alias",
                "verbose_name_plural": "aliases",
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="AliasContent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120, verbose_name="name")),
                (
                    "language",
                    models.CharField(
                        choices=settings.LANGUAGES,
                        default=cms.utils.i18n.get_current_language,
                        max_length=10,
                    ),
                ),
                (
                    "alias",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contents",
                        to="djangocms_alias.Alias",
                    ),
                ),
            ],
            options={
                "verbose_name": "alias content",
                "verbose_name_plural": "alias contents",
            },
        ),
        migrations.CreateModel(
            name="AliasPlugin",
            fields=[
                (
                    "cmsplugin_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name="djangocms_alias_aliasplugin",
                        serialize=False,
                        to="cms.CMSPlugin",
                    ),
                ),
                (
                    "template",
                    models.CharField(
                        choices=get_templates(),
                        default=TEMPLATE_DEFAULT,
                        max_length=255,
                        verbose_name="template",
                    ),
                ),
                (
                    "alias",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cms_plugins",
                        to="djangocms_alias.Alias",
                        verbose_name="alias",
                    ),
                ),
            ],
            options={
                "verbose_name": "alias plugin model",
                "verbose_name_plural": "alias plugin models",
            },
            bases=("cms.cmsplugin",),
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "verbose_name": "category",
                "verbose_name_plural": "categories",
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="CategoryTranslation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "language_code",
                    models.CharField(db_index=True, max_length=15, verbose_name="Language"),
                ),
                (
                    "name",
                    models.CharField(max_length=120, unique=True, verbose_name="name"),
                ),
                (
                    "master",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="djangocms_alias.Category",
                    ),
                ),
            ],
            options={
                "verbose_name": "category Translation",
                "db_table": "djangocms_alias_category_translation",
                "db_tablespace": "",
                "managed": True,
                "default_permissions": (),
            },
        ),
        migrations.AddField(
            model_name="alias",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aliases",
                to="djangocms_alias.Category",
                verbose_name="category",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="categorytranslation",
            unique_together={("language_code", "master")},
        ),
    ]
