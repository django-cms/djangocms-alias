from django.template import Context

from cms.api import add_plugin
from cms.cache.placeholder import get_placeholder_cache
from cms.test_utils.util.fuzzy_int import FuzzyInt

from djangocms_alias.cms_plugins import Alias

from .base import BaseAliasPluginTestCase


class AliasCacheTestCase(BaseAliasPluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% render_alias plugin.alias %}"""

    def setUp(self):
        super().setUp()
        # Create an alias and get a placeholder
        self.alias = self._create_alias(published=True)
        self.alias_placeholder = self.alias.get_placeholder(self.language)
        # Create page and add alias
        self.page = self._create_page('test')
        self.page_placeholder = self.page.get_placeholders(self.language).get(slot='content')

    def test_create_published_alias(self):
        add_plugin(
            self.alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='Content Alias 1234',
        )

        # Create alias plugin inside the page placeholder
        add_plugin(
            self.page_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
        )

        # Get page via http request
        with self.login_user_context(self.superuser):
            response = self.client.get(self.page.get_absolute_url(self.language))

        # Check the response contains the content we added to our page
        self.assertContains(response, 'Content Alias 1234')

    def test_query_plugin_count(self):
        """
        Aliases are cached, so we should see a decrease in the number of queries
        when rendering once the cache is populated.
        """
        # Create an alias, a placeholder and a plugin within the placeholder
        add_plugin(
            self.alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )

        add_plugin(
            self.page_placeholder,
            'TextPlugin',
            language=self.language,
            body='Content Alias 1234',
        )

        add_plugin(
            self.page_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
        )

        with self.login_user_context(self.superuser):
            # returns a template response
            self.client.get(self.page.get_absolute_url(self.language))

        plugins = self.page_placeholder.get_plugins()
        plugins_count = plugins.count()
        self.assertEqual(plugins_count, 2)

    def test_count_queries_second(self):
        add_plugin(
            self.page_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
        )

        with self.assertNumQueries(FuzzyInt(1, 26)):
            self.client.get(self.page.get_absolute_url(self.language))

    def test_create_alias_with_default_render_template(self):
        add_plugin(
            self.alias_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
        )

        add_plugin(
            self.alias_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
        )

        # Test if the template rendered is the default template
        self.assertEqual(self.alias.cms_plugins.first().template, 'default')

    def test_create_alias_with_custom_render_template(self):
        alias_template = 'custom_alias_template'
        add_plugin(
            self.alias_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
            template=alias_template,
        )
        self.assertEqual(self.alias.cms_plugins.first().template, "custom_alias_template")

    def test_count_queries_first(self):
        add_plugin(
            self.alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        add_plugin(
            self.page_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
        )

        with self.assertNumQueries(FuzzyInt(1, 26)):
            self.client.get(self.page.get_absolute_url(self.language))
        with self.assertNumQueries(FuzzyInt(0, 0)):
            self.client.get(self.page.get_absolute_url(self.language))

        request = self.get_request('/en/')
        context = Context({
            'request': request,
        })

        renderer = self.get_content_renderer(request)
        content = renderer.render_placeholder(self.page_placeholder, context, 'en', width=350)

        # placeholder, lang, site_id, request
        # # set_placeholder_cache(page_placeholder, 'en', 1, content, request)
        # cached_content = get_placeholder_cache(page_placeholder, 'en', 1, request)
        # self.assertEqual(cached_content, content)
        cached_placeholder = get_placeholder_cache(self.page_placeholder, 'en', 1, request)
        # self.assertEqual(cached_placeholder, page_placeholder['content'])
        self.assertEqual(cached_placeholder.get('content'), content)
