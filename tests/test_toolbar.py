import itertools

from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
from cms.toolbar.items import Break, ButtonList

from djangocms_alias.cms_toolbars import ALIAS_MENU_IDENTIFIER

from .base import BaseAliasPluginTestCase


class AliasToolbarTestCase(BaseAliasPluginTestCase):

    def _get_wizard_create_button(self, request):
        button_lists = [
            result.item
            for result in request.toolbar.find_items(item_type=ButtonList)
        ]
        buttons = list(
            # flatten the list
            itertools.chain.from_iterable([
                item.buttons
                for item in button_lists
            ])
        )

        # There will always be this button, because we are in the context of
        # alias app views
        return [
            button for button in buttons if button.name == 'Create'
        ][0]

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

    def test_add_publish_button(self):
        alias = self._create_alias([self.plugin])
        request = self.get_alias_request(
            alias,
            path=self.DETAIL_ALIAS_ENDPOINT(alias.pk),
            user=self.superuser,
            edit=True,
            toolbar_object=alias,
        )
        button_list = request.toolbar.find_first(
            item_type=ButtonList,
            identifier='Publish',
        )
        self.assertEqual(button_list.item.buttons[0].name, 'Publish alias changes')  # noqa: E501
        self.assertEqual(
            button_list.item.buttons[0].url,
            self.PUBLISH_ALIAS_ENDPOINT(alias.pk),
        )
        self.assertEqual(
            button_list.item.buttons[0].disabled,
            False,
        )
        self.assertIn(
            'cms-btn-publish',
            button_list.item.buttons[0].extra_classes,
        )
        self.assertIn(
            'cms-btn-publish-active',
            button_list.item.buttons[0].extra_classes,
        )

    def test_add_publish_button_dont_add_when_is_not_alias_edit(self):
        alias = self._create_alias([self.plugin])
        request = self.get_alias_request(
            alias,
            path=self.DETAIL_ALIAS_ENDPOINT(alias.pk),
            user=self.superuser,
            toolbar_object=alias,
        )
        button_list = request.toolbar.find_first(
            item_type=ButtonList,
            identifier='Publish',
        )
        self.assertEqual(button_list, None)

        request = self.get_alias_request(
            alias,
            path=self.LIST_ALIASES_ENDPOINT(alias.category.pk),
            user=self.superuser,
        )
        button_list = request.toolbar.find_first(
            item_type=ButtonList,
            identifier='Publish',
        )
        self.assertEqual(button_list, None)

        request = self.get_page_request(
            self.page,
            user=self.superuser,
        )
        button_list = request.toolbar.find_first(
            item_type=ButtonList,
            identifier='Publish',
        )
        self.assertEqual(button_list, None)

    def test_enable_create_wizard_button(self):
        request = self.get_page_request(
            page=None,
            path=self.CATEGORY_LIST_ENDPOINT,
            user=self.superuser,
        )
        create_button = self._get_wizard_create_button(request)
        self.assertEqual(create_button.disabled, False)
