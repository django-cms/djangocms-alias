from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.toolbar.utils import get_object_edit_url
from cms.utils.permissions import (
    get_model_permission_codename,
    has_plugin_permission,
)
from cms.utils.plugins import copy_plugins_to_placeholder
from cms.utils.urlutils import add_url_parameters, admin_reverse
from django.utils.translation import (
    get_language_from_request,
)
from django.utils.translation import (
    gettext_lazy as _,
)

from .constants import CREATE_ALIAS_URL_NAME, DETACH_ALIAS_PLUGIN_URL_NAME
from .forms import AliasPluginForm
from .models import Alias as AliasModel
from .models import AliasContent, AliasPlugin

__all__ = [
    "Alias",
]


@plugin_pool.register_plugin
class Alias(CMSPluginBase):
    name = _("Alias")
    model = AliasPlugin
    form = AliasPluginForm

    def get_render_template(self, context, instance, placeholder):
        if isinstance(instance.placeholder.source, AliasContent) and instance.is_recursive():
            return "djangocms_alias/alias_recursive.html"
        return f"djangocms_alias/{instance.template}/alias.html"

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        if plugin.plugin_type == cls.__name__:
            alias_content = plugin.alias.get_content()
            detach_endpoint = admin_reverse(
                DETACH_ALIAS_PLUGIN_URL_NAME,
                args=[plugin.pk],
            )

            plugin_menu_items = []
            if alias_content:
                plugin_menu_items.append(
                    PluginMenuItem(
                        _("Edit Alias"),
                        get_object_edit_url(alias_content),
                        action="",
                        attributes={"cms-icon": "alias"},
                    ),
                )

            if cls.can_detach(
                request.user,
                plugin.placeholder,
                plugin.alias.get_plugins(),
            ):
                plugin_menu_items.append(
                    PluginMenuItem(
                        _("Detach Alias"),
                        detach_endpoint,
                        action="modal",
                        attributes={"cms-icon": "alias"},
                    )
                )
            return plugin_menu_items

        data = {
            "plugin": plugin.pk,
            "language": get_language_from_request(request, check_path=True),
        }
        endpoint = add_url_parameters(admin_reverse(CREATE_ALIAS_URL_NAME), **data)
        return [
            PluginMenuItem(
                _("Create Alias"),
                endpoint,
                action="modal",
                attributes={"cms-icon": "alias"},
            ),
        ]

    @classmethod
    def get_extra_placeholder_menu_items(cls, request, placeholder):
        data = {
            "placeholder": placeholder.pk,
            "language": get_language_from_request(request, check_path=True),
        }
        endpoint = add_url_parameters(admin_reverse(CREATE_ALIAS_URL_NAME), **data)

        menu_items = [
            PluginMenuItem(
                _("Create Alias"),
                endpoint,
                action="modal",
                attributes={"cms-icon": "alias"},
            ),
        ]
        return menu_items

    @classmethod
    def can_create_alias(cls, user, plugins=None, replace=False):
        if not user.has_perm(
            get_model_permission_codename(AliasModel, "add"),
        ):
            return False

        if not plugins:
            return True
        elif replace:
            target_placeholder = plugins[0].placeholder
            if not target_placeholder.check_source(user) or not has_plugin_permission(user, Alias.__name__, "add"):
                return False

        return all(
            has_plugin_permission(
                user,
                plugin.plugin_type,
                "add",
            )
            for plugin in plugins
        )

    @classmethod
    def can_detach(cls, user, target_placeholder, plugins):
        return all(
            has_plugin_permission(
                user,
                plugin.plugin_type,
                "add",
            )
            for plugin in plugins
        ) and target_placeholder.check_source(user)

    @classmethod
    def detach_alias_plugin(cls, plugin, language):
        source_plugins = plugin.alias.get_plugins(language, show_draft_content=True)  # We're in edit mode
        target_placeholder = plugin.placeholder
        plugin_position = plugin.position
        plugin_parent = plugin.parent
        target_placeholder.delete_plugin(plugin)
        if source_plugins:
            if target_last_plugin := target_placeholder.get_last_plugin(plugin.language):
                target_placeholder._shift_plugin_positions(
                    language,
                    start=plugin_position,
                    offset=len(source_plugins) + target_last_plugin.position + 1,  # enough space to shift back
                )

            return copy_plugins_to_placeholder(
                source_plugins,
                placeholder=target_placeholder,
                language=language,
                root_plugin=plugin_parent,
                start_positions={language: plugin_position},
            )
        return []
