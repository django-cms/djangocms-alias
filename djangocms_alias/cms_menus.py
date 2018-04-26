from menus.base import Modifier
from menus.menu_pool import menu_pool


class AliasDisableMenu(Modifier):
    """Disable menu rendering on alias pages"""

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if request.resolver_match.url_name.startswith('djangocms_alias'):
            return []
        return nodes


menu_pool.register_modifier(AliasDisableMenu)
