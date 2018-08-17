from django.contrib.auth.models import Permission
from django.http import QueryDict
from django.test.client import RequestFactory
from django.urls import resolve

from cms.api import add_plugin, create_page
from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import CMSTestCase
from cms.utils.conf import get_cms_setting

from djangocms_alias.compat import get_page_placeholders
from djangocms_alias.constants import (
    CATEGORY_LIST_URL_NAME,
    CREATE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
)
from djangocms_alias.models import Alias as AliasModel, AliasContent, Category
from djangocms_alias.utils import alias_plugin_reverse


class BaseAliasPluginTestCase(CMSTestCase):

    @property
    def CREATE_ALIAS_ENDPOINT(self):
        return alias_plugin_reverse(CREATE_ALIAS_URL_NAME)

    @property
    def CATEGORY_LIST_ENDPOINT(self):
        return alias_plugin_reverse(CATEGORY_LIST_URL_NAME)

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

        self.placeholder = get_page_placeholders(self.page, self.language).get(
            slot='content',
        )
        self.plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test',
        )
        self.superuser = self.get_superuser()

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

    def _get_instance_request(self, instance, user, path=None, edit=False,
                              preview=False, structure=False, lang_code='en',
                              disable=False):
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

    def get_alias_request(self, alias, *args, **kwargs):  # noqa: E501
        request = self._get_instance_request(alias, *args, **kwargs)
        request.current_page = None
        request = self._process_request_by_toolbar_middleware(request, obj=alias)
        return request

    def get_page_request(self, page, obj=None, *args, **kwargs):  # noqa: E501
        request = self._get_instance_request(page, *args, **kwargs)
        request.current_page = page
        request = self._process_request_by_toolbar_middleware(request, obj)
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
