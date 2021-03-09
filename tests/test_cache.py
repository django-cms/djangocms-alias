from django.template import Context

from cms.api import add_plugin
from cms.cache.placeholder import get_placeholder_cache
from cms.test_utils.util.fuzzy_int import FuzzyInt

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.constants import DEFAULT_STATIC_ALIAS_CATEGORY_NAME
from djangocms_alias.models import Alias as AliasModel, Category

from .base import BaseAliasPluginTestCase


class AliasCacheTestCase(BaseAliasPluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% render_alias plugin.alias %}"""

    def test_create_published_alias(self):
        """
        A published page populated with placeholders and plugins
        should contain the content it is populated with when rendered
        """
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

        # Create alias plugin inside the page placeholder
        add_plugin(
            page_placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )

        # Get page via http request
        with self.login_user_context(self.superuser):
            response = self.client.get(page.get_absolute_url(self.language))

        # Check the response contains the content we added to our page
        self.assertContains(response, 'Content Alias 1234')

    # def test_static_alias_placeholder_cache(self):
    #     category = Category.objects.create(name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)
    #     unlimited_alias = self._create_alias(
    #         plugins=None, name='test alias', category=category, static_code="site_limit_alias_code", site=None)
    #     add_plugin(
    #         unlimited_alias.get_placeholder(self.language),
    #         'TextPlugin',
    #         language=self.language,
    #         body='unlimited text',
    #     )

    def test_query_plugin_count(self):
        """
        Aliases are cached, so we should see a decrease in the number of queries
        when rendering once the cache is populated.
        """
        # Create an alias, a placeholder and a plugin within the placeholder
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
            # render the page
            self.client.get(page.get_absolute_url(self.language))
        # Get the plugins from the page and count them
        plugins = page_placeholder.get_plugins()
        plugins_count = plugins.count()

        # Ensure only the two created plugins are present
        self.assertEqual(plugins_count, 2)

    def test_placeholder_cache(self):
        """
        The placeholder contents should be cached for published content (or all content if versioning is not installed).
        """

        alias = self._create_alias(published=True)
        alias_placeholder = alias.get_placeholder(self.language)
        # Create a text plugin and an alias plugin
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

        # The first time we render the page it should be querying the database
        with self.assertNumQueries(FuzzyInt(1, 26)):
            self.client.get(page.get_absolute_url(self.language))
        # The second time we render the page, the cache should be populated, there should be no queries
        with self.assertNumQueries(FuzzyInt(0, 0)):
            self.client.get(page.get_absolute_url(self.language))

        # Get a request targeting the page
        request = self.get_request('/en/')
        context = Context({
            'request': request,
        })

        # Render the page given the request we generated earlier
        renderer = self.get_content_renderer(request)
        content = renderer.render_placeholder(page_placeholder, context, 'en', width=350)
        cached_placeholder = get_placeholder_cache(page_placeholder, 'en', 1, request)

        # The content should be the same whether accessed via the rendered page, or via the plugin directly
        self.assertEqual(cached_placeholder.get('content'), content)
