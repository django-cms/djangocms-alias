from operator import attrgetter

from django.contrib.sites.models import Site
from django.test.utils import override_settings

from cms.api import add_plugin, create_page
from cms.utils.plugins import downcast_plugins

from djangocms_alias.compat import get_page_placeholders
from djangocms_alias.cms_plugins import Alias

from .base import BaseAliasPluginTestCase


class AliasPluginTestCase(BaseAliasPluginTestCase):

    def test_create_alias_from_plugin_list(self):
        plugins = self.placeholder.get_plugins()
        alias = self._create_alias(plugins)
        self.assertEqual(
            plugins[0].plugin_type,
            alias.get_placeholder(self.language).get_plugins()[0].plugin_type,
        )
        self.assertEqual(
            plugins[0].get_bound_plugin().body,
            alias.get_placeholder(self.language).get_plugins()[0].get_bound_plugin().body,
        )

    def test_replace_plugin_with_alias(self):
        alias = self._create_alias([self.plugin])
        alias_content = alias.get_content(self.language)
        alias_plugin = alias_content.populate(
            replaced_plugin=self.plugin,
        )
        plugins = self.placeholder.get_plugins()
        self.assertNotIn(
            self.plugin,
            plugins,
        )
        self.assertEqual(plugins[0].get_bound_plugin(), alias_plugin)
        self.assertEqual(alias_content.placeholder.get_plugins()[0].get_bound_plugin().body, 'test')  # noqa: E501

    def test_replace_plugin_with_alias_correct_position(self):
        second_plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        alias = self._create_alias()
        alias_plugin = alias.get_content(self.language).populate(replaced_plugin=second_plugin)
        plugins = self.placeholder.get_plugins()
        self.assertNotIn(
            self.plugin,
            plugins,
        )
        self.assertEqual(plugins[1].get_bound_plugin(), alias_plugin)

        ordered_plugins = sorted(
            downcast_plugins(plugins),
            key=attrgetter('position'),
        )

        self.assertEqual(
            [plugin.plugin_type for plugin in ordered_plugins],
            ['TextPlugin', 'Alias', 'TextPlugin'],
        )

    def test_replace_placeholder_content_with_alias(self):
        add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        alias = self._create_alias()
        alias_content = alias.get_content(self.language)
        alias_content.populate(replaced_placeholder=self.placeholder)
        plugins = self.placeholder.get_plugins()

        self.assertEqual(plugins.count(), 1)
        self.assertEqual(alias_content.placeholder.get_plugins().count(), 2)
        self.assertEqual(
            alias_content.placeholder.get_plugins()[1].get_bound_plugin().body,
            'test 2',
        )

    def test_detach_alias(self):
        alias = self._create_alias()
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        alias_plugin = add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )

        self.assertEqual(plugins.count(), 2)
        Alias.detach_alias_plugin(alias_plugin, self.language)
        self.assertEqual(plugins.count(), 4)

    def test_detach_alias_correct_position(self):
        alias = self._create_alias([])
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        alias_plugin = add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        self.assertEqual(plugins.count(), 3)
        Alias.detach_alias_plugin(alias_plugin, self.language)
        self.assertEqual(plugins.count(), 4)

        ordered_plugins = sorted(
            downcast_plugins(plugins),
            key=attrgetter('position'),
        )
        self.assertEqual(
            [str(plugin) for plugin in ordered_plugins],
            ['test', 'test 1', 'test 2', 'test 3'],
        )

    def test_alias_plugin_edit_button_redirecting_to_page_with_structure_mode_turned_on(self):  # noqa: E501
        alias = self._create_alias([])
        alias_plugin = add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        request = self.get_request('/')

        alias_plugin_menu_items = Alias.get_extra_plugin_menu_items(
            request,
            alias_plugin,
        )

        edit_menu_item = next(filter(
            lambda item: item.name == 'Edit Alias',
            alias_plugin_menu_items,
        ))

        self.assertIn('?structure', edit_menu_item.url)

    def test_alias_multisite_support(self):
        site1 = Site.objects.create(domain='site1.com', name='1')
        site2 = Site.objects.create(domain='site2.com', name='2')
        alias = self._create_alias()
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test alias multisite',
        )

        site1_page = create_page(
            title='Site1',
            template='page.html',
            language=self.language,
            published=True,
            in_navigation=True,
            site=site1,
        )
        site2_page = create_page(
            title='Site2',
            template='page.html',
            language=self.language,
            published=True,
            in_navigation=True,
            site=site2,
        )
        add_plugin(
            get_page_placeholders(site1_page, self.language).get(slot='content'),
            'Alias',
            language=self.language,
            alias=alias,
        )
        add_plugin(
            get_page_placeholders(site2_page, self.language).get(slot='content'),
            'Alias',
            language=self.language,
            alias=alias,
        )
        site1_page.publish(self.language)
        site2_page.publish(self.language)

        with override_settings(SITE_ID=site1.pk):
            response = self.client.get(site1_page.get_absolute_url())
        self.assertContains(response, 'test alias multisite')

        with override_settings(SITE_ID=site2.pk):
            response = self.client.get(site2_page.get_absolute_url())
        self.assertContains(response, 'test alias multisite')

        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='Another alias plugin',
        )
        site1_page.publish(self.language)
        site2_page.publish(self.language)

        with override_settings(SITE_ID=site1.pk):
            response = self.client.get(site1_page.get_absolute_url())
        self.assertContains(response, 'test alias multisite')
        self.assertContains(response, 'Another alias plugin')

        with override_settings(SITE_ID=site2.pk):
            response = self.client.get(site2_page.get_absolute_url())
        self.assertContains(response, 'test alias multisite')
        self.assertContains(response, 'Another alias plugin')
