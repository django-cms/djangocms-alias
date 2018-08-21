# Generated by Django 2.0.7 on 2018-07-30 10:32

import cms.models.fields
import cms.utils.i18n
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import djangocms_alias.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cms', '0020_old_tree_cleanup'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='position')),
            ],
            options={
                'verbose_name': 'alias',
                'verbose_name_plural': 'aliases',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='AliasContent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='name')),
                ('language', models.CharField(choices=settings.LANGUAGES, default=cms.utils.i18n.get_current_language, max_length=10)),
                ('alias', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='djangocms_alias.Alias')),
                ('placeholder', cms.models.fields.PlaceholderField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alias_contents', slotname=djangocms_alias.models._get_alias_placeholder_slot, to='cms.Placeholder')),
                ('template', models.CharField(choices=[('default', 'Default')], default='default', max_length=255, verbose_name='Template')),
            ],
            options={
                'verbose_name': 'alias content',
                'verbose_name_plural': 'alias contents',
            },
        ),
        migrations.CreateModel(
            name='AliasPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='djangocms_alias_aliasplugin', serialize=False, to='cms.CMSPlugin')),
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
        migrations.AddField(
            model_name='alias',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='aliases', to='djangocms_alias.Category', verbose_name='category'),
        ),
    ]
