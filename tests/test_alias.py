from cms.api import (
    add_plugin,
    create_page,
)
from cms.test_utils.testcases import CMSTestCase

from djangocms_alias.constants import CREATE_ALIAS_URL_NAME
from djangocms_alias.cms_plugins import Alias2Plugin
from djangocms_alias.models import Category
from djangocms_alias.utils import alias_plugin_reverse


class Alias2PluginTestCase(CMSTestCase):
    CREATE_ALIAS_ENDPOINT = alias_plugin_reverse(CREATE_ALIAS_URL_NAME)

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
        self.alias_plugin = Alias2Plugin()
        self.superuser = self.get_superuser()

    def _create_alias(self, plugins, name='test alias', category=None):
        if category is None:
            category = self.category
        return self.alias_plugin.create_alias_plugin(
            name=name,
            category=category,
            plugins=plugins,
        )

    def test_create_alias_from_plugin_list(self):
        plugins = self.placeholder.get_plugins()
        alias = self._create_alias(plugins)
        self.assertEqual(
            plugins[0].plugin_type,
            alias.placeholder.get_plugins()[0].plugin_type,
        )
        self.assertEqual(
            plugins[0].get_plugin_instance()[0].body,
            alias.placeholder.get_plugins()[0].get_plugin_instance()[0].body,
        )

    def test_replace_plugin_with_alias(self):
        plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language='en',
            body='test 2',
        )
        alias = self._create_alias(
            [plugin],
        )
        self.alias_plugin.replace_plugin_with_alias(
            self.plugin,
            alias,
            self.language,
        )
        plugins = self.placeholder.get_plugins()
        self.assertNotIn(
            self.plugin,
            plugins,
        )
        self.assertEqual(plugins[0].plugin_type, 'Alias2Plugin')
        self.assertEqual(plugins[0].get_plugin_instance()[0].alias, alias)

    def test_create_alias_view_get_no_data(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.CREATE_ALIAS_ENDPOINT)
            self.assertEqual(response.status_code, 400)
