# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-06 14:58
from __future__ import unicode_literals

import cms.models.fields
from django.db import migrations, models
import django.db.models.deletion
import djangocms_alias.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cms', '0018_pagenode'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='name')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='position')),
            ],
            options={
                'verbose_name': 'alias',
                'verbose_name_plural': 'aliases',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='AliasPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='djangocms_alias_aliaspluginmodel', serialize=False, to='cms.CMSPlugin')),
                ('alias', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cms_plugins', to='djangocms_alias.Alias', verbose_name='alias')),
            ],
            options={
                'verbose_name': 'alias plugin model',
                'verbose_name_plural': 'alias plugin models',
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='AliasPlaceholder',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('cms.placeholder',),
        ),
        migrations.AddField(
            model_name='alias',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='aliases', to='djangocms_alias.Category', verbose_name='category'),
        ),
        migrations.AddField(
            model_name='alias',
            name='placeholder',
            field=cms.models.fields.PlaceholderField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, slotname=djangocms_alias.models._get_alias_placeholder_slot, to='cms.Placeholder'),
        ),
    ]
