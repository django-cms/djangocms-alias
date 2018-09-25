import json
import operator

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import (
    get_language_from_request,
    ugettext_lazy as _,
)
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from cms.models import Page
from cms.toolbar.utils import get_plugin_toolbar_info, get_plugin_tree_as_json
from cms.utils.i18n import get_current_language

from .cms_plugins import Alias
from .forms import BaseCreateAliasForm, CreateAliasForm, SetAliasPositionForm
from .models import Alias as AliasModel, AliasPlugin, Category


JAVASCRIPT_SUCCESS_RESPONSE = """
    <div><div class="messagelist">
    <div class="success"></div>
    </div></div>
"""


def detach_alias_plugin_view(request, plugin_pk):
    if not request.user.is_staff:
        raise PermissionDenied

    instance = get_object_or_404(AliasPlugin, pk=plugin_pk)

    if request.method == 'GET':
        opts = Alias.model._meta
        context = {
            'has_change_permission': True,
            'opts': opts,
            'root_path': reverse('admin:index'),
            'is_popup': True,
            'app_label': opts.app_label,
            'object_name': _('Alias'),
            'object': instance.alias,
        }
        return render(request, 'djangocms_alias/detach_alias.html', context)

    language = get_language_from_request(request, check_path=True)

    plugins = instance.alias.get_plugins(language)

    can_detach = Alias.can_detach(request.user, instance.placeholder, plugins)

    if not can_detach:
        raise PermissionDenied

    copied_plugins = Alias.detach_alias_plugin(
        plugin=instance,
        language=language,
    )

    return render_replace_response(
        request,
        new_plugins=copied_plugins,
        source_plugin=instance,
    )


def delete_alias_view(request, pk, *args, **kwargs):
    from djangocms_alias.admin import AliasAdmin

    alias_admin = AliasAdmin(
        model=AliasModel,
        admin_site=admin.site,
    )
    response = alias_admin.delete_view(request, pk)
    if request.POST and response.status_code in [200, 302]:
        return HttpResponse(JAVASCRIPT_SUCCESS_RESPONSE)
    return response


class AliasListView(ListView):
    model = AliasModel
    context_object_name = 'aliases'
    template_name = 'djangocms_alias/alias_list.html'

    def get_queryset(self):
        return self.category.aliases.all()

    def get_context_data(self, **kwargs):
        kwargs.update({
            'category': self.category,
        })
        return super().get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        self.category = get_object_or_404(
            Category,
            pk=self.kwargs['category_pk'],
        )
        return super().dispatch(request, *args, **kwargs)


class CategoryListView(ListView):
    model = Category
    context_object_name = 'categories'
    template_name = 'djangocms_alias/category_list.html'

    def get_queryset(self):
        qs = Category.objects.active_translations()
        # Using `order_by('translations__name')` results in duplicated QuerySet
        # values.
        return sorted(qs, key=operator.attrgetter('name'))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def create_alias_view(request):
    if not request.user.is_staff:
        raise PermissionDenied

    form = BaseCreateAliasForm(request.GET or None)

    if form.is_valid():
        initial_data = form.cleaned_data
    else:
        initial_data = None

    if request.method == 'GET' and not form.is_valid():
        return HttpResponseBadRequest('Form received unexpected values')

    user = request.user

    create_form = CreateAliasForm(
        request.POST or None,
        initial=initial_data,
        user=user,
    )

    if not create_form.is_valid():
        opts = Alias.model._meta
        context = {
            'form': create_form,
            'has_change_permission': True,
            'opts': opts,
            'root_path': reverse('admin:index'),
            'is_popup': True,
            'app_label': opts.app_label,
            'media': (Alias().media + create_form.media),
        }
        return render(request, 'djangocms_alias/create_alias.html', context)

    plugins = create_form.get_plugins()

    if not plugins:
        return HttpResponseBadRequest(
            'Plugins are required to create an alias',
        )

    replace = create_form.cleaned_data.get('replace')
    if not Alias.can_create_alias(user, plugins, replace):
        raise PermissionDenied

    alias_plugin = create_form.save()

    if replace:
        plugin = create_form.cleaned_data.get('plugin')
        placeholder = create_form.cleaned_data.get('placeholder')
        return render_replace_response(
            request,
            new_plugins=[alias_plugin],
            source_placeholder=placeholder,
            source_plugin=plugin,
        )

    return HttpResponse(JAVASCRIPT_SUCCESS_RESPONSE)


def render_replace_response(request, new_plugins, source_placeholder=None,
                            source_plugin=None):
    move_plugins, add_plugins = [], []
    for plugin in new_plugins:
        root = plugin.parent.get_bound_plugin() if plugin.parent else plugin

        plugins = [root] + list(root.get_descendants())

        plugin_order = plugin.placeholder.get_plugin_tree_order(
            plugin.language,
            parent_id=plugin.parent_id,
        )
        plugin_tree = get_plugin_tree_as_json(request, plugins)
        move_data = get_plugin_toolbar_info(plugin)
        move_data['plugin_order'] = plugin_order
        move_data.update(json.loads(plugin_tree))
        move_plugins.append(json.dumps(move_data))
        add_plugins.append((
            json.dumps(get_plugin_toolbar_info(plugin)),
            plugin_tree,
        ))
    context = {
        'added_plugins': add_plugins,
        'moved_plugins': move_plugins,
        'is_popup': True,
    }
    if source_plugin is not None:
        context['replaced_plugin'] = json.dumps(
            get_plugin_toolbar_info(source_plugin),
        )
    if source_placeholder is not None:
        context['replaced_placeholder'] = json.dumps({
            'placeholder_id': source_placeholder.pk,
            'deleted': True,
        })
    return render(request, 'djangocms_alias/alias_replace.html', context)


@require_POST
@transaction.atomic
def set_alias_position_view(request):
    if not request.user.is_staff:
        raise PermissionDenied

    form = SetAliasPositionForm(request.POST or None)

    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    alias = form.save()
    return JsonResponse({'alias': alias.pk, 'position': alias.position})


class AliasSelect2View(ListView):
    queryset = AliasModel.objects.order_by('category__translations__name', 'position')

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {
                    'text': str(obj),
                    'id': obj.pk,
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next(),
        })

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Showing published and unpublished aliases
        queryset = super().get_queryset().filter(
            contents__language=get_current_language(),
        ).distinct()
        term = self.request.GET.get('term')
        category = self.request.GET.get('category')
        try:
            pk = int(self.request.GET.get('pk'))
        except (TypeError, ValueError):
            pk = None
        q = Q()
        if term:
            q &= Q(contents__name__icontains=term)
        if category:
            q &= Q(category=category)
        if pk:
            q &= Q(pk=pk)
        return queryset.filter(q)

    def get_paginate_by(self, queryset):
        return self.request.GET.get('limit', 30)


def alias_usage_view(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied

    alias = get_object_or_404(AliasModel.objects.all(), pk=pk)
    opts = Alias.model._meta
    title = _('Objects using alias: {}'.format(alias))
    context = {
        'has_change_permission': True,
        'opts': opts,
        'root_path': reverse('admin:index'),
        'is_popup': True,
        'app_label': opts.app_label,
        'object_name': _('Alias'),
        'object': alias,
        'title': title,
        'original': title,
        'show_back_btn': request.GET.get('back'),
        'objects_list': sorted(
            alias.objects_using,
            # First show Pages on list
            key=lambda obj: isinstance(obj, Page),
            reverse=True,
        ),
    }
    return render(request, 'djangocms_alias/alias_usage.html', context)
