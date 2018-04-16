from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
from cms.toolbar.items import Break

from djangocms_alias.cms_toolbars import ALIAS_MENU_IDENTIFIER

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
        request = self.get_page_request(self.page, self.superuser)
        admin_menu = request.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        break_item = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)  # noqa: E501
        item_positioned_before_admin_break = admin_menu.items[break_item.index - 1]  # noqa: E501
        self.assertEqual(item_positioned_before_admin_break.name, 'Aliases')

    def test_add_alias_menu_showing_only_on_alias_plugin_views(self):
        request = self.get_page_request(self.page, self.superuser)
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        self.assertEqual(alias_menu, None)

        alias = self._create_alias([self.plugin])
        for endpoint in [
            self.LIST_ALIASES_ENDPOINT,
            self.DETAIL_ALIAS_ENDPOINT(alias.pk),
        ]:
            request = self.get_page_request(
                None,
                self.superuser,
                path=self.LIST_ALIASES_ENDPOINT,
            )
            alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
            self.assertEqual(alias_menu.name, 'Alias')

    # TODO delete alias
    # TODO: cover cases from get_insert_position
    # TODO showing if has perms
