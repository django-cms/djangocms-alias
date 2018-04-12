import json

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.generic import DetailView, ListView

from cms.toolbar.utils import get_plugin_toolbar_info, get_plugin_tree_as_json

from .cms_plugins import Alias
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
    instance = plugin.get_plugin_instance()[0]
    language = get_language()

    if not Alias.can_detach(
        request.user,
        instance.alias.placeholder.get_plugins(language),
    ):
        raise PermissionDenied

    Alias.detach_alias_plugin(
        plugin=instance,
        language=language,
    )

    return HttpResponse(
        '<div><div class="messagelist">'
        '<div class="success"></div>'
        '</div></div>'
    )


def alias_detail_view(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied

    view = DetailView.as_view(
        model=AliasModel,
        context_object_name='alias',
        queryset=AliasModel.objects.all(),
        template_name='djangocms_alias/alias_detail.html',
    )
    return view(request, pk=pk)


def alias_list_view(request):
    if not request.user.is_staff:
        raise PermissionDenied

    queryset = Category.objects.prefetch_related('aliases').order_by('name')  # noqa: E501

    view = ListView.as_view(
        model=Category,
        context_object_name='categories',
        queryset=queryset,
        template_name='djangocms_alias/aliases_list.html',
    )
    return view(request)


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
        language = get_language()
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

    context = {
        'added_plugin': json.dumps(get_plugin_toolbar_info(new_plugin)),
        'added_plugin_structure': get_plugin_tree_as_json(
            request,
            plugins,
        ),
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
