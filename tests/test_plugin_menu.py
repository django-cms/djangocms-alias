from urllib.parse import urlparse

from djangocms_alias.cms_plugins import Alias

from .base import BaseAliasPluginTestCase


class AliasPluginMenuTestCase(BaseAliasPluginTestCase):

    def test_extra_plugin_items_for_regular_plugins(self):
        extra_items = Alias.get_extra_plugin_menu_items(
            self.get_request(self.page.get_absolute_url()),
            self.plugin,
        )
        self.assertEqual(len(extra_items), 1)
        extra_item = extra_items[0]
        self.assertEqual(extra_item.name, 'Create Alias')
        self.assertEqual(extra_item.action, 'modal')
        parsed_url = urlparse(extra_item.url)
        self.assertEqual(parsed_url.path, self.get_create_alias_endpoint())
        self.assertIn('plugin={}'.format(self.plugin.pk), parsed_url.query)

    def test_extra_plugin_items_for_alias_plugins(self):
        alias = self._create_alias()
        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=self.placeholder
        )

        extra_items = Alias.get_extra_plugin_menu_items(
            self.get_request(self.page.get_absolute_url()),
            alias_plugin,
        )

        self.assertEqual(len(extra_items), 2)
        first, second = extra_items
        self.assertEqual(first.name, 'Edit Alias')
        self.assertEqual(first.url, alias.get_absolute_url())

        self.assertEqual(second.name, 'Detach Alias')
        self.assertEqual(second.action, 'modal')
        self.assertEqual(
            second.url,
            self.get_detach_alias_plugin_endpoint(alias_plugin.pk),
        )

    def test_extra_plugin_items_for_placeholder(self):
        extra_items = Alias.get_extra_placeholder_menu_items(
            self.get_page_request(page=self.page, user=self.superuser),
            self.placeholder,
        )
        self.assertEqual(len(extra_items), 1)
        extra_item = extra_items[0]
        self.assertEqual(extra_item.name, 'Create Alias')
        self.assertEqual(extra_item.action, 'modal')
        parsed_url = urlparse(extra_item.url)
        self.assertEqual(parsed_url.path, self.get_create_alias_endpoint())
        self.assertIn(
            'placeholder={}'.format(self.placeholder.pk),
            parsed_url.query,
        )
