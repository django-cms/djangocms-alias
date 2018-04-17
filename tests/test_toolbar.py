from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
from cms.toolbar.items import Break

from djangocms_alias.cms_toolbars import ALIAS_MENU_IDENTIFIER
from djangocms_alias.constants import DELETE_ALIAS_PLUGIN_URL_NAME
from djangocms_alias.utils import alias_plugin_reverse

from .base import BaseAliasPluginTestCase


class AliasToolbarTestCase(BaseAliasPluginTestCase):

    def test_add_aliases_submenu_to_admin_menu(self):
        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(self.page.get_absolute_url())

        self.assertNotContains(response, '<span>Aliases')

        page_structure_url = self.get_obj_structure_url(
            self.page.get_absolute_url(),
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(page_structure_url)

        self.assertContains(response, '<span>Aliases')

    def test_aliases_link_placement(self):
        request = self.get_page_request(self.page, user=self.superuser)
        admin_menu = request.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        break_item = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)  # noqa: E501
        item_positioned_before_admin_break = admin_menu.items[break_item.index - 1]  # noqa: E501
        self.assertEqual(item_positioned_before_admin_break.name, 'Aliases')

    def test_add_alias_menu_showing_only_on_alias_plugin_views(self):
        request = self.get_page_request(self.page, user=self.superuser)
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        self.assertEqual(alias_menu, None)

        alias = self._create_alias([self.plugin])
        for endpoint in [
            self.CATEGORY_LIST_ENDPOINT,
            self.LIST_ALIASES_ENDPOINT(alias.category_id),
            self.DETAIL_ALIAS_ENDPOINT(alias.pk),
        ]:
            request = self.get_page_request(
                page=None,
                path=endpoint,
                user=self.superuser,
            )
            alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
            self.assertEqual(alias_menu.name, 'Alias')

    def test_delete_alias_button(self):
        alias = self._create_alias([self.plugin])
        request = self.get_alias_request(alias, user=self.superuser)
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)

        self.assertTrue(len(alias_menu.items) >= 1)
        self.assertIn('Delete Alias', alias_menu.items[0].name)
        self.assertIn(
            alias_plugin_reverse(DELETE_ALIAS_PLUGIN_URL_NAME, args=[alias.pk]),  # noqa: E501
            alias_menu.items[0].url,
        )
        self.assertIn('modal', alias_menu.items[0].template)
        self.assertIn(str(alias.pk), alias_menu.items[0].url)

    def test_delete_alias_button_no_showing_on_list_of_aliases(self):
        request = self.get_alias_request(
            alias=None,
            path=self.CATEGORY_LIST_ENDPOINT,
            user=self.superuser,
        )
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        self.assertNotIn(
            'Delete Alias',
            [item.name for item in alias_menu.items]
        )
