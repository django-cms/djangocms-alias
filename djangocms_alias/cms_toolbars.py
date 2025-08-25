import itertools
from copy import copy

from cms.cms_toolbars import (
    ADMIN_MENU_IDENTIFIER,
    ADMINISTRATION_BREAK,
    LANGUAGE_MENU_IDENTIFIER,
    SHORTCUTS_BREAK,
)
from cms.toolbar.items import Break, ButtonList
from cms.toolbar.utils import get_object_edit_url
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.i18n import (
    get_default_language,
    get_language_dict,
    get_language_tuple,
)
from cms.utils.permissions import get_model_permission_codename
from cms.utils.urlutils import add_url_parameters, admin_reverse
from django.urls import NoReverseMatch
from django.utils.encoding import force_str
from django.utils.http import urlencode
from django.utils.translation import (
    get_language_from_request,
    gettext,
)
from django.utils.translation import (
    gettext_lazy as _,
)

from .constants import (
    DELETE_ALIAS_URL_NAME,
    LIST_ALIAS_URL_NAME,
    USAGE_ALIAS_URL_NAME,
)
from .models import Alias, AliasContent

__all__ = [
    "AliasToolbar",
]


ALIAS_MENU_IDENTIFIER = "alias"
ALIAS_MENU_CREATE_IDENTIFIER = "alias-add"
ALIAS_LANGUAGE_BREAK = "alias-language"


@toolbar_pool.register
class AliasToolbar(CMSToolbar):
    name = _("Alias")
    plural_name = _("Aliases")

    def populate(self):
        self.add_aliases_link_to_admin_menu()

        if isinstance(self.toolbar.obj, AliasContent):
            self.add_alias_menu()
            self.override_language_switcher()
            self.change_language_menu()

    def post_template_populate(self):
        if self.is_current_app or isinstance(self.toolbar.obj, AliasContent):
            self.enable_create_wizard_button()

    def add_aliases_link_to_admin_menu(self):
        if not self.request.user.has_perm("djangocms_alias.change_category"):
            return
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)

        url = admin_reverse(LIST_ALIAS_URL_NAME)
        obj = self.toolbar.get_object()
        language = obj.language if hasattr(obj, "language") else get_language_from_request(self.request)
        if language is None:
            language = get_default_language()
        url += f"?{urlencode({'language': language})}"

        admin_menu.add_sideframe_item(
            _("Aliases"),
            url=url,
            position=self.get_insert_position(admin_menu, self.plural_name),
        )

    def add_alias_menu(self):
        alias_menu = self.toolbar.get_or_create_menu(
            ALIAS_MENU_IDENTIFIER,
            self.name,
            position=1,
        )

        can_change = self.request.user.has_perm(
            get_model_permission_codename(Alias, "change"),
        )
        alias_menu.add_modal_item(
            _("Change alias settings"),
            url=admin_reverse(
                "djangocms_alias_alias_change",
                args=[self.toolbar.obj.alias_id],
            ),
            disabled=not can_change,
        )
        alias_menu.add_modal_item(
            _("View usage"),
            url=admin_reverse(
                USAGE_ALIAS_URL_NAME,
                args=[self.toolbar.obj.alias_id],
            ),
        )

        # Only show deletion if versioning is not enabled
        alias_menu.add_modal_item(
            _("Delete alias"),
            url=admin_reverse(
                DELETE_ALIAS_URL_NAME,
                args=(self.toolbar.obj.alias_id,),
            ),
            on_close=admin_reverse(
                LIST_ALIAS_URL_NAME,
            ),
            disabled=not can_change,
        )

    @classmethod
    def get_insert_position(cls, admin_menu, item_name):
        """
        Ensures that there is a SHORTCUTS_BREAK and returns a position for an
        alphabetical position against all items between SHORTCUTS_BREAK, and
        the ADMINISTRATION_BREAK.
        """
        start = admin_menu.find_first(Break, identifier=SHORTCUTS_BREAK)

        if not start:
            end = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)
            admin_menu.add_break(SHORTCUTS_BREAK, position=end.index)
            start = admin_menu.find_first(Break, identifier=SHORTCUTS_BREAK)
        end = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)

        items = admin_menu.get_items()[start.index + 1 : end.index]
        for idx, item in enumerate(items):
            try:
                if force_str(item_name.lower()) < force_str(item.name.lower()):  # noqa: E501
                    return idx + start.index + 1
            except AttributeError:
                # Some item types do not have a 'name' attribute.
                pass
        return end.index

    def enable_create_wizard_button(self):
        button_lists = [result.item for result in self.toolbar.find_items(item_type=ButtonList)]
        buttons = list(
            # flatten the list
            itertools.chain.from_iterable([item.buttons for item in button_lists])
        )

        # There will always be this button, because we are in the context of
        # alias app views
        create_wizard_button = [button for button in buttons if button.name == gettext("Create")][0]

        from cms.wizards.wizard_pool import entry_choices

        # we enable this button when user has permissions to perform actions on
        # wizard
        enable_create_wizard_button = bool(
            # entry_choices gets required argument page
            list(entry_choices(self.request.user, page=None))
        )
        create_wizard_button.disabled = not enable_create_wizard_button

    def override_language_switcher(self):
        language_menu = self.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER, _("Language"))
        if not language_menu:
            return
        # Remove all existing language links
        # remove_item uses `items` attribute so we have to copy object
        for _item in copy(language_menu.items):
            language_menu.remove_item(item=_item)

        for code, name in get_language_tuple(self.current_site.pk):
            # Showing only existing translation. For versioning it will be the
            # latest translation i.e. draft or published
            alias_content = self.toolbar.obj.alias.get_content(
                language=code,
                show_draft_content=True,
            )
            if alias_content:
                url = get_object_edit_url(alias_content, language=code)
                language_menu.add_link_item(name, url=url, active=self.current_lang == code)

    def change_language_menu(self):
        if self.toolbar.edit_mode_active and isinstance(self.toolbar.obj, AliasContent):
            can_change = self.request.user.has_perm(
                get_model_permission_codename(Alias, "change"),
            )
        else:
            can_change = False

        if can_change:
            alias_content = self.toolbar.obj
            language_menu = self.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
            if not language_menu:
                return None

            languages = get_language_dict(self.current_site.pk)
            current_placeholder = alias_content.placeholder

            remove = [
                (code, languages.get(code, code)) for code in alias_content.alias.get_languages() if code in languages
            ]
            add = [code for code in languages.items() if code not in remove]
            copy = [
                (code, name)
                for code, name in languages.items()
                if code != self.current_lang and (code, name) in remove and current_placeholder
            ]

            if add or remove or copy:
                language_menu.add_break(ALIAS_LANGUAGE_BREAK)

            if add:
                add_plugins_menu = language_menu.get_or_create_menu(
                    f"{LANGUAGE_MENU_IDENTIFIER}-add",
                    _("Add Translation"),
                )
                add_url = admin_reverse("djangocms_alias_aliascontent_add")

                for code, name in add:
                    url = add_url_parameters(add_url, language=code, alias=alias_content.alias_id)
                    add_plugins_menu.add_modal_item(name, url=url)

            if remove:
                remove_plugins_menu = language_menu.get_or_create_menu(
                    f"{LANGUAGE_MENU_IDENTIFIER}-del",
                    _("Delete Translation"),
                )
                disabled = len(remove) == 1
                for code, name in remove:
                    alias_content = alias_content.alias.get_content(
                        language=code,
                        show_draft_content=True,
                    )
                    translation_delete_url = admin_reverse(
                        "djangocms_alias_aliascontent_delete",
                        args=(alias_content.pk,),
                    )
                    url = add_url_parameters(translation_delete_url, language=code)
                    remove_plugins_menu.add_modal_item(name, url=url, disabled=disabled)

            if copy:
                copy_plugins_menu = language_menu.get_or_create_menu(
                    f"{LANGUAGE_MENU_IDENTIFIER}-copy", _("Copy all plugins")
                )
                title = _("from %s")
                question = _("Are you sure you want to copy all plugins from %s?")

                try:
                    copy_url = admin_reverse("cms_placeholder_copy_plugins")
                except NoReverseMatch:
                    copy_url = admin_reverse("djangocms_alias_alias_copy_plugins")

                for code, name in copy:
                    source_placeholder = alias_content.alias.get_placeholder(
                        language=code,
                        show_draft_content=True,
                    )
                    copy_plugins_menu.add_ajax_item(
                        title % name,
                        action=copy_url,
                        data={
                            "source_language": code,
                            "source_placeholder_id": source_placeholder.pk,
                            "target_language": self.current_lang,
                            "target_placeholder_id": current_placeholder.pk,
                        },
                        question=question % name,
                        on_success=self.toolbar.REFRESH_PAGE,
                    )
