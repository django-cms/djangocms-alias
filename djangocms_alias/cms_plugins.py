from django.middleware.csrf import get_token
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

from cms.api import add_plugin
from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.utils.permissions import (
    get_model_permission_codename,
    has_plugin_permission,
)
from cms.utils.plugins import copy_plugins_to_placeholder, reorder_plugins

from .constants import (
    CREATE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    DRAFT_ALIASES_QUERY_KEY,
)
from .models import Alias as AliasModel
from .models import AliasPlugin
from .utils import alias_plugin_reverse


__all__ = [
    'Alias',
]


@plugin_pool.register_plugin
class Alias(CMSPluginBase):
    name = _('Alias')
    model = AliasPlugin
    render_template = 'djangocms_alias/alias.html'

    def render(self, context, instance, placeholder):
        context.setdefault(
            'alias_draft',
            DRAFT_ALIASES_QUERY_KEY in context['request'].GET,
        )
        return super().render(context, instance, placeholder)

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        if plugin.plugin_type == cls.__name__:
            edit_endpoint = alias_plugin_reverse(
                DETAIL_ALIAS_URL_NAME,
                args=[plugin.alias_id],
            )

            return [
                PluginMenuItem(
                    _("Edit Alias"),
                    edit_endpoint,
                    action='??',  # TODO get a hold of proper value here
                    attributes={
                        'icon': 'alias',
                    },
                ),
                PluginMenuItem(
                    _("Detach Alias"),
                    alias_plugin_reverse(DETACH_ALIAS_PLUGIN_URL_NAME),
                    data={
                        'plugin': plugin.pk,
                        'csrfmiddlewaretoken': get_token(request),
                        'draft': DRAFT_ALIASES_QUERY_KEY in request.GET,
                        'language': get_language(),
                    },
                    attributes={
                        'icon': 'alias',
                    },
                ),
            ]

        data = {'plugin': plugin.pk}
        endpoint = alias_plugin_reverse(CREATE_ALIAS_URL_NAME, parameters=data)
        return [
            PluginMenuItem(
                _("Create Alias"),
                endpoint,
                action='modal',
                attributes={
                    'icon': 'alias',
                },
            ),
        ]

    @classmethod
    def get_extra_placeholder_menu_items(cls, request, placeholder):
        data = {'placeholder': placeholder.pk}
        endpoint = alias_plugin_reverse(CREATE_ALIAS_URL_NAME, parameters=data)
        return [
            PluginMenuItem(
                _("Create Alias"),
                endpoint,
                action='modal',
                attributes={
                    'icon': 'alias',
                },
            ),
        ]

    @classmethod
    def create_alias(cls, name, category):
        alias = AliasModel.objects.create(
            name=name,
            category=category,
        )
        return alias

    @classmethod
    def populate_alias(cls, alias, plugins):
        copy_plugins_to_placeholder(
            plugins,
            placeholder=alias.draft_content,
        )

    @classmethod
    def move_plugin(cls, plugin, target_placeholder, language):
        plugin_data = {
            'placeholder': target_placeholder,
            'language': language,
        }
        plugin.update(refresh=True, **plugin_data)
        plugin.get_descendants().update(**plugin_data)

    @classmethod
    def replace_plugin_with_alias(cls, plugin, alias, language):
        cls.move_plugin(plugin, alias.draft_content, language)

        new_plugin = add_plugin(
            plugin.placeholder,
            cls.__name__,
            target=plugin,
            position='left',
            language=language,
            alias=alias,
        )
        new_plugin.position = plugin.position
        new_plugin.save(update_fields=['position'])
        return new_plugin

    @classmethod
    def replace_placeholder_content_with_alias(
        cls,
        placeholder,
        alias,
        language,
    ):
        for plugin in placeholder.get_plugins(language):
            cls.move_plugin(plugin, alias.draft_content, language)
        return add_plugin(
            placeholder,
            cls.__name__,
            alias=alias,
            language=language,
        )

    @classmethod
    def can_create_alias(cls, user, plugins):
        if not user.has_perm(
            get_model_permission_codename(AliasModel, 'add'),
        ):
            return False

        return all(
            has_plugin_permission(
                user,
                plugin.plugin_type,
                'add',
            ) for plugin in plugins
        )

    @classmethod
    def can_replace_with_alias(cls, user):
        return has_plugin_permission(user, cls.__name__, 'add')

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
    def detach_alias_plugin(cls, plugin, language, draft=False):
        if draft:
            source_placeholder = plugin.alias.draft_content
        else:
            source_placeholder = plugin.alias.live_content
        target_placeholder = plugin.placeholder

        order = target_placeholder.get_plugin_tree_order(language)

        source_plugins = source_placeholder.get_plugins(language)
        copied_plugins = copy_plugins_to_placeholder(
            source_plugins,
            placeholder=target_placeholder,
        )
        pk_map = {
            source.pk: copy.pk
            for (source, copy) in zip(source_plugins, copied_plugins)
        }

        source_order = source_placeholder.get_plugin_tree_order(language)

        target_pos = order.index(plugin.pk)
        order[target_pos:target_pos + 1] = [pk_map[pk] for pk in source_order]

        plugin.delete()

        reorder_plugins(
            target_placeholder,
            language=language,
            order=order,
            parent_id=plugin.parent_id,
        )

    @classmethod
    def publish_alias(cls, alias, language):
        alias.live_content.clear(language=language)
        copy_plugins_to_placeholder(
            alias.draft_content.get_plugins(language=language),
            placeholder=alias.live_content,
        )
