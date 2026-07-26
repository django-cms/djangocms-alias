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

    def test_published_alias_is_public(self):
        """Published alias content is readable without authentication."""
        alias = self._create_alias_with_text(body="public body")

        response = self.client.get(f"/api/en/aliases/{alias.pk}/")

        self.assertEqual(response.status_code, 200)

    def test_preview_requires_staff(self):
        """Draft content (?preview=true) is not served to anonymous users."""
        alias = self._create_alias_with_text(body="draft body")

        response = self.client.get(f"/api/en/aliases/{alias.pk}/?preview=true")

        self.assertIn(response.status_code, (401, 403))

    def test_preview_denied_without_view_permission(self):
        """A staff user lacking the alias view permission cannot preview."""
        staff_user = self._create_user("no-view staff", is_staff=True, is_superuser=False)
        # Sanity check: the user genuinely lacks the permission under test.
        self.assertFalse(staff_user.has_perm("djangocms_alias.view_alias"))
        alias = self._create_alias_with_text(body="draft body")

        self.client.force_login(staff_user)
        response = self.client.get(f"/api/en/aliases/{alias.pk}/?preview=true")

        self.assertEqual(response.status_code, 403)

    def test_preview_allowed_with_view_permission(self):
        """A staff user with the alias view permission may preview drafts."""
        from cms.utils.permissions import get_model_permission_codename
        from django.contrib.auth.models import Permission

        from djangocms_alias.models import Alias as AliasModel

        staff_user = self._create_user("view staff", is_staff=True, is_superuser=False)
        codename = get_model_permission_codename(AliasModel, "view").split(".", 1)[1]
        staff_user.user_permissions.add(Permission.objects.get(codename=codename))
        alias = self._create_alias_with_text(body="draft body")

        self.client.force_login(staff_user)
        response = self.client.get(f"/api/en/aliases/{alias.pk}/?preview=true")

        self.assertEqual(response.status_code, 200)

    def test_unknown_alias_returns_404(self):
        response = self._get_view_response(pk=999999)

        self.assertEqual(response.status_code, 404)

    def test_alias_get_api_endpoint(self):
        alias = self._create_alias(name="linkable alias")
        self.assertEqual(
            alias.get_api_endpoint("en"),
            f"/api/en/aliases/{alias.pk}/",
        )

    def test_static_alias_get_api_endpoint_uses_static_code(self):
        """A static alias links to its readable code, not its pk."""
        alias = self._create_alias(name="footer", static_code="footer")
        self.assertEqual(alias.get_api_endpoint("en"), "/api/en/aliases/footer/")

    def test_numeric_static_code_falls_back_to_pk_endpoint(self):
        """A numeric code would be swallowed by the pk route, so link by pk."""
        alias = self._create_alias(name="odd one", static_code="2")
        self.assertEqual(alias.get_api_endpoint("en"), f"/api/en/aliases/{alias.pk}/")

    def _create_static_alias_with_text(self, static_code, body, site=None, language="en"):
        alias = self._create_alias(name=static_code, static_code=static_code, site=site, language=language)
        placeholder = alias.get_placeholder(language, show_draft_content=True)
        add_plugin(placeholder, "TextPlugin", language=language, body=body)
        return alias

    def test_endpoint_resolves_static_code(self):
        """``/api/en/aliases/footer/`` serves the static alias' content."""
        self._create_static_alias_with_text("footer", body="footer body")

        response = self.client.get("/api/en/aliases/footer/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["language"], "en")
        self.assertTrue(
            any("footer body" in str(plugin) for plugin in data["content"]),
            data["content"],
        )

    def test_site_specific_static_alias_takes_precedence(self):
        """With both a site-less and a current-site alias, the latter wins."""
        from django.contrib.sites.models import Site

        self._create_static_alias_with_text("footer", body="global footer")
        self._create_static_alias_with_text("footer", body="site footer", site=Site.objects.get_current())

        response = self.client.get("/api/en/aliases/footer/")

        self.assertEqual(response.status_code, 200)
        content = str(response.json()["content"])
        self.assertIn("site footer", content)
        self.assertNotIn("global footer", content)

    def test_static_alias_of_other_site_is_not_served(self):
        from django.contrib.sites.models import Site

        other_site = Site.objects.create(domain="other.example.com", name="other")
        self._create_static_alias_with_text("footer", body="other site footer", site=other_site)

        response = self._get_view_response(static_code="footer")

        self.assertEqual(response.status_code, 404)

    def test_unknown_static_code_returns_404(self):
        response = self._get_view_response(static_code="no-such-code")

        self.assertEqual(response.status_code, 404)

    def _get_view_response(self, language="en", **kwargs):
        """Call the view directly.

        The project's LocaleMiddleware rewrites unprefixed 404s to a
        language-prefixed URL (302), which would mask the view's response in a
        full request cycle.
        """
        from rest_framework.test import APIRequestFactory

        from djangocms_alias.rest import AliasContentView

        lookup = next(iter(kwargs.values()))
        request = APIRequestFactory().get(f"/api/{language}/aliases/{lookup}/")
        return AliasContentView.as_view()(request, language=language, **kwargs)

    def test_alias_plugin_fk_links_to_endpoint(self):
        """An AliasPlugin's ``alias`` FK serializes to the alias endpoint."""
        from djangocms_rest.serializers.plugins import serialize_fk

        alias = self._create_alias(name="referenced alias")
        request = self.get_request("/")
        url = serialize_fk(request, Alias, alias.pk)

        self.assertTrue(url.endswith(f"/api/en/aliases/{alias.pk}/"), url)

    def _serialize_alias_plugin(self, alias_plugin, language="en"):
        """Render an AliasPlugin through djangocms-rest's plugin pipeline."""
        from djangocms_rest.plugin_rendering import serialize_cms_plugin

        request = self.get_request("/")
        return serialize_cms_plugin(alias_plugin, {"request": request})

    def test_alias_plugin_uses_inline_serializer(self):
        """The Alias plugin is wired to AliasInlineSerializer."""
        from djangocms_alias.cms_plugins import Alias
        from djangocms_alias.rest import AliasInlineSerializer

        self.assertIs(Alias.serializer_class, AliasInlineSerializer)

    def test_inline_serializer_expands_alias_content(self):
        """An AliasPlugin serializes the referenced alias' plugin tree inline."""
        from cms.api import add_plugin

        alias = self._create_alias_with_text(body="inlined content")
        # Place an AliasPlugin (referencing the alias) on a page placeholder.
        alias_plugin = add_plugin(
            self.placeholder,
            "Alias",
            language="en",
            alias=alias,
        )

        data = self._serialize_alias_plugin(alias_plugin)

        self.assertIn("content", data)
        self.assertTrue(
            any("inlined content" in str(plugin) for plugin in data["content"]),
            data["content"],
        )

    def _page_placeholder_endpoint(self):
        return f"/api/en/placeholders/{self.placeholder.content_type_id}/{self.placeholder.object_id}/content/"

    def test_page_endpoint_expands_alias_inline(self):
        """An AliasPlugin on a page expands its content via the REST endpoint.

        Mirrors djangocms-rest PR #94's ``test_get``: the full request cycle
        through ``placeholder-detail`` must resolve the alias' nested plugins.
        """
        from cms.api import add_plugin

        alias = self._create_alias_with_text(body="Alias text")
        add_plugin(self.placeholder, "Alias", language="en", alias=alias)

        response = self.client.get(self._page_placeholder_endpoint())

        self.assertEqual(response.status_code, 200)
        data = response.json()
        alias_plugin = next(plugin for plugin in data["content"] if plugin.get("plugin_type") == "Alias")
        self.assertIsInstance(alias_plugin["content"], list)
        self.assertEqual(alias_plugin["content"][0]["plugin_type"], "TextPlugin")
        self.assertTrue(
            any("Alias text" in str(plugin) for plugin in alias_plugin["content"]),
            alias_plugin["content"],
        )

    def test_page_endpoint_handles_circular_alias(self):
        """A self-referential alias resolves to empty nested content.

        Mirrors djangocms-rest PR #94's ``test_circular_alias``.
        """
        from cms.api import add_plugin

        alias = self._create_alias_with_text(body="Alias text")
        # The alias references itself inside its own placeholder.
        inner_placeholder = alias.get_placeholder("en", show_draft_content=True)
        add_plugin(inner_placeholder, "Alias", language="en", alias=alias)
        add_plugin(self.placeholder, "Alias", language="en", alias=alias)

        response = self.client.get(self._page_placeholder_endpoint())

        self.assertEqual(response.status_code, 200)
        data = response.json()
        alias_plugin = next(plugin for plugin in data["content"] if plugin.get("plugin_type") == "Alias")
        self.assertTrue(alias_plugin["content"])
        nested_alias = next(
            plugin for plugin in alias_plugin["content"] if plugin.get("plugin_type") in ("Alias", "AliasPlugin")
        )
        self.assertEqual(nested_alias["content"], [])

    def test_inline_serializer_guards_against_recursion(self):
        """An alias already on the render stack yields empty content."""
        from cms.api import add_plugin

        from djangocms_alias.rest import AliasInlineSerializer

        alias = self._create_alias_with_text(body="should not appear")
        alias_plugin = add_plugin(
            self.placeholder,
            "Alias",
            language="en",
            alias=alias,
        )

        request = self.get_request("/")
        # Simulate the alias already being expanded higher up the tree.
        request._rest_alias_stack = [alias.pk]

        serializer = AliasInlineSerializer(context={"request": request})
        self.assertEqual(serializer.get_content(alias_plugin), [])
        # The guard leaves the caller's stack untouched.
        self.assertEqual(request._rest_alias_stack, [alias.pk])
