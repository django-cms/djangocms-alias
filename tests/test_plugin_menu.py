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
        self.assertEqual(parsed_url.path, self.CREATE_ALIAS_ENDPOINT)
        self.assertIn('plugin={}'.format(self.plugin.pk), parsed_url.query)

    def test_extra_plugin_items_for_alias_plugins(self):
        alias = self._create_alias()
        alias_plugin = alias.populate(
            language=self.language,
            replaced_placeholder=self.placeholder,
        )

        extra_items = Alias.get_extra_plugin_menu_items(
            self.get_request(self.page.get_absolute_url()),
            alias_plugin,
        )

        self.assertEqual(len(extra_items), 2)
        first, second = extra_items
        self.assertEqual(first.name, 'Edit Alias')
        self.assertEqual(first.url, self.DETAIL_ALIAS_ENDPOINT(alias.pk))

        self.assertEqual(second.name, 'Detach Alias')
        self.assertEqual(second.action, 'modal')
        self.assertEqual(
            second.url,
            self.DETACH_ALIAS_PLUGIN_ENDPOINT(alias_plugin.pk),
        )

    def test_extra_plugin_items_for_placeholder(self):
        extra_items = Alias.get_extra_placeholder_menu_items(
            self.get_page_request(self.page, self.superuser),
            self.placeholder,
        )
        self.assertEqual(len(extra_items), 1)
        extra_item = extra_items[0]
        self.assertEqual(extra_item.name, 'Create Alias')
        self.assertEqual(extra_item.action, 'modal')
        parsed_url = urlparse(extra_item.url)
        self.assertEqual(parsed_url.path, self.CREATE_ALIAS_ENDPOINT)
        self.assertIn(
            'placeholder={}'.format(self.placeholder.pk),
            parsed_url.query,
        )

    def test_delete_button_show_on_edit_alias_view(self):
        alias = self._create_alias()
        extra_items = Alias.get_extra_placeholder_menu_items(
            self.get_alias_request(
                alias,
                path=self.DETAIL_ALIAS_ENDPOINT(alias.pk),
                user=self.superuser,
                edit=True,
                toolbar_object=alias,
            ),
            alias.draft_content,
        )
        self.assertEqual(len(extra_items), 2)
        extra_item = extra_items[1]
        self.assertEqual(extra_item.name, 'Delete Alias')
        self.assertEqual(extra_item.action, 'modal')
        self.assertEqual(extra_item.url, self.DELETE_ALIAS_ENDPOINT(alias.pk))
        self.assertEqual(
            extra_item.attributes['on-close'],
            self.LIST_ALIASES_ENDPOINT(alias.category_id),
        )

        extra_items = Alias.get_extra_placeholder_menu_items(
            self.get_alias_request(
                alias,
                path=self.LIST_ALIASES_ENDPOINT(alias.category_id),
                user=self.superuser,
            ),
            alias.draft_content,
        )
        self.assertEqual(len(extra_items), 1)
