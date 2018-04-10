from django.test.client import RequestFactory

from cms.api import (
    add_plugin,
    create_page,
)
from cms.test_utils.testcases import CMSTestCase

from djangocms_alias.cms_plugins import Alias2Plugin
from djangocms_alias.constants import (
    CREATE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
)
from djangocms_alias.models import Category
from djangocms_alias.utils import alias_plugin_reverse


class BaseAlias2PluginTestCase(CMSTestCase):
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
        self.alias_plugin_base = Alias2Plugin()
        self.superuser = self.get_superuser()
        self.rf = RequestFactory()

    def _create_alias(self, plugins, name='test alias', category=None):
        if category is None:
            category = self.category
        return self.alias_plugin_base.create_alias(
            name=name,
            category=category,
            plugins=plugins,
        )
