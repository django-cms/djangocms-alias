from cms.models import Page
from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.toolbar.utils import get_object_edit_url, get_plugin_toolbar_info, get_plugin_tree
from cms.utils import get_language_from_request
from cms.utils.permissions import (
    get_model_permission_codename,
    has_plugin_permission,
)
from cms.utils.plugins import copy_plugins_to_placeholder
from cms.utils.urlutils import add_url_parameters, admin_reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import (
    gettext_lazy as _,
)

from djangocms_alias import constants
from djangocms_alias.utils import emit_content_change

from . import views
from .constants import CREATE_ALIAS_URL_NAME, DETACH_ALIAS_PLUGIN_URL_NAME
from .forms import AliasPluginForm, BaseCreateAliasForm, CreateAliasForm
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

    create_alias_fieldset = (
        (
            None,
            {
                "fields": (
                    "name",
                    "site",
                    "category",
                    "replace",
                    "plugin",
                    "placeholder",
                    "language",
                ),
            },
        ),
    )

    autocomplete_fields = ["alias"]

    def get_render_template(self, context, instance, placeholder):
        if isinstance(instance.placeholder.source, AliasContent) and instance.is_recursive():
            return "djangocms_alias/alias_recursive.html"
        return f"djangocms_alias/{instance.template}/alias.html"

    @classmethod
    def _get_allowed_root_plugins(cls):
        if not hasattr(cls, "_cached_allowed_root_plugins"):
            cls._cached_allowed_root_plugins = set(plugin_pool.get_all_plugins(root_plugin=True))
        return cls._cached_allowed_root_plugins

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        if plugin.plugin_type == cls.__name__:
            alias_content = plugin.alias.get_content(show_draft_content=True)
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
            "language": get_language_from_request(request),
        }
        # Check if the plugin can become root: Should be allowed as a root plugin (in the alias)
        can_become_alias = plugin.get_plugin_class() in cls._get_allowed_root_plugins()
        if can_become_alias:
            endpoint = add_url_parameters(admin_reverse(CREATE_ALIAS_URL_NAME), **data)
            return [
                PluginMenuItem(
                    _("Create Alias"),
                    endpoint,
                    action="modal",
                    attributes={"cms-icon": "alias"},
                ),
            ]
        return []

    @classmethod
    def get_extra_placeholder_menu_items(cls, request, placeholder):
        data = {
            "placeholder": placeholder.pk,
            "language": get_language_from_request(request),
        }
        endpoint = add_url_parameters(admin_reverse(CREATE_ALIAS_URL_NAME), **data)

        if placeholder.cmsplugin_set.exists():
            return [
                PluginMenuItem(
                    _("Create Alias"),
                    endpoint,
                    action="modal",
                    attributes={"cms-icon": "alias"},
                ),
            ]
        return []

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

    def get_plugin_urls(self):
        return super().get_plugin_urls() + [
            path(
                "create-alias/",
                self.create_alias_view,
                name=constants.CREATE_ALIAS_URL_NAME,
            ),
            path(
                "aliases/<int:pk>/usage/",
                self.alias_usage_view,
                name=constants.USAGE_ALIAS_URL_NAME,
            ),
            path(
                "detach-alias/<int:plugin_pk>/",
                self.detach_alias_plugin_view,
                name=constants.DETACH_ALIAS_PLUGIN_URL_NAME,
            ),
            path(
                "select2/",
                views.AliasSelect2View.as_view(),
                name=constants.SELECT2_ALIAS_URL_NAME,
            ),
            path(
                "category-select2/",
                views.CategorySelect2View.as_view(),
                name=constants.CATEGORY_SELECT2_URL_NAME,
            ),
        ]

    def create_alias_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied

        form = BaseCreateAliasForm(request.GET or None)

        initial_data = form.cleaned_data if form.is_valid() else None
        if request.method == "GET" and not form.is_valid():
            return HttpResponseBadRequest("Form received unexpected values")

        user = request.user

        create_form = CreateAliasForm(
            request.POST or None,
            initial=initial_data,
            user=user,
        )

        if not create_form.is_valid():
            from django.contrib import admin

            fieldsets = self.create_alias_fieldset
            admin_form = admin.helpers.AdminForm(create_form, fieldsets, {})
            self.opts = self.model._meta
            self.admin_site = admin.site
            context = {
                "title": _("Create Alias"),
                "adminform": admin_form,
                "is_popup": True,
                "media": admin_form.media,
                "errors": create_form.errors,
                "preserved_filters": self.get_preserved_filters(request),
                "inline_admin_formsets": [],
            }
            return self.render_change_form(
                request,
                context,
                add=True,
                change=False,
                obj=None,
            )

        plugins = create_form.get_plugins()

        if not plugins:
            return HttpResponseBadRequest(
                "Plugins are required to create an alias",
            )

        replace = create_form.cleaned_data.get("replace")
        if not Alias.can_create_alias(user, plugins, replace):
            raise PermissionDenied

        alias, alias_content, alias_plugin = create_form.save()
        emit_content_change([alias_content])

        if replace:
            plugin = create_form.cleaned_data.get("plugin")
            placeholder = create_form.cleaned_data.get("placeholder")
            return self.render_replace_response(
                request,
                new_plugins=[alias_plugin],
                source_placeholder=placeholder,
                source_plugin=plugin,
            )
        return TemplateResponse(request, "admin/cms/page/close_frame.html")

    def detach_alias_plugin_view(self, request, plugin_pk):
        if not request.user.is_staff:
            raise PermissionDenied

        instance = get_object_or_404(AliasPlugin, pk=plugin_pk)

        if request.method == "GET":
            opts = self.model._meta
            context = {
                "title": _("Detach Alias"),
                "has_change_permission": True,
                "opts": opts,
                "root_path": admin_reverse("index"),
                "is_popup": True,
                "app_label": opts.app_label,
                "object_name": _("Alias"),
                "object": instance.alias,
            }
            return TemplateResponse(request, "djangocms_alias/detach_alias.html", context)

        language = get_language_from_request(request)

        plugins = instance.alias.get_plugins(language, show_draft_content=True)
        can_detach = self.can_detach(request.user, instance.placeholder, plugins)

        if not can_detach:
            raise PermissionDenied

        copied_plugins = self.detach_alias_plugin(
            plugin=instance,
            language=language,
        )

        return self.render_replace_response(
            request,
            new_plugins=copied_plugins,
            source_plugin=instance,
        )

    def render_replace_response(self, request, new_plugins, source_placeholder=None, source_plugin=None):
        move_plugins, add_plugins = [], []
        for plugin in new_plugins:
            root = plugin.parent.get_bound_plugin() if plugin.parent else plugin

            plugins = [root] + list(root.get_descendants())

            plugin_order = plugin.placeholder.get_plugin_tree_order(
                plugin.language,
                parent_id=plugin.parent_id,
            )
            plugin_tree = get_plugin_tree(request, plugins, target_plugin=root)
            move_data = get_plugin_toolbar_info(plugin)
            move_data["plugin_order"] = plugin_order
            move_data.update(plugin_tree)
            move_plugins.append(move_data)
            add_plugins.append({**get_plugin_toolbar_info(plugin), "structure": plugin_tree})
        data = {
            "addedPlugins": add_plugins,
            "movedPlugins": move_plugins,
            "is_popup": True,
        }
        if source_plugin and source_plugin.pk:
            data["replacedPlugin"] = get_plugin_toolbar_info(source_plugin)
        if source_placeholder and source_placeholder.pk:
            data["replacedPlaceholder"] = {
                "placeholder_id": source_placeholder.pk,
                "deleted": True,
            }
        return self.render_close_frame(request, obj=None, action="ALIAS_REPLACE", extra_data=data)

    def alias_usage_view(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied

        alias = get_object_or_404(AliasModel, pk=pk)
        opts = AliasModel._meta
        title = _(f"Objects using alias: {alias}")
        context = {
            "has_change_permission": True,
            "opts": opts,
            "root_path": admin_reverse("index"),
            "is_popup": True,
            "app_label": opts.app_label,
            "object_name": _("Alias"),
            "object": alias,
            "title": title,
            "original": title,
            "show_back_btn": request.GET.get("back"),
            "objects_list": sorted(
                alias.objects_using,
                # First show Pages on list
                key=lambda obj: isinstance(obj, Page),
                reverse=True,
            ),
        }
        return TemplateResponse(request, "djangocms_alias/alias_usage.html", context)
