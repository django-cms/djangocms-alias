from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.http import QueryDict
from django.test.client import RequestFactory
from django.urls import resolve

from cms.api import add_plugin, create_page
from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.utils import (
    get_object_edit_url,
    get_object_preview_url,
    get_object_structure_url,
)
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse

from djangocms_alias.constants import (
    CATEGORY_LIST_URL_NAME,
    CREATE_ALIAS_URL_NAME,
    DELETE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    LIST_ALIASES_URL_NAME,
)
from djangocms_alias.models import Alias as AliasModel, AliasContent, Category


class BaseAliasPluginTestCase(CMSTestCase):

    def get_create_alias_endpoint(self):
        return admin_reverse(CREATE_ALIAS_URL_NAME)

    def get_category_list_endpoint(self):
        return admin_reverse(CATEGORY_LIST_URL_NAME)

    def get_detach_alias_plugin_endpoint(self, plugin_pk):
        return admin_reverse(
            DETACH_ALIAS_PLUGIN_URL_NAME,
            args=[plugin_pk],
        )

    def get_delete_alias_endpoint(self, alias_pk):
        return admin_reverse(
            DELETE_ALIAS_URL_NAME,
            args=[alias_pk],
        )

    def get_list_aliases_endpoint(self, category_pk):
        return admin_reverse(
            LIST_ALIASES_URL_NAME,
            args=[category_pk],
        )

    def setUp(self):
        self.language = 'en'
        self.page = create_page(
            title='test',
            template='page.html',
            language=self.language,
            in_navigation=True,
        )
        self.placeholder = self.page.get_placeholders(self.language).get(
            slot='content',
        )
        self.plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test',
        )
        self.superuser = self.get_superuser()
        self.category = Category.objects.create(name='test category')

    def _create_alias(self, plugins=None, name='test alias', category=None, position=0, language=None):
        if language is None:
            language = self.language
        if category is None:
            category = self.category
        if plugins is None:
            plugins = []
        alias = AliasModel.objects.create(
            category=category,
            position=position,
        )
        alias_content = AliasContent.objects.create(
            alias=alias,
            name=name,
            language=language,
        )
        if plugins:
            alias_content.populate(plugins=plugins)
        return alias

    def get_alias_request(self, alias, lang_code='en', *args, **kwargs):
        request = self._get_instance_request(alias, *args, **kwargs)
        request.current_page = None
        request = self._process_request_by_toolbar_middleware(request, obj=alias.get_content(lang_code))
        return request

    def get_page_request(self, page, obj=None, *args, **kwargs):
        request = self._get_instance_request(page, *args, **kwargs)
        request.current_page = page
        request = self._process_request_by_toolbar_middleware(request, obj)
        return request

    def _get_instance_request(self, instance, user, path=None, edit=False,
                              preview=False, structure=False, lang_code='en',
                              disable=False):
        if not path:
            if edit:
                path = get_object_edit_url(instance)
            elif preview:
                path = get_object_preview_url(instance)
            elif structure:
                path = get_object_structure_url(instance)
            else:
                path = instance.get_absolute_url()

        request = RequestFactory().get(path)
        request.session = {}
        request.user = user
        request.LANGUAGE_CODE = lang_code
        request.GET = QueryDict('', mutable=True)
        if edit:
            request.GET['edit'] = None
        else:
            request.GET['edit_off'] = None
        if disable:
            request.GET[get_cms_setting('CMS_TOOLBAR_URL__DISABLE')] = None

        return request

    def _process_request_by_toolbar_middleware(self, request, obj=None):
        midleware = ToolbarMiddleware()
        midleware.process_request(request)
        if hasattr(request, 'toolbar'):
            if obj:
                request.toolbar.set_object(obj)
            request.toolbar.populate()
            request.resolver_match = resolve(request.path)
            request.toolbar.post_template_populate()
        return request

    def _add_default_permissions(self, user):
        # Text plugin permissions
        user.user_permissions.add(Permission.objects.get(codename='add_text'))
        user.user_permissions.add(Permission.objects.get(codename='delete_text'))
        user.user_permissions.add(Permission.objects.get(codename='change_text'))
        # Page permissions
        user.user_permissions.add(Permission.objects.get(codename='publish_page'))
        user.user_permissions.add(Permission.objects.get(codename='add_page'))
        user.user_permissions.add(Permission.objects.get(codename='change_page'))
        user.user_permissions.add(Permission.objects.get(codename='delete_page'))

    def add_alias_plugin_to_page(self, page, alias, language=None):
        if language is None:
            language = self.language

        add_plugin(
            page.get_placeholders(language).get(slot='content'),
            'Alias',
            language=language,
            alias=alias,
        )

    def get_staff_user_with_alias_permissions(self):
        staff_user = self._create_user("alias staff", is_staff=True, is_superuser=False)  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('add', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('change', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('delete', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('add', AliasContent._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('change', AliasContent._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('delete', AliasContent._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('add', Category._meta))  # noqa: E501
        return staff_user
