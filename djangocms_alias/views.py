import json

from cms.toolbar.utils import get_plugin_toolbar_info
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import (
    get_language,
)
from django.views.generic import ListView

from .models import Alias, Category

try:
    from cms.toolbar.utils import get_plugin_tree
except ImportError:
    from cms.toolbar.utils import get_plugin_tree_as_json

    def get_plugin_tree(request, plugins):
        """
        Fallback for older versions of django CMS
        """
        return json.loads(get_plugin_tree_as_json(request, plugins))


def render_replace_response(request, new_plugins, source_placeholder=None, source_plugin=None):
    move_plugins, add_plugins = [], []
    for plugin in new_plugins:
        root = plugin.parent.get_bound_plugin() if plugin.parent else plugin

        plugins = [root] + list(root.get_descendants())

        plugin_order = plugin.placeholder.get_plugin_tree_order(
            plugin.language,
            parent_id=plugin.parent_id,
        )
        plugin_tree = get_plugin_tree(request, plugins)
        move_data = get_plugin_toolbar_info(plugin)
        move_data["plugin_order"] = plugin_order
        move_data.update(plugin_tree)
        move_plugins.append(json.dumps(move_data))
        add_plugins.append(
            (
                json.dumps(get_plugin_toolbar_info(plugin)),
                json.dumps(plugin_tree),
            )
        )
    context = {
        "added_plugins": add_plugins,
        "moved_plugins": move_plugins,
        "is_popup": True,
    }
    if source_plugin is not None:
        context["replaced_plugin"] = json.dumps(
            get_plugin_toolbar_info(source_plugin),
        )
    if source_placeholder is not None:
        context["replaced_placeholder"] = json.dumps(
            {
                "placeholder_id": source_placeholder.pk,
                "deleted": True,
            }
        )
    return render(request, "djangocms_alias/alias_replace.html", context)


class CategorySelect2View(ListView):
    queryset = Category.objects.order_by("translations__name")

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse(
            {
                "results": [
                    {
                        "text": str(obj),
                        "id": obj.pk,
                    }
                    for obj in context["object_list"]
                ],
                "more": context["page_obj"].has_next(),
            }
        )

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Only show Categories that have an Alias attached.
        If site is selected, use that to filter further.
        """
        term = self.request.GET.get("term")
        site = self.request.GET.get("site")
        queryset = super().get_queryset()
        # Only get categories that have aliases attached
        queryset = queryset.filter(aliases__isnull=False)

        try:
            pk = int(self.request.GET.get("pk"))
        except (TypeError, ValueError):
            pk = None

        q = Q()
        if term:
            q &= Q(translations__name__icontains=term)
        if site:
            q &= Q(aliases__site=site) | Q(aliases__site=None)
        if pk:
            q &= Q(pk=pk)

        return queryset.translated(get_language()).filter(q).distinct()

    def get_paginate_by(self, queryset):
        return self.request.GET.get("limit", 30)


class AliasSelect2View(ListView):
    queryset = Alias.objects.order_by("category__translations__name", "position")

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse(
            {
                "results": [
                    {
                        "text": str(obj),
                        "id": obj.pk,
                    }
                    for obj in context["object_list"]
                ],
                "more": context["page_obj"].has_next(),
            }
        )

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        term = self.request.GET.get("term")
        category = self.request.GET.get("category")
        site = self.request.GET.get("site")
        # Showing published and unpublished aliases
        queryset = (
            super()
            .get_queryset()
            .filter(
                contents__language=get_language(),
            )
            .distinct()
        )

        try:
            pk = int(self.request.GET.get("pk"))
        except (TypeError, ValueError):
            pk = None

        q = Q()
        if term:
            q &= Q(contents__name__icontains=term)
        if category:
            q &= Q(category=category)
        if site:
            q &= Q(site=site) | Q(site=None)
        if pk:
            q &= Q(pk=pk)

        return queryset.filter(q).distinct()

    def get_paginate_by(self, queryset):
        return self.request.GET.get("limit", 30)
