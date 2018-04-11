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
from cms.utils.permissions import (
    get_model_permission_codename,
    has_plugin_permission,
)
from cms.utils.plugins import (
    copy_plugins_to_placeholder,
    reorder_plugins,
)

from .constants import (
    CREATE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
)
from .forms import (
    BaseCreateAliasForm,
    CreateAliasForm,
    CreateAliasWithReplaceForm,
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

    @classmethod
    def create_alias(cls, name, category, plugins):
        alias = Alias.objects.create(
            name=name,
            category=category,
        )
        copy_plugins_to_placeholder(
            plugins,
            placeholder=alias.placeholder,
        )
        return alias

    @classmethod
    def replace_plugin_with_alias(cls, plugin, alias, language):
        new_plugin = add_plugin(
            plugin.placeholder,
            cls.__name__,
            target=plugin,
            position='left',
            language=plugin.language,
            alias=alias,
        )
        plugin.delete()
        return new_plugin

    @classmethod
    def replace_placeholder_content_with_alias(
        cls,
        placeholder,
        alias,
        language,
    ):
        placeholder.clear()
        return add_plugin(
            placeholder,
            cls.__name__,
            alias=alias,
            language=language,
        )

    @classmethod
    def can_create_alias(cls, user, plugins):
        if not user.has_perm(
            get_model_permission_codename(Alias, 'add'),
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

        user = request.user

        if self.can_replace_with_alias(user):
            form_class = CreateAliasWithReplaceForm
        else:
            form_class = CreateAliasForm

        create_form = form_class(
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

        if not self.can_create_alias(user, plugins):
            raise PermissionDenied

        replace = create_form.cleaned_data.get('replace')

        if replace and not self.can_replace_with_alias(user):
            raise PermissionDenied

        alias = self.create_alias(
            name=create_form.cleaned_data.get('name'),
            category=create_form.cleaned_data.get('category'),
            plugins=plugins,
        )
        if replace:
            plugin = create_form.cleaned_data.get('plugin')
            language = get_language()
            if plugin:
                new_plugin = self.replace_plugin_with_alias(
                    plugin,
                    alias,
                    language=language,
                )
            else:
                placeholder = create_form.cleaned_data.get('placeholder')
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
        source_placeholder = plugin.alias.placeholder
        target_placeholder = plugin.placeholder

        order = target_placeholder.get_plugin_tree_order(language=language)

        source_plugins = list(plugin.alias.placeholder.get_plugins())
        copied_plugins = copy_plugins_to_placeholder(
            source_plugins,
            placeholder=target_placeholder,
        )
        pk_map = {
            source.pk: copy.pk
            for (source, copy) in zip(source_plugins, copied_plugins)
        }

        source_order = source_placeholder.get_plugin_tree_order(
            language=language,
        )

        index = order.index(plugin.pk)
        plugin.delete()
        order[index:index + 1] = [pk_map[pk] for pk in source_order]

        plugin_map = {
            plugin.pk: plugin
            for plugin in target_placeholder.get_plugins()
        }

        reorder_plugins(
            target_placeholder,
            language=language,
            order=order,
            parent_id=plugin.parent_id,
        )
        # TODO get a better solution for moving a group of nodes at once
        for plugin in copied_plugins:
            target = plugin_map[order[order.index(plugin.pk) - 1]]
            target.refresh_from_db()
            plugin.move(
                target,
                'right',
            )

    def detach_alias_plugin_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied

        form = DetachAliasPluginForm(request.POST)

        if request.method == 'GET' or not form.is_valid():
            return HttpResponseBadRequest('Form received unexpected values')

        plugin = form.cleaned_data['plugin']
        instance = plugin.get_plugin_instance()[0]

        if not self.can_detach(
            request.user,
            instance.alias.placeholder.get_plugins(),
        ):
            raise PermissionDenied

        self.detach_alias_plugin(
            plugin=instance,
            language=get_language(),
        )

        return HttpResponse(
            '<div><div class="messagelist">'
            '<div class="success"></div>'
            '</div></div>'
        )
