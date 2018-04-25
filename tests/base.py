from django.contrib.auth import get_permission_codename
from django.http import QueryDict
from django.test.client import RequestFactory
from django.urls import resolve

from cms.api import add_plugin, create_page
from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import CMSTestCase
from cms.utils.conf import get_cms_setting

from djangocms_alias.constants import (
    CATEGORY_LIST_URL_NAME,
    CREATE_ALIAS_URL_NAME,
    DELETE_ALIAS_PLUGIN_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
    PUBLISH_ALIAS_URL_NAME,
    SET_ALIAS_DRAFT_URL_NAME,
)
from djangocms_alias.models import Alias as AliasModel
from djangocms_alias.models import Category
from djangocms_alias.utils import alias_plugin_reverse


class BaseAliasPluginTestCase(CMSTestCase):
    CREATE_ALIAS_ENDPOINT = alias_plugin_reverse(CREATE_ALIAS_URL_NAME)
    CATEGORY_LIST_ENDPOINT = alias_plugin_reverse(CATEGORY_LIST_URL_NAME)
    SET_ALIAS_DRAFT_ENDPOINT = alias_plugin_reverse(SET_ALIAS_DRAFT_URL_NAME)

    def PUBLISH_ALIAS_ENDPOINT(self, alias_pk, language=None):
        return alias_plugin_reverse(
            PUBLISH_ALIAS_URL_NAME,
            args=(
                alias_pk,
                language or self.language,
            ),
        )

    def DETACH_ALIAS_PLUGIN_ENDPOINT(self, plugin_pk):
        return alias_plugin_reverse(
            DETACH_ALIAS_PLUGIN_URL_NAME,
            args=[plugin_pk],
        )

    def DETAIL_ALIAS_ENDPOINT(self, alias_pk):
        return alias_plugin_reverse(
            DETAIL_ALIAS_URL_NAME,
            args=[alias_pk],
        )

    def DELETE_ALIAS_ENDPOINT(self, alias_pk):
        return alias_plugin_reverse(
            DELETE_ALIAS_PLUGIN_URL_NAME,
            args=[alias_pk],
        )

    def LIST_ALIASES_ENDPOINT(self, category_pk):
        return alias_plugin_reverse(
            LIST_ALIASES_URL_NAME,
            args=[category_pk],
        )

    def setUp(self):
        self.language = 'en'
        self.page = create_page(
            title='test',
            template='page.html',
            language=self.language,
            published=True,
            in_navigation=True,
        )
        self.category = Category.objects.create(
            name='test category',
        )
        self.placeholder = self.page.placeholders.get(slot='content')
        self.plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test',
        )
        self.superuser = self.get_superuser()

    def _create_alias(self, plugins=None, name='test alias', category=None,
                      position=0):
        if category is None:
            category = self.category
        if plugins is None:
            plugins = []
        alias = AliasModel.objects.create(
            name=name,
            category=category,
            position=position,
        )
        if plugins:
            alias.populate(plugins=plugins)
        return alias

    def _get_instance_request(self, instance, user, path=None, edit=False,
                              preview=False, structure=False, lang_code='en',
                              disable=False, **kwargs):
        if not path:
            path = instance.get_absolute_url()

        if edit:
            path += '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')

        if structure:
            path += '?%s' % get_cms_setting('CMS_TOOLBAR_URL__BUILD')

        if preview:
            path += '?preview'

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

    def _process_request_by_toolbar_middleware(self, request, toolbar_object=None):  # noqa: E501
        midleware = ToolbarMiddleware()
        midleware.process_request(request)
        if hasattr(request, 'toolbar'):
            if toolbar_object:
                request.toolbar.set_object(toolbar_object)
            request.toolbar.populate()
            request.resolver_match = resolve(request.path)
            request.toolbar.post_template_populate()
        return request

    def get_alias_request(self, alias, *args, **kwargs):  # noqa: E501
        request = self._get_instance_request(alias, *args, **kwargs)
        request.current_page = None
        request = self._process_request_by_toolbar_middleware(
            request,
            kwargs.get('toolbar_object', None),
        )
        return request

    def get_page_request(self, page, *args, **kwargs):  # noqa: E501
        request = self._get_instance_request(page, *args, **kwargs)
        request.current_page = page
        request = self._process_request_by_toolbar_middleware(request)
        return request

    def get_staff_user_with_alias_permissions(self):
        staff_user = self._create_user("alias staff", is_staff=True, is_superuser=False)  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('add', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('change', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('delete', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('add', Category._meta))  # noqa: E501
        return staff_user
