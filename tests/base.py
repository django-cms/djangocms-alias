from django.test.client import RequestFactory

from cms.api import (
    add_plugin,
    create_page,
)
from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import CMSTestCase
from cms.utils.conf import get_cms_setting

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.constants import (
    CREATE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
)
from djangocms_alias.models import Category
from djangocms_alias.utils import alias_plugin_reverse


class BaseAliasPluginTestCase(CMSTestCase):
    CREATE_ALIAS_ENDPOINT = alias_plugin_reverse(CREATE_ALIAS_URL_NAME)
    LIST_ALIASES_ENDPOINT = alias_plugin_reverse(LIST_ALIASES_URL_NAME)
    DETACH_ALIAS_PLUGIN_ENDPOINT = alias_plugin_reverse(DETACH_ALIAS_PLUGIN_URL_NAME)  # noqa: E501

    def DETAIL_ALIAS_ENDPOINT(self, alias_pk):
        return alias_plugin_reverse(
            DETAIL_ALIAS_URL_NAME,
            args=[alias_pk],
        )

    def setUp(self):
        self.language = 'en'
        self.page = create_page(
            title='test',
            template='page.html',
            language=self.language,
            published=True,
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
        self.alias_plugin_base = Alias()
        self.superuser = self.get_superuser()

    def _create_alias(self, plugins=None, name='test alias', category=None):
        if category is None:
            category = self.category
        if plugins is None:
            plugins = []
        alias = self.alias_plugin_base.create_alias(
            name=name,
            category=category,
        )
        if plugins:
            self.alias_plugin_base.populate_alias(alias, plugins)
        return alias

    def get_page_request(self, page, user, path=None, edit=False,
                         preview=False, structure=False, lang_code='en', disable=False):  # noqa: E501
        if not path:
            path = page.get_absolute_url()

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
        if edit:
            request.GET = {'edit': None}
        else:
            request.GET = {'edit_off': None}
        if disable:
            request.GET[get_cms_setting('CMS_TOOLBAR_URL__DISABLE')] = None
        request.current_page = page
        mid = ToolbarMiddleware()
        mid.process_request(request)
        if hasattr(request, 'toolbar'):
            request.toolbar.populate()
        return request
