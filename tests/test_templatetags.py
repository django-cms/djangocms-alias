from unittest import skipUnless

from cms.api import add_plugin, create_page, create_page_content
from cms.toolbar.utils import get_object_edit_url, get_object_preview_url
from django.contrib.sites.models import Site
from django.test.utils import override_settings

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.constants import DEFAULT_STATIC_ALIAS_CATEGORY_NAME
from djangocms_alias.models import Alias as AliasModel
from djangocms_alias.models import Category
from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class AliasTemplateTagsTestCase(BaseAliasPluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% render_alias plugin.alias %}"""  # noqa: E501

    def test_render_alias(self):
        alias = self._create_alias()
        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=self.placeholder,
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                "plugin": alias_plugin,
            },
            self.get_request("/"),
        )
        self.assertEqual(output, "test")

    def test_render_alias_includes_recursed_alias(self):
        alias = self._create_alias()
        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=self.placeholder,
        )
        add_plugin(
            alias.get_placeholder(self.language),
            Alias,
            language=self.language,
            alias=alias,
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                "plugin": alias_plugin,
            },
            self.get_request("/"),
        )
        self.assertEqual(output, "test")

    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_render_alias_dont_render_draft_aliases(self):
        alias = self._create_alias([self.plugin], published=False)
        alias_plugin = add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        output = self.render_template_obj(
            self.alias_template,
            {"plugin": alias_plugin},
            self.get_request("/"),
        )
        self.assertEqual(output, "")

        self._publish(alias)
        alias.clear_cache()

        output = self.render_template_obj(
            self.alias_template,
            {"plugin": alias_plugin},
            self.get_request("/"),
        )
        self.assertEqual(output, "test")


class AliasTemplateTagAliasPlaceholderTestCase(BaseAliasPluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% static_alias "some_unique_id" %}"""  # noqa: E501

    def test_no_alias_rendered_when_no_alias_exists(self):
        alias = self._create_alias(static_code="")
        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=self.placeholder,
        )
        add_plugin(
            alias.get_placeholder(self.language),
            "TextPlugin",
            language=self.language,
            body="Content Alias 1234",
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                "plugin": alias_plugin,
            },
            self.get_request("/"),
        )
        self.assertEqual(output, "")

    def test_alias_rendered_when_alias_with_identifier_exists(self):
        alias = self._create_alias(static_code="some_unique_id")
        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=self.placeholder,
        )
        add_plugin(
            alias.get_placeholder(self.language),
            "TextPlugin",
            language=self.language,
            body="Content Alias 1234",
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                "plugin": alias_plugin,
            },
            self.get_request("/"),
        )

        self.assertEqual(output, "testContent Alias 1234")

    def test_alias_auto_creation_in_template(self):
        """
        When a template discovers a static code that doesn't exist:
            - A category is created if it doesn't exist
            - An alias is created if one doesn't exist that matches the static_code
            - The creation_method is recorded as created by a template
            - If versioning is enabled the tag is only created for a user that is logged in
        """
        alias_template = """{% load djangocms_alias_tags %}{% static_alias "category_unique_code" %}"""  # noqa: E501

        # No Alias or Category exist
        category = Category.objects.filter(translations__name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)
        alias = AliasModel.objects.filter(static_code="category_unique_code")

        self.assertEqual(category.count(), 0)
        self.assertEqual(alias.count(), 0)

        # If versioning is enabled the tag is only created for a user that is logged in
        if is_versioning_enabled():
            self.render_template_obj(alias_template, {}, self.get_request("/"))

            self.assertEqual(category.count(), 0)
            self.assertEqual(alias.count(), 0)

        with self.login_user_context(self.superuser):
            # A default category, and a new alias is created for the template tag
            self.render_template_obj(alias_template, {}, self.get_request("/"))

        category_result = category.first()
        alias_result = alias.first()

        self.assertEqual(category.count(), 1)
        self.assertEqual(category_result.name, DEFAULT_STATIC_ALIAS_CATEGORY_NAME)
        self.assertEqual(alias.count(), 1)
        self.assertEqual(alias_result.static_code, "category_unique_code")
        self.assertEqual(alias_result.creation_method, AliasModel.CREATION_BY_TEMPLATE)

    def test_alias_auto_creation_in_template_site_limited_alias(self):
        """
        When a template discovers a static code for a site and with no site with the same static_code
        entries are created for both scenarios
        """
        unlimited_template = """{% load djangocms_alias_tags %}{% static_alias "limited_alias_code" %}"""  # noqa: E501
        site_limited_template = """{% load djangocms_alias_tags %}{% static_alias "limited_alias_code" site %}"""  # noqa: E501
        site_id = 1

        with self.login_user_context(self.superuser):
            # A default category, and a new alias is created for the template tag
            self.render_template_obj(unlimited_template, {}, self.get_request("/"))
            self.render_template_obj(site_limited_template, {}, self.get_request("/"))

        alias = AliasModel.objects.filter(static_code="limited_alias_code")

        self.assertEqual(len(alias), 2)
        self.assertEqual(alias[0].static_code, "limited_alias_code")
        self.assertEqual(alias[0].site, None)
        self.assertEqual(alias[1].static_code, "limited_alias_code")
        self.assertEqual(alias[1].site.pk, site_id)

        # Render both templates again and be sure that the original tags are reused
        self.render_template_obj(unlimited_template, {}, self.get_request("/"))
        self.render_template_obj(site_limited_template, {}, self.get_request("/"))

        alias_requery = AliasModel.objects.filter(static_code="limited_alias_code")

        self.assertEqual(alias_requery.count(), 2)

    def test_site_limited_alias_displays_the_correct_contents(self):
        """
        The correct contents are shown when viewing the static alias in different sites.
        """
        unlimited_template = """{% load djangocms_alias_tags %}{% static_alias "site_limit_alias_code" %}"""  # noqa: E501
        site_limited_template = """{% load djangocms_alias_tags %}{% static_alias "site_limit_alias_code" site %}"""  # noqa: E501
        site1 = Site.objects.create(domain="site1.com", name="1")
        site2 = Site.objects.create(domain="site2.com", name="2")

        category = Category.objects.create(name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)

        unlimited_alias = self._create_alias(
            plugins=None,
            name="test alias",
            category=category,
            static_code="site_limit_alias_code",
            site=None,
        )
        site_limited_alias = self._create_alias(
            plugins=None,
            name="test alias",
            category=category,
            static_code="site_limit_alias_code",
            site=site2,
        )

        add_plugin(
            unlimited_alias.get_placeholder(self.language),
            "TextPlugin",
            language=self.language,
            body="unlimited text",
        )
        add_plugin(
            site_limited_alias.get_placeholder(self.language),
            "TextPlugin",
            language=self.language,
            body="site limited text",
        )

        # Should show the contents of the unlimited template
        with override_settings(SITE_ID=site1.pk):
            site1_unlimited_preview = self.render_template_obj(unlimited_template, {}, self.get_request("/"))
            site1_limited_preview = self.render_template_obj(site_limited_template, {}, self.get_request("/"))

        self.assertEqual(site1_unlimited_preview, "unlimited text")
        self.assertEqual(site1_limited_preview, "")

        # Should show the contents of the site limited template
        with override_settings(SITE_ID=site2.pk):
            site2_unlimited_preview = self.render_template_obj(unlimited_template, {}, self.get_request("/"))
            site2_limited_preview = self.render_template_obj(site_limited_template, {}, self.get_request("/"))

        self.assertEqual(site2_unlimited_preview, "unlimited text")
        self.assertEqual(site2_limited_preview, "site limited text")

    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_static_alias_shows_correct_content_for_versioning_states(self):
        """
        The correct contents are shown when viewing the static alias:
        - A draft page shows draft content
        - A published page shows published content or nothing at all
        """
        from djangocms_versioning.constants import PUBLISHED

        category = Category.objects.create(name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)
        alias = self._create_alias(
            plugins=None,
            name="test alias",
            category=category,
            published=True,
            static_code="template_example_global_alias_code",
        )
        add_plugin(
            alias.get_placeholder(language="en"),
            "TextPlugin",
            language="en",
            body="Published content for: template_example_global_alias_code",
        )
        page = create_page(
            title="Static Code Test",
            language="en",
            template="static_alias.html",
            limit_visibility_in_menu=None,
            created_by=self.superuser,
        )

        # Publish the page and create a draft alias
        self._publish(page, "en")
        version = self._get_version(alias, PUBLISHED, "en")
        draft = version.copy(self.superuser)

        # Add draft content to the draft version
        add_plugin(
            draft.content.placeholder,
            "TextPlugin",
            language="en",
            body="Updated Draft content for: template_example_global_alias_code",
        )
        try:
            page_content = page.get_title_obj("en")
        except AttributeError:
            page_content = page.get_content_obj("en")
        page_live_url = page.get_absolute_url()
        page_edit_url = get_object_edit_url(page_content, "en")
        page_preview_url = get_object_preview_url(page_content, "en")

        # The live page should still contain the published contents
        live_response = self.client.get(page_live_url)

        self.assertContains(live_response, "Published content for: template_example_global_alias_code")
        self.assertNotContains(
            live_response,
            "Updated Draft content for: template_example_global_alias_code",
        )

        # The edit and preview url should show the draft contents
        with self.login_user_context(self.superuser):
            edit_response = self.client.get(page_edit_url, follow=True)
            preview_response = self.client.get(page_preview_url, follow=True)

        self.assertContains(
            edit_response,
            "Updated Draft content for: template_example_global_alias_code",
        )
        self.assertContains(
            preview_response,
            "Updated Draft content for: template_example_global_alias_code",
        )

    def test_static_alias_creates_content_for_missing_languages(self):
        """
        If a static alias is used by a logged-in user a first (empty) alias content object is created
        if no content objects for the language exist
        """

        page = create_page(
            title="Static Code Test",
            language="en",
            template="static_alias.html",
            limit_visibility_in_menu=None,
            created_by=self.superuser,
        )
        create_page_content(
            title="Statischer Code-Test",
            language="de",
            page=page,
            template="static_alias.html",
            created_by=self.superuser,
        )
        self._publish(page, "en")
        self._publish(page, "de")
        if hasattr(page, "get_title_obj"):

            def page_edit_url(lang):
                return get_object_edit_url(page.get_title_obj(lang))
        else:

            def page_edit_url(lang):
                return get_object_edit_url(page.get_content_obj(lang), language=lang)

        with self.login_user_context(self.superuser):
            self.client.get(page_edit_url("en"), follow=True)  # supposed to create the alias and alias content for en
            self.client.get(page_edit_url("en"), follow=True)  # supposed to create no additional object
            self.client.get(page_edit_url("de"), follow=True)  # supposed to create the alias content for de

        alias = AliasModel.objects.filter(static_code="template_example_global_alias_code").first()

        self.assertIsNotNone(alias, "Alias not created")
        self.assertIsNotNone(alias.get_content("en", show_draft_content=True))
        self.assertIsNotNone(alias.get_content("de", show_draft_content=True))
        # Ensure that exactly two content objects have been created
        self.assertEqual(alias.contents(manager="admin_manager").count(), 2)

    def test_alias_rendered_when_identifier_is_variable(self):
        alias_template = """{% load djangocms_alias_tags %}{% static_alias foo_variable %}"""  # noqa: E501

        alias = self._create_alias(static_code="some_unique_id")
        add_plugin(
            alias.get_placeholder(self.language),
            "TextPlugin",
            language=self.language,
            body="Content Alias 1234",
        )

        output = self.render_template_obj(
            alias_template,
            {"foo_variable": "some_unique_id"},
            self.get_request("/"),
        )

        self.assertEqual(output, "Content Alias 1234")
