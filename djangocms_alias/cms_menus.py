from menus.base import Modifier
from menus.menu_pool import menu_pool

from .constants import PLUGIN_URL_NAME_PREFIX


class AliasDisableMenu(Modifier):
    """Disable menu rendering on alias pages"""

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if request.toolbar.app_name == PLUGIN_URL_NAME_PREFIX:
            return []
        return nodes


menu_pool.register_modifier(AliasDisableMenu)
