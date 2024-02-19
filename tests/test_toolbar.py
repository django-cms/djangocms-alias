import itertools
from collections import ChainMap
from unittest import skipUnless

from cms.cms_toolbars import (
    ADMIN_MENU_IDENTIFIER,
    ADMINISTRATION_BREAK,
    LANGUAGE_MENU_IDENTIFIER,
)
from cms.toolbar.items import Break, ButtonList, ModalItem
from cms.toolbar.utils import get_object_edit_url
from cms.utils.i18n import force_language
from cms.utils.urlutils import admin_reverse
from django.contrib.auth.models import Permission
from django.urls import reverse

from djangocms_alias.cms_toolbars import ALIAS_MENU_IDENTIFIER
from djangocms_alias.constants import USAGE_ALIAS_URL_NAME
from djangocms_alias.models import AliasContent
from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class AliasToolbarTestCase(BaseAliasPluginTestCase):
    def _get_wizard_create_button(self, request):
        button_lists = [result.item for result in request.toolbar.find_items(item_type=ButtonList)]
        buttons = list(
            # flatten the list
            itertools.chain.from_iterable([item.buttons for item in button_lists])
        )
        # There will always be this button, because we are in the context of
        # alias app views
        return [button for button in buttons if button.name == "Create"][0]

    def test_add_aliases_submenu_to_admin_menu_no_permission(self):
        with self.login_user_context(self.get_staff_user_with_std_permissions()):
            response = self.client.get(self.page.get_absolute_url())
        self.assertNotContains(response, "<span>Aliases")

    def test_add_aliases_submenu_to_admin_menu(self):
        user = self.get_staff_user_with_std_permissions()
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label="djangocms_alias", codename="change_category")
        )
        try:
            page_url = get_object_edit_url(self.page.get_title_obj(self.language))
        except AttributeError:
            page_url = get_object_edit_url(self.page.get_content_obj(self.language))
        with self.login_user_context(user):
            response = self.client.get(page_url, follow=True)
        self.assertContains(response, "<span>Aliases")

    def test_aliases_link_placement(self):
        request = self.get_page_request(self.page, user=self.superuser)
        admin_menu = request.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        break_item = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)  # noqa: E501
        item_positioned_before_admin_break = admin_menu.items[break_item.index - 1]  # noqa: E501
        self.assertEqual(item_positioned_before_admin_break.name, "Aliases...")

    def test_add_alias_menu_showing_only_on_alias_plugin_views(self):
        alias = self._create_alias([self.plugin])
        for endpoint in [
            self.get_category_list_endpoint(),
            self.get_list_alias_endpoint(),
            self.page.get_absolute_url(language=self.language),
        ]:
            request = self.get_page_request(page=None, path=endpoint, user=self.superuser)
            alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
            self.assertEqual(alias_menu, None)

        def _test_alias_endpoint(**kwargs):
            kwargs.update(
                {
                    "alias": alias,
                    "path": endpoint,
                    "user": self.superuser,
                }
            )
            # py34 compat
            request = self.get_alias_request(**ChainMap(kwargs))
            alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
            self.assertEqual(alias_menu.name, "Alias")

        _test_alias_endpoint()
        _test_alias_endpoint(edit=True)
        _test_alias_endpoint(preview=True)

    def test_alias_toolbar_language_menu(self):
        request = self.get_page_request(self.page, user=self.superuser)
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        self.assertEqual(alias_menu, None)

        alias = self._create_alias([self.plugin])

        request = self.get_page_request(
            page=None,
            path=self.get_category_list_endpoint(),
            user=self.superuser,
            edit=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        self.assertEqual(language_menu.get_item_count(), 4)

        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            preview=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        self.assertEqual(language_menu.get_item_count(), 1)

        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            edit=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        self.assertEqual(language_menu.get_item_count(), 4)

        language_menu_dict = {
            menu.name: [menu_item.name for menu_item in menu.items] for key, menu in language_menu.menus.items()
        }
        self.assertIn("Add Translation", language_menu_dict.keys())
        self.assertIn("Delete Translation", language_menu_dict.keys())
        self.assertEqual(
            {"Deutsche...", "Française...", "Italiano..."},
            set(language_menu_dict["Add Translation"]),
        )
        self.assertEqual(
            {"English..."},
            set(language_menu_dict["Delete Translation"]),
        )

        alias_content = alias.contents.create(name="test alias 2", language="fr")
        alias_content.populate(replaced_placeholder=self.placeholder)
        alias_content.alias.clear_cache()

        if is_versioning_enabled():
            from djangocms_versioning.constants import PUBLISHED
            from djangocms_versioning.models import Version

            Version.objects.create(content=alias_content, created_by=self.superuser, state=PUBLISHED)

        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            edit=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        self.assertEqual(language_menu.get_item_count(), 6)

        language_menu_dict = {
            menu.name: [menu_item.name for menu_item in menu.items] for key, menu in language_menu.menus.items()
        }
        self.assertEqual(
            {"Deutsche...", "Italiano..."},
            set(language_menu_dict["Add Translation"]),
        )
        self.assertEqual(
            {"Française...", "English..."},
            set(language_menu_dict["Delete Translation"]),
        )
        self.assertEqual(
            {"from Française"},
            set(language_menu_dict["Copy all plugins"]),
        )
        language_menu_first_items = {
            menu.name: next(
                filter(
                    lambda item: item.name in ["Française...", "Deutsche...", "from Française"],
                    menu.items,
                )
            )
            for key, menu in language_menu.menus.items()
        }
        # First item is Deutsche... for Add Translation
        self.assertIn(
            "/en/admin/djangocms_alias/aliascontent/add/",
            language_menu_first_items["Add Translation"].url,
        )
        self.assertIn(
            "language=de",
            language_menu_first_items["Add Translation"].url,
        )
        self.assertIn(
            f"alias={alias.pk}",
            language_menu_first_items["Add Translation"].url,
        )
        self.assertEqual(
            # First item is Française... for Delete Translation
            "/en/admin/djangocms_alias/aliascontent/{}/delete/?language=fr".format(
                alias.get_content("fr").pk,
            ),
            language_menu_first_items["Delete Translation"].url,
        )
        self.assertRegex(
            language_menu_first_items["Copy all plugins"].action,
            r"en\/admin\/([\w\/]+)\/copy-plugins\/",
        )

    def test_language_switcher_when_toolbar_object_is_alias_content(self):
        alias = self._create_alias([self.plugin])
        alias_content = alias.contents.create(name="test alias 2", language="fr")
        expected_result = ["English", "Française"]

        if is_versioning_enabled():
            from djangocms_versioning.constants import DRAFT
            from djangocms_versioning.models import Version

            Version.objects.create(content=alias_content, created_by=self.superuser, state=DRAFT)

        alias_content.populate(replaced_placeholder=self.placeholder)
        alias_content.alias.clear_cache()
        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            preview=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)

        self.assertEqual([item.name for item in language_menu.items], expected_result)

    def test_language_switcher_when_toolbar_object_isnt_alias_content(self):
        request = self.get_page_request(
            page=self.page,
            user=self.superuser,
            preview=True,
        )
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        expected_result = ["English", "Deutsche", "Française", "Italiano"]
        # Versioning changes the toolbar language selector and only shows
        # languages that have translations
        if is_versioning_enabled():
            expected_result = ["English"]

        # Don't change default language switcher that is used for Pages
        self.assertEqual([item.name for item in language_menu.items], expected_result)

    def test_page_toolbar_no_language_menu(self):
        from django.utils.translation import gettext as _

        alias = self._create_alias([self.plugin])
        alias_content = alias.contents.create(name="test alias 2", language="fr")
        # Get request
        request = self.get_alias_request(
            alias=alias,
            lang_code="fr",
            path=get_object_edit_url(alias_content),
            user=self.get_superuser(),
        )
        # Remove language menu from request's toolbar
        del request.toolbar.menus[LANGUAGE_MENU_IDENTIFIER]

        # find VersioningPageToolbar
        for cls, toolbar in request.toolbar.toolbars.items():
            if cls == "djangocms_alias.cms_toolbars.AliasToolbar":
                # and call override_language_menu
                toolbar.override_language_switcher()
                break
        else:
            self.fail("No AliasToolbar in alias request")
        language_menu = request.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER, _("Language"))
        self.assertIsNone(language_menu)

    def test_change_alias_settings_button_is_visible_on_alias_edit_view(self):
        button_label = "Change alias settings..."
        alias_change_viewname = "djangocms_alias_alias_change"
        alias = self._create_alias()
        with force_language("en"):
            request = self.get_alias_request(
                alias=alias,
                user=self.superuser,
                edit=True,
            )
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        search_result = alias_menu.find_first(item_type=ModalItem, name=button_label)
        self.assertIsNotNone(search_result)
        button = search_result.item
        self.assertEqual(button.on_close, "REFRESH_PAGE")
        self.assertEqual(
            button.url,
            admin_reverse(
                alias_change_viewname,
                args=[alias.pk],
            ),
        )

    def test_alias_usage_button(self):
        alias = self._create_alias()
        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            edit=True,
        )
        button_label = "View usage..."
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        search_result = alias_menu.find_first(item_type=ModalItem, name=button_label)
        self.assertIsNotNone(search_result)
        button = search_result.item
        self.assertEqual(
            button.url,
            admin_reverse(
                USAGE_ALIAS_URL_NAME,
                args=[alias.pk],
            ),
        )
        self.assertEqual(
            button.on_close,
            "REFRESH_PAGE",
        )

    def test_create_wizard_button_enabled(self):
        request = self.get_page_request(
            page=None,
            path=self.get_category_list_endpoint(),
            user=self.superuser,
        )
        create_button = self._get_wizard_create_button(request)
        self.assertEqual(create_button.disabled, False)

    @skipUnless(not is_versioning_enabled(), "Test only relevant when no versioning")
    def test_delete_button_show_on_edit_alias_view_no_versioning(self):
        """
        When versioning is not installed deletion should be possible. The delete button
        should be available in the toolbar.
        """
        alias = self._create_alias()
        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            edit=True,
        )
        button_label = "Delete alias..."
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)

        search_result = alias_menu.find_first(item_type=ModalItem, name=button_label)

        self.assertIsNotNone(search_result)

        button = search_result.item

        self.assertEqual(button.name, button_label)
        self.assertEqual(button.url, self.get_delete_alias_endpoint(alias.pk))
        self.assertEqual(
            button.on_close,
            self.get_list_alias_endpoint(),
        )

    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_delete_button_not_shown_on_edit_alias_view_with_versioning(self):
        """
        When versioning is installed no deletion should be possible. The delete button
        should not be available in the toolbar.
        """
        alias = self._create_alias()
        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            edit=True,
        )
        button_label = "Delete alias..."
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        search_result = alias_menu.find_first(item_type=ModalItem, name=button_label)

        # No button should be found for delete
        self.assertIsNone(search_result)

    def test_do_not_disable_buttons_when_in_preview_mode(self):
        alias = self._create_alias()
        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            preview=True,
        )
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        search_results = alias_menu.find_items(item_type=ModalItem)
        self.assertNotEqual(bool(search_results), False)
        for result in search_results:
            if result.item.name == "View usage...":
                self.assertEqual(result.item.disabled, False)
            else:
                self.assertEqual(result.item.disabled, False)

    def test_disable_buttons_when_not_have_perms(self):
        alias = self._create_alias()
        staff_user = self._create_user("user1", is_staff=True, is_superuser=False)
        request = self.get_alias_request(
            alias=alias,
            user=staff_user,
            edit=True,
        )
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        search_results = alias_menu.find_items(item_type=ModalItem)
        self.assertNotEqual(bool(search_results), False)
        for result in search_results:
            if result.item.name == "View usage...":
                self.assertEqual(result.item.disabled, False)
            else:
                self.assertEqual(result.item.disabled, True)

    def test_enable_buttons_when_on_edit_mode(self):
        alias = self._create_alias()
        request = self.get_alias_request(
            alias=alias,
            user=self.superuser,
            edit=True,
        )
        alias_menu = request.toolbar.get_menu(ALIAS_MENU_IDENTIFIER)
        search_results = alias_menu.find_items(item_type=ModalItem)
        self.assertNotEqual(bool(search_results), False)
        for result in search_results:
            self.assertEqual(result.item.disabled, False)

    def test_site_dropdown_url_renders_admin_changelist(self):
        request = self.get_page_request(self.page, user=self.superuser)
        admin_menu = request.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        site_aliases_url = admin_menu.items[3].url

        with self.login_user_context(self.superuser):
            response = self.client.get(
                site_aliases_url,
            )

        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        # Rendered content should contain admin changelist header
        self.assertIn("Select alias to change | Django site admin", content)

    def test_site_dropdown_url_renders_admin_changelist_url(self):
        request = self.get_page_request(self.page, user=self.superuser)
        admin_menu = request.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        site_aliases_url = admin_menu.items[3].url
        admin_changelist_aliases_url = (
            reverse(f"admin:{AliasContent._meta.app_label}_alias_changelist") + "?language=en"
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                site_aliases_url,
            )

        self.assertEqual(response.status_code, 200)
        # Url from site menu renders Alias content
        self.assertEqual(site_aliases_url, admin_changelist_aliases_url)
