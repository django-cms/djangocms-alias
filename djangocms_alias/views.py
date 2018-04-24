import json

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import get_language_from_request
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from cms.toolbar.utils import get_plugin_toolbar_info, get_plugin_tree_as_json
from cms.utils.permissions import has_plugin_permission

from .cms_plugins import Alias
from .constants import (
    CHANGE_ALIAS_POSITION_URL_NAME,
    DRAFT_ALIASES_SESSION_KEY,
)
from .forms import BaseCreateAliasForm, CreateAliasForm
from .models import Alias as AliasModel
from .models import AliasPlugin, Category
from .utils import alias_plugin_reverse


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
    use_draft = request.session.get(DRAFT_ALIASES_SESSION_KEY)

    plugins = instance.alias.get_plugins(language, use_draft)

    can_detach = Alias.can_detach(request.user, plugins)

    if not can_detach:
        raise PermissionDenied

    copied_plugins = Alias.detach_alias_plugin(
        plugin=instance,
        language=language,
        use_draft=use_draft,
    )

    return render_replace_response(
        request,
        new_plugins=copied_plugins,
        source_plugin=instance,
    )


class AliasDetailView(DetailView):
    model = AliasModel
    context_object_name = 'alias'
    queryset = AliasModel.objects.all()
    template_name = 'djangocms_alias/alias_detail.html'

    def get_context_data(self, **kwargs):
        kwargs.update({
            'use_draft': self.request.toolbar.edit_mode_active,
        })
        return super().get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.request.toolbar.set_object(self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


def delete_alias_view(request, pk, *args, **kwargs):
    from djangocms_alias.admin import AliasAdmin

    response = AliasAdmin(
        model=AliasModel,
        admin_site=admin.site,
    ).delete_view(request, pk)

    if request.POST and response.status_code == 200:
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
            'use_draft': self.request.toolbar.edit_mode_active,
            'category': self.category,
            'ajax_set_alias_position_url': alias_plugin_reverse(
                CHANGE_ALIAS_POSITION_URL_NAME,
            ),
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
    queryset = Category.objects.order_by('name')
    template_name = 'djangocms_alias/category_list.html'

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

    if not Alias.can_create_alias(user, plugins):
        raise PermissionDenied

    replace = create_form.cleaned_data.get('replace')

    if replace and not has_plugin_permission(user, Alias.__name__, 'add'):
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

        plugins = [root] + list(root.get_descendants().order_by('path'))

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
def publish_alias_view(request, pk, language):
    if not request.user.is_staff:
        raise PermissionDenied

    alias = get_object_or_404(AliasModel, pk=pk)
    alias.publish(language)
    return HttpResponse(JAVASCRIPT_SUCCESS_RESPONSE)


@require_POST
def set_alias_draft_mode_view(request):
    if not request.user.is_staff:
        raise PermissionDenied

    try:
        request.session[DRAFT_ALIASES_SESSION_KEY] = bool(int(
            request.POST.get('enable'),
        ))
    except ValueError:
        return HttpResponseBadRequest('Form received unexpected values')

    return HttpResponse(JAVASCRIPT_SUCCESS_RESPONSE)


@require_POST
@transaction.atomic
def change_alias_position_view(request):
    if not request.user.is_staff:
        raise PermissionDenied

    try:
        alias_id = int(request.POST.get('alias_id', '-'))
    except ValueError:
        return JsonResponse(
            {
                'error':
                '\'alias_id\' is a required parameter and has to be integer.'
            },
            status=400,
        )

    try:
        position = int(request.POST.get('position', '-'))
    except ValueError:
        return JsonResponse(
            {
                'error':
                '\'position\' is a required parameter and has to be integer.'
            },
            status=400,
        )

    try:
        alias = AliasModel.objects.get(pk=alias_id)
    except AliasModel.DoesNotExist:
        return JsonResponse(
            {'error': 'Alias with that id doesn\'t exist.'},
            status=400,
        )

    try:
        alias.change_position(position)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    response_data = {'alias_id': alias_id, 'position': position}
    return JsonResponse(response_data)
