import itertools

from django.utils.translation import override, ugettext
from django.utils.translation import ugettext_lazy as _

from cms.cms_toolbars import (
    ADMIN_MENU_IDENTIFIER,
    ADMINISTRATION_BREAK,
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

    @property
    def is_alias_edit_view(self):
        return self.alias_placeholder and self.toolbar.edit_mode_active

    @property
    def has_dirty_objects(self):
        # TODO
        return True

    def populate(self):
        self.add_aliases_link_to_admin_menu()

        if self.is_current_app:
            self.add_alias_menu()

    def post_template_populate(self):
        if self.is_current_app:
            self.alias_placeholder = self.get_alias_placeholder()
            self.add_publish_button()
            self.enable_wizard_create_button()

    def get_alias_placeholder(self):
        if not isinstance(self.toolbar.obj, AliasModel):
            return

        if self.toolbar.edit_mode_active:
            return self.toolbar.obj.draft_placeholder
        return self.toolbar.obj.live_placeholder

    def add_publish_button(self, classes=None):
        if classes is None:
            classes = ('cms-btn-action', 'cms-btn-publish')
        if self.is_alias_edit_view:
            button = self.get_publish_button(classes=classes)
            self.toolbar.add_item(button)

    def get_publish_button(self, classes=None):
        dirty = self.has_dirty_objects
        classes = list(classes or [])

        if dirty and 'cms-btn-publish-active' not in classes:
            classes.append('cms-btn-publish-active')

        title = _('Publish alias changes')

        item = ButtonList('Publish', side=self.toolbar.RIGHT)
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
        position = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)  # noqa: E501
        alias_menu = admin_menu.get_or_create_menu(
            ADMIN_ALIAS_MENU_IDENTIFIER,
            self.plural_name,
            position=position,
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

    def enable_wizard_create_button(self):
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
        wizard_create_button = [
            button for button in buttons if button.name == ugettext('Create')
        ][0]

        from cms.wizards.wizard_pool import entry_choices
        # we enable this button when user has permissions to perform actions on
        # wizard
        enabled = bool(
            list(entry_choices(self.request.user, page=None))
        )
        wizard_create_button.disabled = not enabled
