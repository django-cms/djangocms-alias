import json
from urllib.parse import urlparse

from .base import BaseAliasPluginTestCase


class AliasPluginMenuTestCase(BaseAliasPluginTestCase):

    def test_extra_plugin_items_for_regular_plugins(self):
        extra_items = self.alias_plugin_base.get_extra_plugin_menu_items(
            self.get_request(self.page.get_absolute_url()),
            self.plugin,
        )
        self.assertEqual(len(extra_items), 1)
        extra_item = extra_items[0]
        self.assertEqual(extra_item.name, 'Create Alias')
        self.assertEqual(extra_item.action, 'modal')
        parsed_url = urlparse(extra_item.url)
        self.assertEqual(parsed_url.path, self.CREATE_ALIAS_ENDPOINT)
        self.assertEqual(parsed_url.query, 'plugin={}'.format(self.plugin.pk))

    def test_extra_plugin_items_for_alias_plugins(self):
        alias = self._create_alias(self.placeholder.get_plugins())
        alias_plugin = self.alias_plugin_base.replace_placeholder_content_with_alias(  # noqa: E501
            self.placeholder,
            alias,
            self.language,
        )

        extra_items = self.alias_plugin_base.get_extra_plugin_menu_items(
            self.get_request(self.page.get_absolute_url()),
            alias_plugin,
        )

        self.assertEqual(len(extra_items), 2)
        first, second = extra_items
        self.assertEqual(first.name, 'Edit Alias')
        self.assertEqual(first.url, self.DETAIL_ALIAS_ENDPOINT(alias.pk))

        self.assertEqual(second.name, 'Detach Alias')
        self.assertEqual(second.action, 'ajax')
        data = json.loads(second.data)
        self.assertIn('plugin', data)
        self.assertEqual(data['plugin'], alias_plugin.pk)

        parsed_url = urlparse(second.url)
        self.assertEqual(parsed_url.path, self.DETACH_ALIAS_PLUGIN_ENDPOINT)

    def test_extra_plugin_items_for_placeholder(self):
        extra_items = self.alias_plugin_base.get_extra_placeholder_menu_items(
            self.get_request(self.page.get_absolute_url()),
            self.placeholder,
        )
        self.assertEqual(len(extra_items), 1)
        extra_item = extra_items[0]
        self.assertEqual(extra_item.name, 'Create Alias')
        self.assertEqual(extra_item.action, 'modal')
        parsed_url = urlparse(extra_item.url)
        self.assertEqual(parsed_url.path, self.CREATE_ALIAS_ENDPOINT)
        self.assertEqual(
            parsed_url.query,
            'placeholder={}'.format(self.placeholder.pk),
        )
