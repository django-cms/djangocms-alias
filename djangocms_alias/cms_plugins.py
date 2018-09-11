from copy import copy

from django.utils.translation import (
    get_language_from_request,
    ugettext_lazy as _,
)

from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.utils.permissions import (
    get_model_permission_codename,
    has_plugin_permission,
)
from cms.utils.plugins import copy_plugins_to_placeholder
from cms.utils.urlutils import add_url_parameters, admin_reverse

from .constants import CREATE_ALIAS_URL_NAME, DETACH_ALIAS_PLUGIN_URL_NAME
from .forms import AliasPluginForm
from .models import Alias as AliasModel, AliasPlugin


__all__ = [
    'Alias',
]


@plugin_pool.register_plugin
class Alias(CMSPluginBase):
    name = _('Alias')
    model = AliasPlugin
    form = AliasPluginForm

    def get_render_template(self, context, instance, placeholder):
        if not instance.is_recursive():
            return 'djangocms_alias/{}/alias.html'.format(instance.template)
        return 'djangocms_alias/alias_recursive.html'

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        if plugin.plugin_type == cls.__name__:
            edit_endpoint = plugin.alias.get_absolute_url()
            detach_endpoint = admin_reverse(
                DETACH_ALIAS_PLUGIN_URL_NAME,
                args=[plugin.pk],
            )

            return [
                PluginMenuItem(
                    _('Edit Alias'),
                    edit_endpoint,
                    action='',
                    attributes={'icon': 'alias'},
                ),
                PluginMenuItem(
                    _('Detach Alias'),
                    detach_endpoint,
                    action='modal',
                    attributes={'icon': 'alias'},
                ),
            ]

        data = {
            'plugin': plugin.pk,
            'language': get_language_from_request(request, check_path=True),
        }
        endpoint = add_url_parameters(admin_reverse(CREATE_ALIAS_URL_NAME), **data)
        return [
            PluginMenuItem(
                _('Create Alias'),
                endpoint,
                action='modal',
                attributes={'icon': 'alias'},
            ),
        ]

    @classmethod
    def get_extra_placeholder_menu_items(cls, request, placeholder):
        data = {
            'placeholder': placeholder.pk,
            'language': get_language_from_request(request, check_path=True),
        }
        endpoint = add_url_parameters(admin_reverse(CREATE_ALIAS_URL_NAME), **data)

        menu_items = [
            PluginMenuItem(
                _('Create Alias'),
                endpoint,
                action='modal',
                attributes={'icon': 'alias'},
            ),
        ]
        return menu_items

    @classmethod
    def can_create_alias(cls, user, plugins=None):
        if not user.has_perm(
            get_model_permission_codename(AliasModel, 'add'),
        ):
            return False

        if plugins is None:
            return True

        return all(
            has_plugin_permission(
                user,
                plugin.plugin_type,
                'add',
            ) for plugin in plugins
        )

    @classmethod
    def can_detach(cls, user, plugins):
        return all(
            has_plugin_permission(
                user,
                plugin.plugin_type,
                'add',
            ) for plugin in plugins
        )

    @classmethod
    def detach_alias_plugin(cls, plugin, language):
        source_placeholder = plugin.alias.get_placeholder(language)
        target_placeholder = plugin.placeholder
        source_plugins = plugin.alias.get_plugins(language)

        # Deleting uses a copy of a plugin to preserve pk on existing
        # ``plugin`` object. This is done due to
        # plugin.get_plugin_toolbar_info requiring a PK in a passed
        # instance.
        source_placeholder.delete_plugin(copy(plugin))
        target_placeholder._shift_plugin_positions(
            language,
            plugin.position,
            offset=target_placeholder.get_last_plugin_position(language),
        )
        copied_plugins = copy_plugins_to_placeholder(
            source_plugins,
            placeholder=target_placeholder,
            language=language,
            start_positions={language: plugin.position},
        )
        return copied_plugins
