from cms.cms_toolbars import (
    ADMIN_MENU_IDENTIFIER,
    ADMINISTRATION_BREAK,
    LANGUAGE_MENU_IDENTIFIER,
)
from cms.toolbar.items import Break
import cms.toolbar.utils

from djangocms_alias.cms_toolbars import ALIAS_MENU_IDENTIFIER
from djangocms_alias.compat import get_object_structure_url

from .base import BaseAliasPluginTestCase


class AliasToolbarTestCase(BaseAliasPluginTestCase):

    def test_add_aliases_submenu_to_admin_menu(self):
        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(self.page.get_absolute_url())

        self.assertNotContains(response, '<span>Aliases')

        page_url = get_object_structure_url(self.page)
        with self.login_user_context(self.superuser):
            response = self.client.get(page_url)

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

    def test_alias_toolbar_language_menu(self):
        request = self.get_page_request(self.page, user=self.superuser)
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        self.assertEqual(alias_menu, None)

        alias = self._create_alias([self.plugin])

        request = self.get_page_request(
            page=None,
            path=self.CATEGORY_LIST_ENDPOINT,
            user=self.superuser,
            edit=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        self.assertEqual(language_menu.get_item_count(), 4)

        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            edit=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        self.assertEqual(language_menu.get_item_count(), 7)

        language_menu_dict = {
            menu.name: [menu_item.name for menu_item in menu.items]
            for key, menu in language_menu.menus.items()
        }
        self.assertIn('Add Translation', language_menu_dict.keys())
        self.assertIn('Delete Translation', language_menu_dict.keys())
        self.assertEqual(
            set(['Deutsche...', 'Française...', 'Italiano...']),
            set(language_menu_dict['Add Translation']),
        )
        self.assertEqual(
            set(['English...']),
            set(language_menu_dict['Delete Translation']),
        )

        alias_content = alias.contents.create(name='test alias 2', language='fr')
        alias_content.populate(replaced_placeholder=self.placeholder)

        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            edit=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        self.assertEqual(language_menu.get_item_count(), 8)

        language_menu_dict = {
            menu.name: [menu_item.name for menu_item in menu.items]
            for key, menu in language_menu.menus.items()
        }
        self.assertEqual(
            set(['Deutsche...', 'Italiano...']),
            set(language_menu_dict['Add Translation']),
        )
        self.assertEqual(
            set(['Française...', 'English...']),
            set(language_menu_dict['Delete Translation']),
        )
        self.assertEqual(
            set(['from Française']),
            set(language_menu_dict['Copy all plugins']),
        )
        language_menu_first_items = {
            menu.name: next(filter(
                lambda item: item.name in ['Française...', 'Deutsche...', 'from Française'],
                menu.items,
            ))
            for key, menu in language_menu.menus.items()
        }
        # First item is Deutsche... for Add Translation
        self.assertIn(
            '/en/admin/djangocms_alias/aliascontent/add/',
            language_menu_first_items['Add Translation'].url,
        )
        self.assertIn(
            'language=de',
            language_menu_first_items['Add Translation'].url,
        )
        self.assertIn(
            'alias={}'.format(alias.pk),
            language_menu_first_items['Add Translation'].url,
        )
        self.assertEqual(
            # First item is Française... for Delete Translation
            '/en/admin/djangocms_alias/aliascontent/{}/delete/?language=fr'.format(
                alias.get_content('fr').pk,
            ),
            language_menu_first_items['Delete Translation'].url,
        )
        self.assertRegexpMatches(
            language_menu_first_items['Copy all plugins'].action,
            'en\/admin\/([\w\/]+)\/copy-plugins\/',
        )
