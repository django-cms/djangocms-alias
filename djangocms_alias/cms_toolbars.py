import itertools

from django.utils.encoding import force_text
from django.utils.translation import override
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

from cms.cms_toolbars import (
    ADMIN_MENU_IDENTIFIER,
    ADMINISTRATION_BREAK,
    SHORTCUTS_BREAK,
)
from cms.toolbar.items import Break, ButtonList
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool

from .constants import (
    CATEGORY_LIST_URL_NAME,
    DRAFT_ALIASES_SESSION_KEY,
    PUBLISH_ALIAS_URL_NAME,
    SET_ALIAS_DRAFT_URL_NAME,
)
from .models import Alias as AliasModel
from .utils import alias_plugin_reverse


__all__ = [
    'AliasToolbar',
]


ALIAS_MENU_IDENTIFIER = 'alias'
ADMIN_ALIAS_MENU_IDENTIFIER = 'admin-alias'
ALIAS_MENU_CREATE_IDENTIFIER = 'alias-add'


@toolbar_pool.register
class AliasToolbar(CMSToolbar):
    name = _('Alias')
    plural_name = _('Aliases')

    def populate(self):
        self.add_aliases_link_to_admin_menu()

        if self.is_current_app:
            self.add_alias_menu()

    def post_template_populate(self):
        if self.is_current_app:
            self.alias_placeholder = self.get_alias_placeholder()
            self.add_publish_button()
            self.enable_create_wizard_button()

    def get_alias_placeholder(self):
        if not isinstance(self.toolbar.obj, AliasModel):
            return

        if self.toolbar.edit_mode_active:
            return self.toolbar.obj.draft_placeholder
        return self.toolbar.obj.live_placeholder

    def has_publish_permission(self):
        return self.alias_placeholder and self.toolbar.edit_mode_active

    def has_dirty_objects(self):
        return True

    def user_can_publish(self):
        if not self.toolbar.edit_mode_active:
            return False
        return self.has_publish_permission() and self.has_dirty_objects()

    def add_publish_button(self, classes=None):
        if classes is None:
            classes = ('cms-btn-action', 'cms-btn-publish')
        if self.user_can_publish():
            button = self.get_publish_button(classes=classes)
            self.toolbar.add_item(button)

    def get_publish_button(self, classes=None):
        dirty = self.has_dirty_objects()
        classes = list(classes or [])

        if dirty and 'cms-btn-publish-active' not in classes:
            classes.append('cms-btn-publish-active')

        title = _('Publish alias changes')

        item = ButtonList(side=self.toolbar.RIGHT)
        item.add_button(
            title,
            url=self.get_publish_url(),
            disabled=not dirty,
            extra_classes=classes,
        )
        return item

    def get_publish_url(self):
        with override(self.current_lang):
            return alias_plugin_reverse(
                PUBLISH_ALIAS_URL_NAME,
                args=(
                    self.alias_placeholder.alias.pk,
                    self.current_lang,
                ),
            )

    def add_aliases_link_to_admin_menu(self):
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        alias_menu = admin_menu.get_or_create_menu(
            ADMIN_ALIAS_MENU_IDENTIFIER,
            self.plural_name,
            position=self.get_insert_position(admin_menu, self.plural_name),
        )
        alias_menu.add_link_item(
            _('List of Aliases'),
            url=alias_plugin_reverse(CATEGORY_LIST_URL_NAME),
        )

        use_draft_aliases = self.request.session.get(DRAFT_ALIASES_SESSION_KEY)
        if use_draft_aliases:
            text = _('Disable draft version of Aliases')
        else:
            text = _('Enable draft version of Aliases')

        alias_menu.add_ajax_item(
            text,
            action=alias_plugin_reverse(SET_ALIAS_DRAFT_URL_NAME),
            on_success='REFRESH_PAGE',
            data={'enable': int(not use_draft_aliases)},
        )

    def add_alias_menu(self):
        self.toolbar.get_or_create_menu(
            ALIAS_MENU_IDENTIFIER,
            self.name,
            position=1,
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

        items = admin_menu.get_items()[start.index + 1: end.index]
        for idx, item in enumerate(items):
            try:
                if force_text(item_name.lower()) < force_text(item.name.lower()):  # noqa: E501
                    return idx + start.index + 1
            except AttributeError:
                # Some item types do not have a 'name' attribute.
                pass
        return end.index

    def enable_create_wizard_button(self):
        button_lists = [
            result.item
            for result in self.toolbar.find_items(item_type=ButtonList)
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
        create_wizard_button = [
            button for button in buttons if button.name == ugettext('Create')
        ][0]

        from cms.wizards.wizard_pool import entry_choices
        # we enable this button when user has permissions to perform actions on
        # wizard
        enable_create_wizard_button = bool(
            # entry_choices gets required argument page
            list(entry_choices(self.request.user, page=None))
        )
        create_wizard_button.disabled = not enable_create_wizard_button
