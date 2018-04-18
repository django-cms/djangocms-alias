from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from cms.api import add_plugin
from cms.models import Placeholder
from cms.utils.i18n import force_language
from cms.utils.plugins import downcast_plugins

from djangocms_alias.constants import (
    DETAIL_ALIAS_URL_NAME,
    PUBLISH_ALIAS_URL_NAME,
)
from djangocms_alias.models import Alias, Category
from djangocms_alias.utils import alias_plugin_reverse

from .base import BaseAliasPluginTestCase


class AliasViewsTestCase(BaseAliasPluginTestCase):

    def test_create_alias_view_get_no_data(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.CREATE_ALIAS_ENDPOINT)
            self.assertEqual(response.status_code, 400)

    def test_create_alias_view_non_staff_denied_access(self):
        response = self.client.get(self.CREATE_ALIAS_ENDPOINT)
        self.assertEqual(response.status_code, 403)

    def test_create_alias_view_get_show_form_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].initial['plugin'].pk,
                self.plugin.pk,
            )

    def test_create_alias_view_get_show_form_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.CREATE_ALIAS_ENDPOINT, data={
                'placeholder': self.placeholder.pk,
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
            response = self.client.get(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
            })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                response.context['form'].fields['replace'].widget.is_hidden,
            )

    def test_create_alias_view_post_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        alias_plugins = alias.draft_content.get_plugins()

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
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'replace': True,
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        plugins = alias.draft_content.get_plugins()

        self.assertEqual(plugins.count(), 1)
        self.assertEqual(plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            plugins[0].get_bound_plugin().body,
            self.plugin.body,
        )

    def test_create_alias_view_name(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        self.assertEqual(alias.name, 'test alias')

    def test_create_alias_view_post_no_plugin_or_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'category': self.category.pk,
                'name': 'test alias',
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_valid())

    def test_create_alias_view_post_both_plugin_and_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
                'placeholder': self.placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_valid())

    def test_create_alias_view_post_empty_placeholder(self):
        placeholder = Placeholder(slot='empty')
        placeholder.save()

        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'placeholder': placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
            })
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.content.decode(),
                'Plugins are required to create an alias',
            )

    def test_create_alias_view_post_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'placeholder': self.placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
            })
            self.assertEqual(response.status_code, 200)

        # Source plugins are kept in original placeholder
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        plugin_in_placeholder = plugins[0].get_bound_plugin()
        self.assertEqual(self.plugin, plugin_in_placeholder)

        alias = Alias.objects.last()

        source_plugins = self.placeholder.get_plugins()
        alias_plugins = alias.draft_content.get_plugins()

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
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'placeholder': self.placeholder.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'replace': True,
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        alias_plugins = alias.draft_content.get_plugins()

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
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
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
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
                'replace': True,
            })
            self.assertEqual(response.status_code, 403)

    def test_detach_view_no_permission_to_add_plugins_from_alias(self):
        response = self.client.get(self.DETACH_ALIAS_PLUGIN_ENDPOINT)
        self.assertEqual(response.status_code, 403)

    def test_detach_view_get(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.DETACH_ALIAS_PLUGIN_ENDPOINT)
            self.assertEqual(response.status_code, 400)

    def test_detach_view_non_staff_denied_access(self):
        alias = self._create_alias([self.plugin])
        plugin = add_plugin(
            self.placeholder,
            self.alias_plugin_base.__class__,
            language='en',
            alias=alias,
        )
        user = self.get_staff_user_with_no_permissions()
        with self.login_user_context(user):
            response = self.client.post(
                self.DETACH_ALIAS_PLUGIN_ENDPOINT,
                data={
                    'plugin': plugin.pk,
                    'language': self.language,
                },
            )
        self.assertEqual(response.status_code, 403)

    def test_detach_view_invalid_form(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.DETACH_ALIAS_PLUGIN_ENDPOINT,
            )
            self.assertEqual(response.status_code, 400)

    def test_detach_view_non_alias_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.DETACH_ALIAS_PLUGIN_ENDPOINT,
                data={
                    'plugin': self.plugin.pk,
                    'language': self.language,
                },
            )
            self.assertEqual(response.status_code, 400)

    def test_detach_view(self):
        alias = self._create_alias([self.plugin])
        plugin = add_plugin(
            self.placeholder,
            self.alias_plugin_base.__class__,
            language='en',
            alias=alias,
        )
        alias.publish(self.language)
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.DETACH_ALIAS_PLUGIN_ENDPOINT,
                data={
                    'plugin': plugin.pk,
                    'language': self.language,
                },
            )
            self.assertEqual(response.status_code, 200)

        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 2)
        self.assertEqual(
            plugins[0].get_bound_plugin().body,
            plugins[1].get_bound_plugin().body,
        )

    def test_detach_view_draft(self):
        alias = self._create_alias([self.plugin])
        plugin = add_plugin(
            self.placeholder,
            self.alias_plugin_base.__class__,
            language='en',
            alias=alias,
        )
        alias.publish(self.language)
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.DETACH_ALIAS_PLUGIN_ENDPOINT,
                data={
                    'plugin': plugin.pk,
                    'language': self.language,
                    'use_draft': True,
                },
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
        alias1.publish(self.language)
        alias2 = self._create_alias(
            [plugin],
            name='Alias 2',
            category=category2,
        )
        alias2.publish(self.language)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.LIST_ALIASES_ENDPOINT(category1.pk),
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, category1.name)
        self.assertNotContains(response, category2.name)
        self.assertContains(response, alias1.name)
        self.assertContains(
            response,
            alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias1.pk])
        )
        self.assertNotContains(
            response,
            alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias2.pk])
        )
        self.assertNotContains(response, alias2.name)
        self.assertContains(response, 'This is basic content')

    def test_list_view_standard_user(self):
        category = Category.objects.create(
            name='Category 1',
        )

        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(self.LIST_ALIASES_ENDPOINT(category.pk))
        self.assertEqual(response.status_code, 403)

    def test_list_view_standard_staff_user(self):
        category = Category.objects.create(
            name='Category 1',
        )

        with self.login_user_context(
            self.get_staff_user_with_std_permissions(),
        ):
            response = self.client.get(self.LIST_ALIASES_ENDPOINT(category.pk))
        self.assertEqual(response.status_code, 200)

    def test_category_list_view(self):
        category1 = Category.objects.create(
            name='Category 1',
        )
        category2 = Category.objects.create(
            name='Category 2',
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(self.CATEGORY_LIST_ENDPOINT)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, category1.name)
        self.assertContains(response, category2.name)

    def test_category_list_view_standard_user(self):
        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(self.CATEGORY_LIST_ENDPOINT)
        self.assertEqual(response.status_code, 403)

    def test_category_list_view_standard_staff_user(self):
        with self.login_user_context(
            self.get_staff_user_with_std_permissions(),
        ):
            response = self.client.get(self.CATEGORY_LIST_ENDPOINT)
        self.assertEqual(response.status_code, 200)

    def test_detail_view(self):
        alias = self._create_alias([self.plugin])
        alias.publish(self.language)
        plugin2 = add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk]),
                data={'preview': True},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plugin.body)
        self.assertNotContains(response, plugin2.body)

    def test_detail_view_draft(self):
        alias = self._create_alias([self.plugin])
        alias.publish(self.language)
        plugin2 = add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk]),
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plugin.body)
        self.assertContains(response, plugin2.body)

    def test_detail_view_standard_user(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(
                alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk]),
            )
        self.assertEqual(response.status_code, 403)

    def test_detail_view_standard_staff_user(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(
            self.get_staff_user_with_std_permissions(),
        ):
            response = self.client.get(
                alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk]),
            )
        self.assertEqual(response.status_code, 200)

    def test_detail_view_multilanguage(self):
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
        # Create alias with only en plugin
        alias = self._create_alias([en_plugin, de_plugin, fr_plugin])

        with self.login_user_context(self.superuser):
            with force_language('de'):
                response = self.client.get(
                    alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk]),  # noqa: E501
                )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, de_plugin.body)
        self.assertNotContains(response, fr_plugin.body)
        self.assertNotContains(response, en_plugin.body)

        with self.login_user_context(self.superuser):
            with force_language('fr'):
                response = self.client.get(
                    alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk]),  # noqa: E501
                )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fr_plugin.body)
        self.assertNotContains(response, de_plugin.body)
        self.assertNotContains(response, en_plugin.body)

    def test_detail_view_only_one_language_created_user_can_see_different_langs(self):  # noqa: E501
        # alias with en plugin
        alias = self._create_alias([self.plugin])

        with self.login_user_context(self.superuser):
            with force_language('de'):
                response = self.client.get(
                    alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk]),  # noqa: E501
                )
        self.assertEqual(response.status_code, 200)

    def test_publish_view_no_permissions(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(
                alias_plugin_reverse(
                    PUBLISH_ALIAS_URL_NAME,
                    args=[alias.pk, self.language],
                ),
            )
        self.assertEqual(response.status_code, 403)

    def test_publish_view_get(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(self.superuser):
            response = self.client.get(
                alias_plugin_reverse(
                    PUBLISH_ALIAS_URL_NAME,
                    args=[alias.pk, self.language],
                ),
            )
        self.assertEqual(response.status_code, 400)

    def test_publish_view_alias_does_not_exist(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(self.superuser):
            response = self.client.post(
                alias_plugin_reverse(
                    PUBLISH_ALIAS_URL_NAME,
                    args=[alias.pk + 1000, self.language],
                ),
            )
        self.assertEqual(response.status_code, 404)

    def test_publish_view(self):
        alias = self._create_alias()
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        live_plugins = alias.live_content.get_plugins()
        self.assertEqual(live_plugins.count(), 0)
        with self.login_user_context(self.superuser):
            response = self.client.post(
                alias_plugin_reverse(
                    PUBLISH_ALIAS_URL_NAME,
                    args=[alias.pk, self.language],
                ),
            )
        self.assertEqual(response.status_code, 200)
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        self.assertEqual(live_plugins.count(), 2)
