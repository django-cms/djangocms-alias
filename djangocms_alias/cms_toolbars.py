from django.core.urlresolvers import resolve
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from cms.cms_toolbars import (
    ADMIN_MENU_IDENTIFIER,
    ADMINISTRATION_BREAK,
    SHORTCUTS_BREAK,
)
from cms.toolbar.items import Break
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool

from .constants import (
    CREATE_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
    PLUGIN_URL_NAME_PREFIX,
)
from .utils import alias_plugin_reverse


__all__ = [
    'AliasToolbar',
]


ALIAS_MENU_IDENTIFIER = 'alias'
ALIAS_MENU_CREATE_IDENTIFIER = 'alias-add'


@toolbar_pool.register
class AliasToolbar(CMSToolbar):
    plural_name = _('Aliases')

    def get_create_alias_url(self, parameters):
        return alias_plugin_reverse(
            CREATE_ALIAS_URL_NAME,
            parameters=parameters,
        )

    def populate(self):
        self.is_user_currently_on_alias_plugin_pages = resolve(
            self.toolbar.request_path,
        ).url_name.startswith(PLUGIN_URL_NAME_PREFIX)

        self.add_aliases_link_to_admin_menu()
        self.add_alias_menu()

    def add_aliases_link_to_admin_menu(self):
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        admin_menu.add_link_item(
            self.plural_name,
            url=alias_plugin_reverse(LIST_ALIASES_URL_NAME),
            position=get_insert_position(admin_menu, self.plural_name)
        )

    def add_alias_menu(self):
        if self.is_user_currently_on_alias_plugin_pages:
            alias_menu = self.toolbar.get_or_create_menu(
                ALIAS_MENU_IDENTIFIER,
                self.plural_name,
                position=1,
            )
            alias_menu.add_modal_item(
                _('Create Alias'),
                url=self.get_create_alias_url({
                    'edit': 1,
                    'language': self.toolbar.language,
                }),
                # disabled=not has_perm,
            )


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
