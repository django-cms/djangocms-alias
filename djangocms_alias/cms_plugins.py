from django.conf.urls import url
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
)
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    DetailView,
    ListView,
)

from cms.api import add_plugin
from cms.plugin_base import (
    CMSPluginBase,
    PluginMenuItem,
)
from cms.plugin_pool import plugin_pool
from cms.utils.plugins import copy_plugins_to_placeholder

from .constants import (
    CREATE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
)
from .forms import (
    BaseCreateAliasForm,
    CreateAliasForm,
    DetachAliasPluginForm,
)
from .models import (
    Alias,
    AliasPluginModel,
    Category,
)
from .utils import alias_plugin_reverse


__all__ = [
    'Alias2Plugin',
]


@plugin_pool.register_plugin
class Alias2Plugin(CMSPluginBase):
    # name = _('Alias')
    model = AliasPluginModel
    render_template = 'djangocms_alias/render_alias.html'

    def get_plugin_urls(self):
        urlpatterns = [
            url(
                r'^create-alias/$',
                self.create_alias_view,
                name=CREATE_ALIAS_URL_NAME,
            ),
            url(
                r'^aliases/$',
                self.alias_list_view,
                name=LIST_ALIASES_URL_NAME,
            ),
            url(
                r'^aliases/(?P<pk>\d+)/$',
                self.alias_detail_view,
                name=DETAIL_ALIAS_URL_NAME,
            ),
            url(
                r'^detach-alias/$',
                self.detach_alias_plugin_view,
                name=DETACH_ALIAS_PLUGIN_URL_NAME,
            ),
        ]
        return urlpatterns

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

    def create_alias_plugin(self, name, category, plugins):
        alias = Alias.objects.create(
            name=name,
            category=category,
        )
        placeholder = alias.placeholder
        copy_plugins_to_placeholder(
            plugins,
            placeholder=placeholder,
        )
        return alias

    def replace_plugin_with_alias(self, plugin, alias, language):
        new_plugin = add_plugin(
            plugin.placeholder,
            self.name,
            target=plugin,
            position='left',  # TODO find out how to reuse plugin's position
            language=plugin.language,
            alias=alias,
        )
        plugin.delete()
        return new_plugin

    def replace_placeholder_content_with_alias(
        self,
        placeholder,
        alias,
        language,
    ):
        placeholder.clear()
        return add_plugin(
            placeholder,
            self.name,
            alias=alias,
            language=language,
        )

    def create_alias_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied

        form = BaseCreateAliasForm(request.GET or None)

        if form.is_valid():
            initial_data = form.cleaned_data
        else:
            initial_data = None

        if request.method == 'GET' and not form.is_valid():
            return HttpResponseBadRequest('Form received unexpected values')

        create_form = CreateAliasForm(
            request.POST or None,
            initial=initial_data,
        )
        create_form.set_category_widget(request)

        if not create_form.is_valid():
            opts = self.model._meta
            context = {
                'form': create_form,
                'has_change_permission': True,
                'opts': opts,
                'root_path': reverse('admin:index'),
                'is_popup': True,
                'app_label': opts.app_label,
                'media': (self.media + create_form.media),
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

        alias = self.create_alias_plugin(
            name=create_form.cleaned_data.get('name'),
            category=create_form.cleaned_data.get('category'),
            plugins=plugins,
        )
        if create_form.cleaned_data.get('replace'):
            plugin = create_form.cleaned_data.get('plugin')
            placeholder = create_form.cleaned_data.get('placeholder')
            language = get_language()
            if plugin:
                new_plugin = self.replace_plugin_with_alias(
                    plugin,
                    alias,
                    language=language,
                )
            elif placeholder:
                new_plugin = self.replace_placeholder_content_with_alias(
                    placeholder,
                    alias,
                    language=language,
                )
            return self.render_close_frame(request, obj=new_plugin)

        return HttpResponse(
            '<div><div class="messagelist">'
            '<div class="success"></div>'
            '</div></div>'
        )

    def alias_detail_view(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied

        view = DetailView.as_view(
            model=Alias,
            context_object_name='alias',
            queryset=Alias.objects.all(),
            template_name='djangocms_alias/alias_detail.html',
        )
        return view(request, pk=pk)

    def alias_list_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied

        queryset = Category.objects.prefetch_related(
            'aliases',
        ).order_by(
            'name',
        )

        view = ListView.as_view(
            model=Category,
            context_object_name='categories',
            queryset=queryset,
            template_name='djangocms_alias/aliases_list.html',
        )

        return view(request)

    def detach_alias_plugin_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied

        form = DetachAliasPluginForm(request.POST)

        if request.method == 'GET' or not form.is_valid():
            return HttpResponseBadRequest('Form received unexpected values')

        plugin = form.cleaned_data['plugin']
        instance = plugin.get_plugin_instance()[0]
        copy_plugins_to_placeholder(
            list(instance.alias.placeholder.get_plugins()),
            placeholder=instance.placeholder,
        )
        plugin.delete()

        return HttpResponse(
            '<div><div class="messagelist">'
            '<div class="success"></div>'
            '</div></div>'
        )
