from unittest import skipUnless

from cms.api import add_plugin

from djangocms_alias.models import Alias

from .base import BaseAliasPluginTestCase

try:
    import djangocms_rest  # noqa: F401

    HAS_REST = True
except ImportError:
    HAS_REST = False


@skipUnless(HAS_REST, "djangocms-rest is not installed")
class AliasRESTIntegrationTestCase(BaseAliasPluginTestCase):
    """End-to-end coverage of the djangocms-rest cms_config integration."""

    def _create_alias_with_text(self, body="alias body", language="en"):
        alias = self._create_alias(name="test alias", language=language)
        placeholder = alias.get_placeholder(language, show_draft_content=True)
        add_plugin(placeholder, "TextPlugin", language=language, body=body)
        return alias

    def test_endpoint_returns_serialized_placeholder(self):
        alias = self._create_alias_with_text(body="hello from alias")

        response = self.client.get(f"/api/en/aliases/{alias.pk}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["slot"], "content")
        self.assertEqual(data["language"], "en")
        # The text plugin is serialized into the placeholder content tree.
        self.assertTrue(
            any("hello from alias" in str(plugin) for plugin in data["content"]),
            data["content"],
        )

    def test_unknown_alias_returns_404(self):
        # Call the view directly: the project's LocaleMiddleware rewrites
        # unprefixed 404s to a language-prefixed URL (302), which would mask
        # the view's actual response in a full request cycle.
        from rest_framework.test import APIRequestFactory

        from djangocms_alias.rest import AliasContentView

        request = APIRequestFactory().get("/api/en/aliases/999999/")
        response = AliasContentView.as_view()(request, language="en", pk=999999)
        self.assertEqual(response.status_code, 404)

    def test_alias_get_api_endpoint(self):
        alias = self._create_alias(name="linkable alias")
        self.assertEqual(
            alias.get_api_endpoint("en"),
            f"/api/en/aliases/{alias.pk}/",
        )

    def test_alias_plugin_fk_links_to_endpoint(self):
        """An AliasPlugin's ``alias`` FK serializes to the alias endpoint."""
        from djangocms_rest.serializers.plugins import serialize_fk

        alias = self._create_alias(name="referenced alias")
        request = self.get_request("/")
        url = serialize_fk(request, Alias, alias.pk)

        self.assertTrue(url.endswith(f"/api/en/aliases/{alias.pk}/"), url)
