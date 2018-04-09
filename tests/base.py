from cms.api import (
    add_plugin,
    create_page,
)
from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import admin_reverse

from djangocms_aliases.cms_plugins import Alias2Plugin
from djangocms_aliases.models import Category


class BaseAlias2PluginTestCase(CMSTestCase):
    CREATE_ALIAS_ENDPOINT = admin_reverse('djangocms_aliases_create')
    LIST_ALIASES_ENDPOINT = admin_reverse('djangocms_aliases_list')
    DETACH_ALIAS_PLUGIN_ENDPOINT = admin_reverse('djangocms_aliases_detach_plugin')  # noqa: E501

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
            language='en',
            body='test',
        )
        self.alias_plugin_base = Alias2Plugin()
        self.superuser = self.get_superuser()

    def _create_alias(self, plugins, name='test alias', category=None):
        if category is None:
            category = self.category
        return self.alias_plugin_base.create_alias(
            name=name,
            category=category,
            plugins=plugins,
        )
