from cms.api import add_plugin
from cms.models import Placeholder
from cms.utils.plugins import downcast_plugins

from djangocms_alias.models import Alias

from .base import BaseAlias2PluginTestCase


class Alias2ViewsTestCase(BaseAlias2PluginTestCase):

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

    def test_create_alias_view_post_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_ALIAS_ENDPOINT, data={
                'plugin': self.plugin.pk,
                'category': self.category.pk,
                'name': 'test alias',
            })
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        alias_plugins = alias.placeholder.get_plugins()

        # Source plugin is kept in original placeholder
        self.assertIn(
            self.plugin,
            downcast_plugins(self.placeholder.get_plugins()),
        )

        self.assertEqual(alias_plugins.count(), 1)
        self.assertEqual(alias_plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            alias_plugins[0].get_plugin_instance()[0].body,
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
        plugins = alias.placeholder.get_plugins()

        self.assertEqual(plugins.count(), 1)
        self.assertEqual(plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            plugins[0].get_plugin_instance()[0].body,
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
        plugin_in_placeholder = plugins[0].get_plugin_instance()[0]
        self.assertEqual(self.plugin, plugin_in_placeholder)

        alias = Alias.objects.last()

        source_plugins = self.placeholder.get_plugins()
        alias_plugins = alias.placeholder.get_plugins()

        self.assertEqual(alias_plugins.count(), source_plugins.count())
        for source, target in zip(source_plugins, alias_plugins):
            self.assertEqual(source.plugin_type, target.plugin_type)
            self.assertEqual(
                source.get_plugin_instance()[0].body,
                target.get_plugin_instance()[0].body,
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
        alias_plugins = alias.placeholder.get_plugins()

        self.assertEqual(alias_plugins.count(), 2)
        self.assertEqual(alias_plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            alias_plugins[0].get_plugin_instance()[0].body,
            self.plugin.body,
        )

        placeholder_plugins = self.placeholder.get_plugins()
        self.assertEqual(placeholder_plugins.count(), 1)

        self.assertEqual(
            placeholder_plugins[0].get_plugin_instance()[0].alias,
            alias,
        )

    def test_detach_view_non_staff_denied_access(self):
        response = self.client.get(self.DETACH_ALIAS_PLUGIN_ENDPOINT)
        self.assertEqual(response.status_code, 403)

    def test_detach_view_get(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.DETACH_ALIAS_PLUGIN_ENDPOINT)
            self.assertEqual(response.status_code, 400)

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
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.DETACH_ALIAS_PLUGIN_ENDPOINT,
                data={
                    'plugin': plugin.pk,
                },
            )
            self.assertEqual(response.status_code, 200)

        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 2)
        self.assertEqual(
            plugins[0].get_plugin_instance()[0].body,
            plugins[1].get_plugin_instance()[0].body,
        )
