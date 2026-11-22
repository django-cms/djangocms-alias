from unittest import skipUnless

from cms.api import add_plugin
from django.core.cache import cache
from django.test import override_settings

from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase

STATIC_CODE = "template_example_global_alias_code"


@skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
class AliasPublishCacheTestCase(BaseAliasPluginTestCase):
    """Publishing or unpublishing an alias must be visible at once on cached
    pages (#408). Two caches are involved:

    * the page cache, which holds the complete response, and
    * the placeholder cache of the placeholder holding an Alias plugin, which
      holds the rendered content of the alias.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)

    def _create_alias_with_text(self, body, **kwargs):
        alias = self._create_alias(**kwargs)
        add_plugin(alias.get_placeholder(self.language), "TextPlugin", language=self.language, body=body)
        return alias

    def _create_draft_with_text(self, alias, body):
        """Creates a new draft of the alias with a changed text - without
        publishing it."""
        from djangocms_versioning.constants import PUBLISHED

        draft = self._get_version(alias, PUBLISHED).copy(self.superuser)
        plugin = draft.content.placeholder.get_plugins(self.language).get(plugin_type="TextPlugin")
        text, _ = plugin.get_plugin_instance()
        text.body = body
        text.save()
        return draft

    def _get_page(self, page=None):
        """Requests the page as an anonymous visitor"""
        response = self.client.get((page or self.page).get_absolute_url(self.language))
        self.assertEqual(response.status_code, 200)
        return response

    def assertAliasContentIsReplaced(self, page=None, old="old alias content", new="new alias content"):
        response = self._get_page(page)
        self.assertContains(response, new)
        self.assertNotContains(response, old)

    def test_publish_updates_alias_plugin_on_cached_page(self):
        alias = self._create_alias_with_text("old alias content")
        self.add_alias_plugin_to_page(self.page, alias)
        draft = self._create_draft_with_text(alias, "new alias content")
        # Fill the caches
        self.assertContains(self._get_page(), "old alias content")

        draft.publish(self.superuser)

        self.assertAliasContentIsReplaced()

    @override_settings(CMS_PAGE_CACHE=False)
    def test_publish_clears_placeholder_cache_of_alias_plugin(self):
        # Without the page cache the response is rendered for each request, but
        # the page's placeholder still serves its content from the placeholder
        # cache. That placeholder does not change when the alias is published.
        alias = self._create_alias_with_text("old alias content")
        self.add_alias_plugin_to_page(self.page, alias)
        draft = self._create_draft_with_text(alias, "new alias content")
        self.assertContains(self._get_page(), "old alias content")

        draft.publish(self.superuser)

        self.assertAliasContentIsReplaced()

    @override_settings(CMS_PAGE_CACHE=False)
    def test_publish_clears_placeholder_cache_of_nested_alias_plugin(self):
        # page > outer alias > inner alias: the page's placeholder caches the
        # content of both aliases
        inner = self._create_alias_with_text("old alias content", name="inner")
        outer = self._create_alias(name="outer", position=1)
        add_plugin(outer.get_placeholder(self.language), "Alias", language=self.language, alias=inner)
        self.add_alias_plugin_to_page(self.page, outer)
        draft = self._create_draft_with_text(inner, "new alias content")
        self.assertContains(self._get_page(), "old alias content")

        draft.publish(self.superuser)

        self.assertAliasContentIsReplaced()

    def test_unpublish_removes_alias_plugin_from_cached_page(self):
        alias = self._create_alias_with_text("old alias content")
        self.add_alias_plugin_to_page(self.page, alias)
        self.assertContains(self._get_page(), "old alias content")

        self._unpublish(alias)

        self.assertNotContains(self._get_page(), "old alias content")

    @override_settings(CMS_PAGE_CACHE=False)
    def test_unpublish_clears_placeholder_cache_of_alias_plugin(self):
        alias = self._create_alias_with_text("old alias content")
        self.add_alias_plugin_to_page(self.page, alias)
        self.assertContains(self._get_page(), "old alias content")

        self._unpublish(alias)

        self.assertNotContains(self._get_page(), "old alias content")

    def test_publish_updates_static_alias_on_cached_page(self):
        alias = self._create_alias_with_text("old alias content", static_code=STATIC_CODE)
        page = self._create_page("static alias page", template="static_alias.html")
        draft = self._create_draft_with_text(alias, "new alias content")
        self.assertContains(self._get_page(page), "old alias content")

        draft.publish(self.superuser)

        self.assertAliasContentIsReplaced(page)

    @override_settings(CMS_PAGE_CACHE=False)
    def test_publish_clears_placeholder_cache_of_static_alias_with_alias_plugin(self):
        # The placeholder of the static alias caches the content of the alias
        # it shows through an Alias plugin
        inner = self._create_alias_with_text("old alias content", name="inner")
        static_alias = self._create_alias(name="static", position=1, static_code=STATIC_CODE)
        add_plugin(static_alias.get_placeholder(self.language), "Alias", language=self.language, alias=inner)
        page = self._create_page("static alias page", template="static_alias.html")
        draft = self._create_draft_with_text(inner, "new alias content")
        self.assertContains(self._get_page(page), "old alias content")

        draft.publish(self.superuser)

        self.assertAliasContentIsReplaced(page)

    def test_unpublish_removes_static_alias_from_cached_page(self):
        alias = self._create_alias_with_text("old alias content", static_code=STATIC_CODE)
        page = self._create_page("static alias page", template="static_alias.html")
        self.assertContains(self._get_page(page), "old alias content")

        self._unpublish(alias)

        self.assertNotContains(self._get_page(page), "old alias content")

    def test_publish_does_not_clear_placeholder_cache_of_unrelated_placeholders(self):
        from cms.cache.placeholder import _get_placeholder_cache_version

        alias = self._create_alias_with_text("old alias content")
        other_page = self._create_page("other page")
        other_placeholder = other_page.get_placeholders(self.language).get(slot="content")
        add_plugin(other_placeholder, "TextPlugin", language=self.language, body="other content")
        self.add_alias_plugin_to_page(self.page, alias)
        draft = self._create_draft_with_text(alias, "new alias content")
        self._get_page()
        self._get_page(other_page)
        site_id = other_page.site_id
        version = _get_placeholder_cache_version(other_placeholder, self.language, site_id)

        draft.publish(self.superuser)

        self.assertEqual(
            _get_placeholder_cache_version(other_placeholder, self.language, site_id),
            version,
        )


class AliasPluginPageCacheTestCase(BaseAliasPluginTestCase):
    """Rendering an Alias plugin must not prevent the page from being stored
    in the page cache (#409)."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)

    def _get_page(self):
        """Requests the page as an anonymous visitor"""
        response = self.client.get(self.page.get_absolute_url(self.language))
        self.assertEqual(response.status_code, 200)
        return response

    def assertIsCacheable(self, response):
        cache_control = response.headers.get("Cache-Control", "")
        self.assertNotIn("no-cache", cache_control)
        self.assertNotIn("no-store", cache_control)
        self.assertRegex(cache_control, r"max-age=[1-9]")

    def test_page_without_alias_plugin_is_cached_at_first_request(self):
        # Reference: the behaviour of a page without an alias
        self.assertIsCacheable(self._get_page())

    def test_page_with_alias_plugin_is_cached_at_first_request(self):
        from cms.cache.page import get_page_cache

        alias = self._create_alias()
        add_plugin(alias.get_placeholder(self.language), "TextPlugin", language=self.language, body="alias content")
        self.add_alias_plugin_to_page(self.page, alias)

        response = self._get_page()

        self.assertContains(response, "alias content")
        self.assertIsCacheable(response)
        self.assertIsNotNone(get_page_cache(response.wsgi_request))

    def test_page_with_alias_plugin_is_not_cached_for_users(self):
        alias = self._create_alias()
        add_plugin(alias.get_placeholder(self.language), "TextPlugin", language=self.language, body="alias content")
        self.add_alias_plugin_to_page(self.page, alias)

        with self.login_user_context(self.superuser):
            response = self._get_page()

        self.assertContains(response, "alias content")
        self.assertIn("no-cache", response.headers.get("Cache-Control", ""))
