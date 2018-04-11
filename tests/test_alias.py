from operator import attrgetter

from cms.api import add_plugin
from cms.utils.plugins import downcast_plugins

from djangocms_alias.constants import DETAIL_ALIAS_URL_NAME
from djangocms_alias.utils import alias_plugin_reverse

from .base import BaseAlias2PluginTestCase


class Alias2PluginTestCase(BaseAlias2PluginTestCase):

    def test_create_alias_from_plugin_list(self):
        plugins = self.placeholder.get_plugins()
        alias = self._create_alias(plugins)
        self.assertEqual(
            plugins[0].plugin_type,
            alias.placeholder.get_plugins()[0].plugin_type,
        )
        self.assertEqual(
            plugins[0].get_plugin_instance()[0].body,
            alias.placeholder.get_plugins()[0].get_plugin_instance()[0].body,
        )

    def test_replace_plugin_with_alias(self):
        alias = self._create_alias(
            [self.plugin],
        )
        alias_plugin = self.alias_plugin_base.replace_plugin_with_alias(
            self.plugin,
            alias,
            self.language,
        )
        plugins = self.placeholder.get_plugins()
        self.assertNotIn(
            self.plugin,
            plugins,
        )
        self.assertEqual(plugins[0].get_plugin_instance()[0], alias_plugin)
        self.assertEqual(alias_plugin.alias.placeholder.get_plugins()[0].get_plugin_instance()[0].body, 'test')  # noqa: E501

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
        alias_plugin = self.alias_plugin_base.replace_plugin_with_alias(
            second_plugin,
            alias,
            self.language,
        )
        plugins = self.placeholder.get_plugins()
        self.assertNotIn(
            self.plugin,
            plugins,
        )
        self.assertEqual(plugins[1].get_plugin_instance()[0], alias_plugin)

        ordered_plugins = sorted(
            downcast_plugins(plugins),
            key=attrgetter('position'),
        )

        self.assertEqual(
            [plugin.plugin_type for plugin in ordered_plugins],
            ['TextPlugin', 'Alias2Plugin', 'TextPlugin'],
        )

    def test_replace_placeholder_content_with_alias(self):
        add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        alias = self._create_alias()
        self.alias_plugin_base.replace_placeholder_content_with_alias(
            self.placeholder,
            alias,
            self.language,
        )
        plugins = self.placeholder.get_plugins()

        self.assertEqual(plugins.count(), 1)
        self.assertEqual(alias.placeholder.get_plugins().count(), 2)
        self.assertEqual(
            alias.placeholder.get_plugins()[1].get_plugin_instance()[0].body,
            'test 2',
        )

    def test_detach_alias(self):
        alias = self._create_alias()
        add_plugin(
            alias.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        alias_plugin = add_plugin(
            self.placeholder,
            self.alias_plugin_base.__class__,
            language=self.language,
            alias=alias,
        )
        self.assertEqual(plugins.count(), 2)
        self.alias_plugin_base.detach_alias_plugin(alias_plugin, self.language)
        self.assertEqual(plugins.count(), 3)

    def test_detach_alias_correct_position(self):
        alias = self._create_alias([])
        add_plugin(
            alias.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        alias_plugin = add_plugin(
            self.placeholder,
            self.alias_plugin_base.__class__,
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
        self.alias_plugin_base.detach_alias_plugin(alias_plugin, self.language)
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
            self.alias_plugin_base.__class__,
            language=self.language,
            alias=alias,
        )
        request = self.get_request('/')

        alias_plugin_menu_items = self.alias_plugin_base.__class__.get_extra_plugin_menu_items(  # noqa: E501
            request,
            alias_plugin,
        )

        edit_menu_item = next(filter(
            lambda item: item.name == 'Edit Alias',
            alias_plugin_menu_items,
        ))

        self.assertIn('?structure', edit_menu_item.url)
