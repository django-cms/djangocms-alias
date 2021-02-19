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
        """
        A published page populated with placeholders and plugins
        should contain the content it is populated with when rendered
        """
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
            # render the page
            self.client.get(self.page.get_absolute_url(self.language))
        # Get the plugins from the page and count them
        plugins = self.page_placeholder.get_plugins()
        plugins_count = plugins.count()

        # Ensure only the two created plugins are present
        self.assertEqual(plugins_count, 2)

    def test_create_alias_with_default_render_template(self):
        # Create an alias plugin without explicitly defining the template to use
        add_plugin(
            self.alias_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
        )

        # The default template should be used if one is not provided
        self.assertEqual(self.alias.cms_plugins.first().template, 'default')

    def test_create_alias_with_custom_render_template(self):
        # Define a custom template
        alias_template = 'custom_alias_template'

        # Create an alias plugin providing our custom template
        add_plugin(
            self.alias_placeholder,
            Alias,
            language=self.language,
            alias=self.alias,
            template=alias_template,
        )

        # The custom template should be assigned to the plugin we created
        self.assertEqual(self.alias.cms_plugins.first().template, "custom_alias_template")

    def test_query_count(self):
        # Create a text plugin and an alias plugin
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

        # The first time we render the page it should be querying the database
        with self.assertNumQueries(FuzzyInt(1, 26)):
            self.client.get(self.page.get_absolute_url(self.language))
        # The second time we render the page, the cache should be populated, there should be no queries
        with self.assertNumQueries(FuzzyInt(0, 0)):
            self.client.get(self.page.get_absolute_url(self.language))

        # Get a request targeting the page
        request = self.get_request('/en/')
        context = Context({
            'request': request,
        })

        # Render the page given the request we generated earlier
        renderer = self.get_content_renderer(request)
        content = renderer.render_placeholder(self.page_placeholder, context, 'en', width=350)
        cached_placeholder = get_placeholder_cache(self.page_placeholder, 'en', 1, request)

        # The content should be the same whether accessed via the rendered page, or via the plugin directly
        self.assertEqual(cached_placeholder.get('content'), content)
