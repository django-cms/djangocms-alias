from cms.api import add_plugin
from cms.test_utils.util.fuzzy_int import FuzzyInt

from djangocms_alias.cms_plugins import Alias

from .base import BaseAliasPluginTestCase


class AliasCacheTestCase(BaseAliasPluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% render_alias plugin.alias %}"""

    def test_create_published_alias(self):
        # Create and populate alias
        alias = self._create_alias(published=True)
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='Content Alias 1234',
        )

        # Create page and add alias
        page = self._create_page('test')
        page_placeholder = page.get_placeholders(self.language).get(
            slot='content',
        )

        add_plugin(
            page_placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(page.get_absolute_url(self.language))

        self.assertContains(response, 'Content Alias 1234')

    def test_query_plugin_count(self):

        alias = self._create_alias(published=True)
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )

        page = self._create_page('test')
        page_placeholder = page.get_placeholders(self.language).get(
            slot='content',
        )

        add_plugin(
            page_placeholder,
            'TextPlugin',
            language=self.language,
            body='Content Alias 1234',
        )

        add_plugin(
            page_placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )

        with self.login_user_context(self.superuser):
            # returns a template response
            self.client.get(page.get_absolute_url(self.language))

        plugins = page_placeholder.get_plugins()
        plugins_count = plugins.count()
        self.assertEqual(plugins_count, 2)

    def test_count_queries(self):

        alias = self._create_alias(published=True)
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )

        page = self._create_page('test')
        page_placeholder = page.get_placeholders(self.language).get(
            slot='content',
        )

        add_plugin(
            page_placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )

        with self.assertNumQueries(FuzzyInt(1, 25)):
            self.client.get(page.get_absolute_url(self.language))

        with self.assertNumQueries(FuzzyInt(1, 25)):
            self.client.get(page.get_absolute_url(self.language))

    def test_create_alias_with_default_render_template(self):
        # Create alias
        alias = self._create_alias()
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )

        add_plugin(
            alias_placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )

        # Test if the template rendered is the default template
        self.assertEqual(alias.cms_plugins.first().template, 'default')

    def test_create_alias_with_custom_render_template(self):
        alias_template = 'custom_alias_template'
        alias = self._create_alias()
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            Alias,
            language=self.language,
            alias=alias,
            template=alias_template,
        )
        self.assertEqual(alias.cms_plugins.first().template, "custom_alias_template")
