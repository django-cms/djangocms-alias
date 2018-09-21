import re
from unittest import skipIf, skipUnless

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from cms.api import add_plugin
from cms.models import Placeholder
from cms.utils.i18n import force_language
from cms.utils.plugins import downcast_plugins
from cms.utils.urlutils import add_url_parameters, admin_reverse

from djangocms_alias.constants import (
    DELETE_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
    SELECT2_ALIAS_URL_NAME,
    SET_ALIAS_POSITION_URL_NAME,
    USAGE_ALIAS_URL_NAME,
)
from djangocms_alias.models import Alias, AliasContent, Category
from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class AliasViewsTestCase(BaseAliasPluginTestCase):

    def test_create_alias_view_get_no_data(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.get_create_alias_endpoint())
            self.assertEqual(response.status_code, 400)

    def test_create_alias_view_non_staff_denied_access(self):
        response = self.client.get(self.get_create_alias_endpoint())
        self.assertEqual(response.status_code, 403)

    def test_create_alias_view_get_show_form_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].initial['plugin'].pk,
                self.plugin.pk,
            )

    def test_create_alias_view_get_show_form_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.get_create_alias_endpoint(), data={
                'placeholder': self.placeholder.pk,
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].initial['placeholder'],
                self.placeholder,
            )

    def test_create_alias_view_show_form_replace_hidden(self):
        user = self.get_staff_user_with_std_permissions()
        user.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(
                    Alias,
                ),
                codename='add_alias',
            )
        )
        with self.login_user_context(user):
            response = self.client.get(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                response.context['form'].fields['replace'].widget.is_hidden,
            )

    def test_create_alias_view_post_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'language': self.language,
                'name': 'test alias',
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            self._publish(alias)
        alias_plugins = alias.get_placeholder(self.language).get_plugins()

        # Source plugin is kept in original placeholder
        self.assertIn(
            self.plugin,
            downcast_plugins(self.placeholder.get_plugins()),
        )

        self.assertEqual(alias_plugins.count(), 1)
        self.assertEqual(alias_plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            alias_plugins[0].get_bound_plugin().body,
            self.plugin.body,
        )

    def test_create_alias_view_post_plugin_replace(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
                'replace': True,
            })

        self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            self._publish(alias)
        plugins = alias.get_placeholder(self.language).get_plugins()

        self.assertEqual(plugins.count(), 1)
        self.assertEqual(plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            plugins[0].get_bound_plugin().body,
            self.plugin.body,
        )

    def test_create_alias_view_name(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            self._publish(alias)
        self.assertEqual(alias.name, 'test alias')

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
    def test_create_alias_view_name_draft_alias(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        # AliasContent not published
        self.assertEqual(alias.name, 'Alias {} (No content)'.format(alias.pk))

    @skipIf(is_versioning_enabled(), 'Test only relevant without versioning enabled')
    def test_create_alias_name_unique_per_category_and_language(self):
        self._create_alias(
            name='test alias',
            category=self.category,
        )
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Alias with this Name and Category already exists.',
        )
        self.assertEqual(
            AliasContent.objects.filter(
                name='test alias',
                language=self.language,
                alias__category=self.category,
            ).count(),
            1,
        )

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
    def test_create_alias_name_without_uniqness(self):
        alias1 = self._create_alias(
            name='test alias',
            category=self.category,
            published=True,
        )
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Alias with this Name and Category already exists.',
        )

        self._unpublish(alias1)

        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            'Alias with this Name and Category already exists.',
        )

        alias = Alias.objects.last()
        self._publish(alias)
        qs = AliasContent.objects.filter(
            name='test alias',
            language=self.language,
            alias__category=self.category,
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), alias.get_content(self.language))

    def test_create_alias_view_post_no_plugin_or_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_valid())

    def test_create_alias_view_post_both_plugin_and_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'placeholder': self.placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_valid())

    def test_create_alias_view_post_empty_placeholder(self):
        placeholder = Placeholder(slot='empty')
        placeholder.save()

        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'placeholder': placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.content.decode(),
                'Plugins are required to create an alias',
            )

    def test_create_alias_view_post_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'placeholder': self.placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)

        # Source plugins are kept in original placeholder
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        plugin_in_placeholder = plugins[0].get_bound_plugin()
        self.assertEqual(self.plugin, plugin_in_placeholder)

        alias = Alias.objects.first()
        if is_versioning_enabled():
            self._publish(alias)

        source_plugins = self.placeholder.get_plugins()
        alias_plugins = alias.get_placeholder(self.language).get_plugins()

        self.assertEqual(alias_plugins.count(), source_plugins.count())
        for source, target in zip(source_plugins, alias_plugins):
            self.assertEqual(source.plugin_type, target.plugin_type)
            self.assertEqual(
                source.get_bound_plugin().body,
                target.get_bound_plugin().body,
            )

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
    def test_create_alias_view_post_placeholder_from_draft_page(self):
        page1 = self._create_page('test alias page')
        placeholder = page1.get_placeholders(self.language).get(
            slot='content',
        )
        plugin = add_plugin(
            placeholder,
            'TextPlugin',
            language=self.language,
            body='test alias',
        )
        self._unpublish(page1)
        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'placeholder': placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })
            self.assertEqual(response.status_code, 200)

        # Source plugins are kept in original placeholder
        plugins = placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        plugin_in_placeholder = plugins[0].get_bound_plugin()
        self.assertEqual(plugin, plugin_in_placeholder)

        alias = Alias.objects.first()
        if is_versioning_enabled():
            self._publish(alias)

        source_plugins = placeholder.get_plugins()
        alias_plugins = alias.get_placeholder(self.language).get_plugins()

        self.assertEqual(alias_plugins.count(), source_plugins.count())
        for source, target in zip(source_plugins, alias_plugins):
            self.assertEqual(source.plugin_type, target.plugin_type)
            self.assertEqual(
                source.get_bound_plugin().body,
                target.get_bound_plugin().body,
            )

    def test_create_alias_view_post_placeholder_replace(self):
        add_plugin(
            self.placeholder,
            'TextPlugin',
            language='en',
            body='test 2',
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'placeholder': self.placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
                'replace': True,
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            self._publish(alias)
        alias_plugins = alias.get_placeholder(self.language).get_plugins()

        self.assertEqual(alias_plugins.count(), 2)
        self.assertEqual(alias_plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            alias_plugins[0].get_bound_plugin().body,
            self.plugin.body,
        )

        placeholder_plugins = self.placeholder.get_plugins()
        self.assertEqual(placeholder_plugins.count(), 1)

        self.assertEqual(
            placeholder_plugins[0].get_bound_plugin().alias,
            alias,
        )

    def test_create_alias_view_post_no_create_permission(self):
        with self.login_user_context(self.get_staff_user_with_no_permissions()):  # noqa: E501
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
            })
            self.assertEqual(response.status_code, 403)

    def test_create_alias_view_post_no_replace_permission(self):
        user = self.get_staff_user_with_std_permissions()
        user.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(
                    Alias,
                ),
                codename='add_alias',
            )
        )
        with self.login_user_context(user):
            response = self.client.post(self.get_create_alias_endpoint(), data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'language': self.language,
                'replace': True,
            })
            self.assertEqual(response.status_code, 403)

    def test_detach_view_no_permission_to_add_plugins_from_alias(self):
        response = self.client.post(
            self.get_detach_alias_plugin_endpoint(self.plugin.pk),
        )
        self.assertEqual(response.status_code, 403)

    def test_detach_view_get(self):
        alias = self._create_alias([self.plugin])
        plugin = add_plugin(
            self.placeholder,
            'Alias',
            language='en',
            alias=alias,
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_detach_alias_plugin_endpoint(plugin.pk),
            )
            self.assertEqual(response.status_code, 200)

    def test_detach_view_non_staff_denied_access(self):
        alias = self._create_alias([self.plugin])
        plugin = add_plugin(
            self.placeholder,
            'Alias',
            language='en',
            alias=alias,
        )
        user = self.get_staff_user_with_no_permissions()
        with self.login_user_context(user):
            response = self.client.post(
                self.get_detach_alias_plugin_endpoint(plugin.pk),
            )
        self.assertEqual(response.status_code, 403)

    def test_detach_view_non_alias_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_detach_alias_plugin_endpoint(self.plugin.pk),
            )
            self.assertEqual(response.status_code, 404)

    def test_detach_view(self):
        alias = self._create_alias([self.plugin])
        plugin = add_plugin(
            self.placeholder,
            'Alias',
            language='en',
            alias=alias,
        )
        add_plugin(
            alias.get_placeholder(self.language),
            'TextPlugin',
            language=self.language,
            body='test 2',
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_detach_alias_plugin_endpoint(plugin.pk),
            )
            self.assertEqual(response.status_code, 200)

        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 3)
        self.assertEqual(
            plugins[0].get_bound_plugin().body,
            plugins[1].get_bound_plugin().body,
        )

    def test_list_view(self):
        category1 = Category.objects.create(
            name='Category 1',
        )
        category2 = Category.objects.create(
            name='Category 2',
        )

        plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='This is basic content',
        )

        alias1 = self._create_alias(
            [plugin],
            name='Alias 1',
            category=category1,
        )
        alias2 = self._create_alias(
            [plugin],
            name='Alias 2',
            category=category2,
        )
        alias3 = self._create_alias(
            [plugin],
            name='Alias test 3',
            category=category1,
            published=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_list_aliases_endpoint(category1.pk),
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, category1.name)
        self.assertNotContains(response, category2.name)
        self.assertContains(response, 'Alias 1')
        self.assertNotContains(response, 'Alias 2')
        if is_versioning_enabled():
            self.assertContains(response, 'Alias {} (No content)'.format(alias3.pk))
        else:
            self.assertContains(response, 'Alias test 3')

        alias1_content = alias1.get_content(language=self.language)
        alias1_url = alias1_content.get_absolute_url()
        if is_versioning_enabled():
            alias1_url = admin_reverse(
                'djangocms_versioning_aliascontentversion_changelist'
            ) + '?grouper={}'.format(alias1.pk)

        self.assertContains(response, alias1_url)
        self.assertNotContains(response, alias2.get_absolute_url())
        self.assertContains(response, 'This is basic content')

        with self.login_user_context(self.superuser):
            with force_language('it'):
                response = self.client.get(
                    self.get_list_aliases_endpoint(category1.pk),
                )
        self.assertContains(response, 'Alias {} (No content)'.format(alias1.pk))
        self.assertContains(response, 'Alias {} (No content)'.format(alias3.pk))
        self.assertNotContains(response, 'Alias {} (No content)'.format(alias2.pk))
        self.assertNotContains(response, 'This is basic content')

    def test_list_view_standard_user(self):
        category = Category.objects.create(
            name='Category 1',
        )

        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(self.get_list_aliases_endpoint(category.pk))
        self.assertEqual(response.status_code, 403)

    def test_list_view_standard_staff_user(self):
        category = Category.objects.create(
            name='Category 1',
        )

        with self.login_user_context(
            self.get_staff_user_with_std_permissions(),
        ):
            response = self.client.get(self.get_list_aliases_endpoint(category.pk))
        self.assertEqual(response.status_code, 200)

    def test_category_list_view(self):
        Category.objects.all().delete()
        category1 = Category.objects.create()
        category2 = Category.objects.create()
        category1.translations.create(language_code='en', name='Category 1')
        category2.translations.create(language_code='en', name='Category 2')
        category1.translations.create(language_code='de', name='Kategorie 1')
        category2.translations.create(language_code='fr', name='Catégorie 2')
        category1.translations.create(language_code='it', name='Categoria 1')

        with self.login_user_context(self.superuser):
            with force_language('en'):
                en_response = self.client.get(self.get_category_list_endpoint())
            with force_language('de'):
                de_response = self.client.get(self.get_category_list_endpoint())
            with force_language('fr'):
                fr_response = self.client.get(self.get_category_list_endpoint())
            with force_language('it'):
                it_response = self.client.get(self.get_category_list_endpoint())

        self.assertContains(en_response, 'Category 1')
        self.assertContains(en_response, 'Category 2')
        self.assertNotContains(en_response, 'Kategorie 1')
        self.assertNotContains(en_response, 'Catégorie 2')
        self.assertNotContains(en_response, 'Categoria 1')

        self.assertContains(de_response, 'Kategorie 1')
        self.assertContains(de_response, 'Category 2')  # fallback
        self.assertNotContains(de_response, 'Category 1')
        self.assertNotContains(de_response, 'Catégorie 2')
        self.assertNotContains(de_response, 'Categoria 1')

        self.assertContains(fr_response, 'Category 1')  # fallback
        self.assertContains(fr_response, 'Catégorie 2')
        self.assertNotContains(fr_response, 'Category 2')
        self.assertNotContains(fr_response, 'Kategorie 1')
        self.assertNotContains(fr_response, 'Categoria 2')

        self.assertContains(it_response, 'Catégorie 2')  # fallback
        self.assertNotContains(it_response, 'Category 1')
        self.assertNotContains(it_response, 'Category 2')
        self.assertNotContains(it_response, 'Kategorie 1')
        self.assertNotContains(it_response, 'Categoria 2')

    def test_category_list_view_standard_user(self):
        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(self.get_category_list_endpoint())
        self.assertEqual(response.status_code, 403)

    def test_category_list_view_standard_staff_user(self):
        with self.login_user_context(
            self.get_staff_user_with_std_permissions(),
        ):
            response = self.client.get(self.get_category_list_endpoint())
        self.assertEqual(response.status_code, 200)

    def test_category_list_ordering(self):
        Category.objects.all().delete()
        category2 = Category.objects.create(name='B category')
        category1 = Category.objects.create(name='A category')

        with self.login_user_context(self.superuser):
            response = self.client.get(self.get_category_list_endpoint())

        self.assertEqual([category1, category2], response.context['categories'])

    def test_category_list_edit_button(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.get_category_list_endpoint())

        self.assertContains(
            response,
            '<a href="/en/admin/djangocms_alias/category/1/change/"'
        )

    def test_alias_content_preview_view(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(self.superuser):
            response = self.client.get(alias.get_content().get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, alias.name)
        self.assertContains(response, self.plugin.body)

    @skipIf(is_versioning_enabled(), 'Right now this feature wont work with versioning')
    def test_view_multilanguage(self):
        en_plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language='en',
            body='This is text in English',
        )
        de_plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language='de',
            body='Das ist Text auf Deutsch',
        )
        fr_plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language='fr',
            body='C\'est le texte en français',
        )
        alias = self._create_alias([en_plugin])
        alias_content_de = AliasContent.objects.create(
            alias=alias,
            name='test alias',
            language='de',
        )
        alias_content_de.populate(plugins=[de_plugin])
        alias_content_fr = AliasContent.objects.create(
            alias=alias,
            name='test alias',
            language='fr',
        )
        alias_content_fr.populate(plugins=[fr_plugin])

        with self.login_user_context(self.superuser):
            with force_language('de'):
                detail_response = self.client.get(alias.get_absolute_url())
                list_response = self.client.get(
                    admin_reverse(LIST_ALIASES_URL_NAME, args=[alias.category.pk]),
                )
        self.assertContains(detail_response, de_plugin.body)
        self.assertContains(list_response, de_plugin.body)
        self.assertNotContains(detail_response, fr_plugin.body)
        self.assertNotContains(list_response, fr_plugin.body)
        self.assertNotContains(detail_response, en_plugin.body)
        self.assertNotContains(list_response, en_plugin.body)

        with self.login_user_context(self.superuser):
            with force_language('fr'):
                detail_response = self.client.get(alias.get_absolute_url())
                list_response = self.client.get(
                    admin_reverse(LIST_ALIASES_URL_NAME, args=[alias.category.pk]),  # noqa: E501
                )

        self.assertContains(detail_response, fr_plugin.body)
        self.assertContains(list_response, fr_plugin.body)
        self.assertNotContains(detail_response, de_plugin.body)
        self.assertNotContains(list_response, de_plugin.body)
        self.assertNotContains(detail_response, en_plugin.body)
        self.assertNotContains(list_response, en_plugin.body)

    def test_set_alias_position_view(self):
        alias1 = Alias.objects.create(category=self.category)  # 0
        alias2 = Alias.objects.create(category=self.category)  # 1

        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias1.pk, 'position': 1},
            )

        ordered_aliases = list(
            alias1.category.aliases.order_by('position').values_list('pk', flat=True)  # noqa: E501
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ordered_aliases, [alias2.pk, alias1.pk])

        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias1.pk, 'position': 0},
            )

        ordered_aliases = list(
            alias1.category.aliases.order_by('position').values_list('pk', flat=True)  # noqa: E501
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ordered_aliases, [alias1.pk, alias2.pk])

        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias1.pk, 'position': 1},
            )

        ordered_aliases = list(
            alias1.category.aliases.order_by('position').values_list('pk', flat=True)  # noqa: E501
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ordered_aliases, [alias2.pk, alias1.pk])

    def test_set_alias_position_view_only_staff_users(self):
        alias = Alias.objects.create(category=self.category)
        Alias.objects.create(category=self.category)

        with self.login_user_context(self.get_standard_user()):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias.pk, 'position': 1},
            )
        self.assertEqual(response.status_code, 403)

        with self.login_user_context(self.get_staff_user_with_std_permissions()):  # noqa: E501
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias.pk, 'position': 1},
            )
        self.assertEqual(response.status_code, 200)

    def test_set_alias_position_view_bad_request_wrong_position(self):
        alias = Alias.objects.create(category=self.category)
        Alias.objects.create(category=self.category)
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias.pk},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            b'This field is required',
            response.content,
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias.pk, 'position': 2},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            b'Invalid position in category list, available positions are: [0, 1]',  # noqa: E501
            response.content,
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias.pk, 'position': -5},
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            b'Ensure this value is greater than or equal to 0.',
            response.content,
        )

    def test_set_alias_position_view_bad_request_the_same_position(self):
        alias = Alias.objects.create(category=self.category)
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': alias.pk, 'position': 0},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            b'Argument position have to be different than current alias position',  # noqa: E501
            response.content,
        )

    def test_set_alias_position_view_bad_request_wrong_alias_id(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'position': 0},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            b'This field is required.',
            response.content,
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': 'test', 'position': 0},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            b'Select a valid choice. That choice is not one of the available choices.',  # noqa: E501
            response.content,
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    SET_ALIAS_POSITION_URL_NAME,
                ),
                data={'alias': 5, 'position': 0},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            b'Select a valid choice. That choice is not one of the available choices.',  # noqa: E501
            response.content,
        )

    def test_select2_view_no_permission(self):
        response = self.client.get(
            admin_reverse(
                SELECT2_ALIAS_URL_NAME,
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_select2_view(self):
        alias1 = self._create_alias(name='test 2')
        alias2 = self._create_alias(name='foo', position=1)
        alias3 = self._create_alias(name='foo4', position=1, published=False)
        # This shouldnt show becuase it hasnt content in current language
        self._create_alias(name='foo2', language='fr', position=1)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
            )

        result = [alias1.pk, alias2.pk, alias3.pk]
        text_result = ['test 2', 'foo']
        if is_versioning_enabled():
            text_result.append('Alias 3 (No content)')
        else:
            text_result.append('foo4')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([a['id'] for a in response.json()['results']], result)
        self.assertEqual(
            [a['text'] for a in response.json()['results']],
            text_result,
        )

    def test_select2_view_order_by_category_and_position(self):
        category2 = Category.objects.create(name='foo')
        alias1 = self._create_alias(name='test 2')
        alias2 = self._create_alias(name='foo', position=1)
        alias3 = self._create_alias(name='bar', category=category2)
        alias4 = self._create_alias(name='baz', category=category2, position=1)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a['id'] for a in response.json()['results']],
            [alias3.pk, alias4.pk, alias1.pk, alias2.pk],
        )

    def test_select2_view_set_limit(self):
        self._create_alias(name='test 2')
        self._create_alias(name='foo', position=1)
        self._create_alias(name='three', position=2)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={'limit': 2},
            )

        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(content['more'])
        self.assertEqual(len(content['results']), 2)

    def test_select2_view_text_repr(self):
        alias1 = self._create_alias(name='test 2')
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['results'][0]['text'],
            alias1.name,
        )

    def test_select2_view_term(self):
        alias1 = self._create_alias(name='test 2')
        self._create_alias(name='foo', position=1)
        alias3 = self._create_alias(name='three', position=2)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={'term': 't'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a['id'] for a in response.json()['results']],
            [alias1.pk, alias3.pk],
        )

    def test_select2_view_category(self):
        category2 = Category.objects.create(name='test 2')
        alias1 = self._create_alias(name='test 2', category=category2)
        alias2 = self._create_alias(name='foo', category=category2, position=1)
        # This shouldnt show becuase it's in different Category
        self._create_alias(name='three')
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={'category': category2.pk},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a['id'] for a in response.json()['results']],
            [alias1.pk, alias2.pk],
        )

    def test_select2_view_category_and_term(self):
        category2 = Category.objects.create(name='test 2')
        alias1 = self._create_alias(name='test 2', category=category2)
        self._create_alias(name='foo', category=category2, position=1)
        self._create_alias(name='three')
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={'category': category2.pk, 'term': 't'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a['id'] for a in response.json()['results']],
            [alias1.pk],
        )

    def test_select2_view_pk(self):
        alias1 = self._create_alias(name='test 2')
        self._create_alias(name='foo', position=1)
        self._create_alias(name='three')
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={'pk': alias1.pk},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a['id'] for a in response.json()['results']],
            [alias1.pk],
        )

    def test_aliascontent_add_view(self):
        alias = Alias.objects.create(category=self.category)
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse('djangocms_alias_aliascontent_add'),
                data={
                    'language': 'de',
                    'name': 'alias test de 1',
                    'alias': alias.pk,
                },
            )

        self.assertEqual(response.status_code, 302)
        if is_versioning_enabled():
            self._publish(alias, 'de')
        self.assertEqual(alias.contents.count(), 1)
        alias_content = alias.contents.first()
        self.assertEqual(alias_content.language, 'de')
        self.assertEqual(alias_content.name, 'alias test de 1')

    def test_aliascontent_add_view_get(self):
        alias = Alias.objects.create(category=self.category)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                add_url_parameters(
                    admin_reverse(
                        'djangocms_alias_aliascontent_add',
                    ),
                    language='fr',
                    alias=alias.pk,
                )
            )

        self.assertContains(response, 'type="hidden" name="language" value="fr"')
        self.assertContains(response, 'type="hidden" name="alias" value="{}"'.format(alias.pk))

    def test_aliascontent_add_view_invalid_data(self):
        alias = Alias.objects.create(category=self.category)
        self._create_alias(
            name='test alias',
            category=self.category,
            language=self.language,
            published=True,
        )
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse('djangocms_alias_aliascontent_add'),
                data={
                    'language': self.language,
                    'name': 'test alias',
                    'alias': alias.pk,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Alias with this Name and Category already exists',
        )

    def test_aliascontent_add_view_valid_data(self):
        alias = Alias.objects.create(category=self.category)
        if is_versioning_enabled():
            self._create_alias(
                name='test alias',
                category=self.category,
                language=self.language,
                published=False,
            )
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse('djangocms_alias_aliascontent_add'),
                data={
                    'language': self.language,
                    'name': 'test alias',
                    'alias': alias.pk,
                },
            )

        self.assertEqual(response.status_code, 302)
        if is_versioning_enabled():
            self._publish(alias)
        alias_content = alias.contents.first()
        self.assertEqual(alias_content.name, 'test alias')

    def test_category_change_view(self):
        with self.login_user_context(self.superuser):
            self.client.post(
                add_url_parameters(
                    admin_reverse(
                        'djangocms_alias_category_change',
                        args=[self.category.pk],
                    ),
                    language='de',
                ),
                data={
                    'name': 'Alias Kategorie',
                },
            )

        self.assertEqual(self.category.name, 'test category')
        self.category.set_current_language('de')
        self.assertEqual(self.category.name, 'Alias Kategorie')

    def test_alias_usage_view(self):
        alias = self._create_alias()
        root_alias = self._create_alias()
        self.add_alias_plugin_to_page(self.page, alias)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    USAGE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )

        self.assertContains(response, '<td>Page</td>')
        self.assertNotContains(response, '<td>Alias</td>')

        add_plugin(
            root_alias.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=alias,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    USAGE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )

        self.assertContains(response, '<td>Page</td>')
        self.assertContains(response, '<td>Alias</td>')
        self.assertRegexpMatches(
            str(response.content),
            r'href="{}"[\w+]?>{}<\/a>'.format(
                re.escape(self.page.get_absolute_url(self.language)),
                str(self.page),
            ),
        )
        self.assertRegexpMatches(
            str(response.content),
            r'href="{}"[\w+]?>{}<\/a>'.format(
                re.escape(root_alias.get_absolute_url()),
                str(alias),
            ),
        )
        self.assertRegexpMatches(
            str(response.content),
            r'href="{}"[\w+]?>{}<\/a>'.format(
                re.escape(
                    add_url_parameters(
                        admin_reverse(
                            USAGE_ALIAS_URL_NAME,
                            args=[root_alias.pk],
                        ),
                        back=1,
                    )
                ),
                'View usage',
            ),
        )

    def test_delete_alias_view_get(self):
        alias = self._create_alias([self.plugin])
        add_plugin(
            self.placeholder,
            'Alias',
            language=self.language,
            alias=alias,
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertContains(
            response,
            'Are you sure you want to delete the alias "{}"?'.format(alias.name),  # noqa: E501
        )

    def test_delete_alias_view_get_using_objects(self):
        alias = self._create_alias([self.plugin])
        add_plugin(
            self.placeholder,
            'Alias',
            language=self.language,
            alias=alias,
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertContains(response, 'This alias is used by following objects:')
        test = r'<li>[\s\\n]*Page:[\s\\n]*<a href=\"\/en\/test\/\">test<\/a>[\s\\n]*<\/li>'
        self.assertRegexpMatches(str(response.content), test)

    def test_delete_alias_view_get_alias_not_used_on_any_page(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertContains(response, 'This alias wasn\'t used by any object.')

    def test_delete_alias_view_post(self):
        from djangocms_alias.views import JAVASCRIPT_SUCCESS_RESPONSE
        alias = self._create_alias([self.plugin])
        self.assertIn(alias, Alias.objects.all())
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
                data={'post': 'yes'},
            )
        self.assertContains(response, JAVASCRIPT_SUCCESS_RESPONSE)
        self.assertFalse(Alias.objects.filter(pk=alias.pk).exists())

    def test_delete_alias_view_user_with_no_perms(self):
        alias = self._create_alias([self.plugin])
        staff_user = self.get_staff_user_with_no_permissions()
        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertEqual(response.status_code, 403)

        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.post(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
                data={'post': 'yes'},
            )
        self.assertEqual(response.status_code, 403)

    def test_delete_alias_view_alias_not_being_used(self):
        alias = self._create_alias([self.plugin])
        staff_user = self.get_staff_user_with_alias_permissions()
        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertContains(response, 'Are you sure you want to delete')
        self.assertContains(response, 'type="submit"')
        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.post(  # noqa
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
                data={'post': 'yes'},
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Alias.objects.filter(pk=alias.pk).exists())

    def test_delete_alias_view_alias_being_used_on_pages(self):
        alias = self._create_alias([self.plugin])
        add_plugin(
            self.placeholder,
            'Alias',
            language=self.language,
            alias=alias,
        )
        # this user only can delete alias when alias not being used anywhere
        staff_user = self.get_staff_user_with_no_permissions()
        self.add_permission(staff_user, 'delete_alias')

        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertEqual(response.status_code, 403)

        with self.login_user_context(staff_user):
            response = self.client.post(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
                data={'post': 'yes'},
            )
        self.assertEqual(response.status_code, 403)

    def test_custom_template_alias_view(self):
        alias = self._create_alias()
        add_plugin(
            alias.get_placeholder(self.language),
            'TextPlugin',
            language=self.language,
            body='custom alias content',
        )
        add_plugin(
            self.placeholder,
            'Alias',
            language=self.language,
            alias=alias,
            template='custom_alias_template',
        )

        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, '<b>custom alias content</b>')
