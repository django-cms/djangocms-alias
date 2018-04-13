from django.utils.encoding import force_text
from django.utils.translation import override
from django.utils.translation import ugettext_lazy as _

from cms.cms_toolbars import (
    ADMIN_MENU_IDENTIFIER,
    ADMINISTRATION_BREAK,
    SHORTCUTS_BREAK,
)
from cms.toolbar.items import Break, ButtonList
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.urlutils import admin_reverse

from .constants import (
    CREATE_ALIAS_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
    PUBLISH_ALIAS_URL_NAME,
)
from .models import AliasPlaceholder
from .utils import alias_plugin_reverse


__all__ = [
    'AliasToolbar',
]


ALIAS_MENU_IDENTIFIER = 'alias'
ALIAS_MENU_CREATE_IDENTIFIER = 'alias-add'


@toolbar_pool.register
class AliasToolbar(CMSToolbar):
    name = _('Alias')
    plural_name = _('Aliases')

    def populate(self):
        self.add_aliases_link_to_admin_menu()
        self.add_alias_menu()

    def post_template_populate(self):
        self.alias_placeholder = self.get_alias_placeholder()
        self.is_draft = self.is_alias_placeholder_draft(self.alias_placeholder)
        self.add_publish_button()

    def get_alias_placeholder(self):
        match = self.request.resolver_match
        if match.url_name != DETAIL_ALIAS_URL_NAME:
            return
        renderer = self.toolbar.get_content_renderer()
        placeholder = next(
            (
                placeholder
                for placeholder in renderer.get_rendered_placeholders()
                if placeholder.__class__ == AliasPlaceholder
            ),
            None,
        )
        return placeholder

    def is_alias_placeholder_draft(self, alias_placeholder):
        return (
            alias_placeholder and
            alias_placeholder == alias_placeholder.alias.draft_placeholder
        )

    def has_publish_permission(self):
        return self.alias_placeholder and self.is_draft

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
            return admin_reverse(
                PUBLISH_ALIAS_URL_NAME,
                args=(
                    self.alias_placeholder.alias.pk,
                    self.current_lang,
                ),
            )

    def add_aliases_link_to_admin_menu(self):
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        admin_menu.add_link_item(
            self.plural_name,
            url=alias_plugin_reverse(LIST_ALIASES_URL_NAME),
            position=get_insert_position(admin_menu, self.plural_name),
        )

    def add_alias_menu(self):
        if self.is_current_app:
            alias_menu = self.toolbar.get_or_create_menu(
                ALIAS_MENU_IDENTIFIER,
                self.name,
                position=1,
            )
            # alias_menu.add_modal_item(
            #     _('Delete Alias'),
            #     url=self.get_create_alias_url({
            #         'edit': 1,
            #         'language': self.toolbar.language,
            #     }),
            #     disabled=not has_perm,
            # )


def get_insert_position(admin_menu, item_name):
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
            if force_text(item_name.lower()) < force_text(item.name.lower()):
                return idx + start.index + 1
        except AttributeError:
            # Some item types do not have a 'name' attribute.
            pass
    return end.index
