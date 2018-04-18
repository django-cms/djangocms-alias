import json

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils.translation import get_language_from_request
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView, DetailView, ListView

from cms.toolbar.utils import get_plugin_toolbar_info, get_plugin_tree_as_json

from .cms_plugins import Alias
from .constants import DRAFT_ALIASES_SESSION_KEY
from .forms import BaseCreateAliasForm, CreateAliasForm, DetachAliasPluginForm
from .models import Alias as AliasModel
from .models import Category


def detach_alias_plugin_view(request):
    if not request.user.is_staff:
        raise PermissionDenied

    form = DetachAliasPluginForm(request.POST)

    if request.method == 'GET' or not form.is_valid():
        return HttpResponseBadRequest('Form received unexpected values')

    plugin = form.cleaned_data['plugin']
    instance = plugin.get_bound_plugin()
    language = form.cleaned_data['language']

    if not Alias.can_detach(
        request.user,
        instance.alias.draft_content.get_plugins(language),
    ):
        raise PermissionDenied

    Alias.detach_alias_plugin(
        plugin=instance,
        language=language,
        use_draft=form.cleaned_data.get('use_draft'),
    )

    return HttpResponse(
        '<div><div class="messagelist">'
        '<div class="success"></div>'
        '</div></div>'
    )


class AliasDetailView(DetailView):
    model = AliasModel
    context_object_name = 'alias'
    queryset = AliasModel.objects.all()
    template_name = 'djangocms_alias/alias_detail.html'

    def get_context_data(self, **kwargs):
        kwargs.update({
            'use_draft': 'preview' not in self.request.GET,
        })
        return super().get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AliasDeleteView(DeleteView):
    model = AliasModel

    def get_success_url(self):
        # redirectiong to success_url was handled by PluginMenuItem and cms
        # frontend
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = kwargs['object']

        context = dict(
            title=obj.name,
            object_name=_('Alias'),
            object=obj,
            pages_using_alias=obj.pages_using_this_alias,
            has_perm=self.has_perm_to_delete(self.request, obj)
        )
        return context

    def has_perm_to_delete(self, request, obj=None):
        if not obj:
            return False
        return Alias.can_delete_alias(request.user, obj)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.has_perm_to_delete(request, self.object):
            raise PermissionDenied

        Alias.delete_alias(self.object)

        # redirectiong to success_url was handled by PluginMenuItem and cms
        # frontend
        return HttpResponse(
            '<div><div class="messagelist">'
            '<div class="success"></div>'
            '</div></div>'
        )


class AliasListView(ListView):
    model = AliasModel
    context_object_name = 'aliases'
    template_name = 'djangocms_alias/alias_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(
            category_id=self.kwargs['category_pk'],
        )

    def get_context_data(self, **kwargs):
        kwargs.update({
            'category': get_object_or_404(
                Category,
                pk=self.kwargs['category_pk'],
            ),
        })
        return super().get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
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
    can_replace = Alias.can_replace_with_alias(user)

    create_form = CreateAliasForm(
        request.POST or None,
        initial=initial_data,
        can_replace=can_replace,
    )
    create_form.set_category_widget(request)

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
        return render(
            request,
            'djangocms_alias/create_alias.html',
            context,
        )

    plugins = create_form.get_plugins()

    if not plugins:
        return HttpResponseBadRequest(
            'Plugins are required to create an alias',
        )

    if not Alias.can_create_alias(user, plugins):
        raise PermissionDenied

    replace = create_form.cleaned_data.get('replace')

    if replace and not can_replace:
        raise PermissionDenied

    alias = Alias.create_alias(
        name=create_form.cleaned_data.get('name'),
        category=create_form.cleaned_data.get('category'),
    )
    if replace:
        plugin = create_form.cleaned_data.get('plugin')
        placeholder = create_form.cleaned_data.get('placeholder')
        language = get_language_from_request(request, use_path=True)
        if plugin:
            new_plugin = Alias.replace_plugin_with_alias(
                plugin,
                alias,
                language=language,
            )
        else:
            new_plugin = Alias.replace_placeholder_content_with_alias(
                placeholder,
                alias,
                language=language,
            )
        return render_replace_response(
            request,
            new_plugin=new_plugin,
            source_placeholder=placeholder,
            source_plugin=plugin,
        )
    else:
        Alias.populate_alias(alias, plugins)

    return HttpResponse(
        '<div><div class="messagelist">'
        '<div class="success"></div>'
        '</div></div>'
    )


def render_replace_response(
    request,
    new_plugin,
    source_placeholder=None,
    source_plugin=None,
):
    try:
        root = (
            new_plugin.parent.get_bound_plugin()
            if new_plugin.parent else new_plugin
        )
    except ObjectDoesNotExist:
        root = new_plugin

    plugins = [root] + list(root.get_descendants().order_by('path'))

    move_data = get_plugin_toolbar_info(new_plugin)
    move_data['plugin_order'] = new_plugin.placeholder.get_plugin_tree_order(  # noqa: E501
        new_plugin.language,
        parent_id=new_plugin.parent_id,
    )
    plugin_tree = get_plugin_tree_as_json(
        request,
        plugins,
    )
    move_data.update(json.loads(plugin_tree))
    context = {
        'added_plugin': json.dumps(get_plugin_toolbar_info(new_plugin)),
        'added_plugin_structure': plugin_tree,
        'move_data': json.dumps(move_data),
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
    return render(
        request,
        'djangocms_alias/alias_replace.html',
        context,
    )


def publish_alias_view(request, pk, language):
    if not request.user.is_staff:
        raise PermissionDenied

    if request.method != 'POST':
        return HttpResponseBadRequest('Requires POST method')

    alias = get_object_or_404(AliasModel, pk=pk)
    Alias.publish_alias(alias, language)
    return HttpResponse(
        '<div><div class="messagelist">'
        '<div class="success"></div>'
        '</div></div>'
    )


def set_alias_draft_mode_view(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Requires POST method')

    request.session[DRAFT_ALIASES_SESSION_KEY] = bool(
        request.POST.get('enable'),
    )

    return HttpResponse(
        '<div><div class="messagelist">'
        '<div class="success"></div>'
        '</div></div>'
    )
