from unittest import skipUnless

from cms.api import add_plugin

from django.contrib.sites.models import Site
from django.test.utils import override_settings

from djangocms_alias.constants import DEFAULT_STATIC_ALIAS_CATEGORY_NAME
from djangocms_alias.cms_plugins import Alias
from djangocms_alias.models import Category, Alias as AliasModel
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
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, 'test')

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
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, 'test')

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
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
            {'plugin': alias_plugin},
            self.get_request('/'),
        )
        self.assertEqual(output, '')

        self._publish(alias)
        alias.clear_cache()

        output = self.render_template_obj(
            self.alias_template,
            {'plugin': alias_plugin},
            self.get_request('/'),
        )
        self.assertEqual(output, 'test')


class AliasTemplateTagAliasPlaceholderTestCase(BaseAliasPluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% static_alias "some_unique_id" %}"""  # noqa: E501

    def test_no_alias_rendered_when_no_alias_exists(self):
        alias = self._create_alias(static_code="")
        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=self.placeholder,
        )
        add_plugin(
            alias.get_placeholder(self.language),
            'TextPlugin',
            language=self.language,
            body='Content Alias 1234',
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, "")

    def test_alias_rendered_when_alias_with_identifier_exists(self):
        alias = self._create_alias(static_code="some_unique_id")
        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=self.placeholder,
        )
        add_plugin(
            alias.get_placeholder(self.language),
            'TextPlugin',
            language=self.language,
            body='Content Alias 1234',
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, "testContent Alias 1234")

    def test_alias_auto_creation_in_template(self):
        """
        When a template discovers a static code that doesn't exist:
            - A category is created if it doesn't exist
            - An alias is created if one doesn't exist that matches the static_code
        """
        alias_template = """{% load djangocms_alias_tags %}{% static_alias "category_unique_code" %}"""  # noqa: E501

        # No Alias or Category exist
        category = Category.objects.filter(translations__name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)
        alias = AliasModel.objects.filter(static_code="category_unique_code")

        self.assertEqual(category.count(), 0)
        self.assertEqual(alias.count(), 0)

        # A default category, and a new alias is created for the template tag
        self.render_template_obj(alias_template, {}, self.get_request('/'))

        self.assertEqual(category.count(), 1)
        self.assertEqual(category.first().name, DEFAULT_STATIC_ALIAS_CATEGORY_NAME)
        self.assertEqual(alias.count(), 1)
        self.assertEqual(alias.first().static_code, "category_unique_code")

    def test_alias_auto_creation_in_template_site_limited_alias(self):
        """
        When a template discovers a static code for a site and with no site with the same static_code
        TODO:
            - What should happen?
        """
        unlimited_template = """{% load djangocms_alias_tags %}{% static_alias "limited_alias_code" %}"""  # noqa: E501
        site_limited_template = """{% load djangocms_alias_tags %}{% static_alias "limited_alias_code" site %}"""  # noqa: E501
        site_id = 1

        # A default category, and a new alias is created for the template tag
        self.render_template_obj(unlimited_template, {}, self.get_request('/'))
        self.render_template_obj(site_limited_template, {}, self.get_request('/'))

        alias = AliasModel.objects.filter(static_code="limited_alias_code")

        self.assertEqual(len(alias), 2)
        self.assertEqual(alias[0].static_code, "limited_alias_code")
        self.assertEqual(alias[0].site, None)
        self.assertEqual(alias[1].static_code, "limited_alias_code")
        self.assertEqual(alias[1].site.pk, site_id)

        # Render both templates again and be sure that the original tags are reused
        self.render_template_obj(unlimited_template, {}, self.get_request('/'))
        self.render_template_obj(site_limited_template, {}, self.get_request('/'))

        alias_requery = AliasModel.objects.filter(static_code="limited_alias_code")

        self.assertEqual(alias_requery.count(), 2)

    def test_site_limited_alias_displays_the_correct_contents(self):
        """
        The correct contents are shown when viewing the static alias in different sites.
        """
        unlimited_template = """{% load djangocms_alias_tags %}{% static_alias "site_limit_alias_code" %}"""  # noqa: E501
        site_limited_template = """{% load djangocms_alias_tags %}{% static_alias "site_limit_alias_code" site %}"""  # noqa: E501
        site1 = Site.objects.create(domain='site1.com', name='1')
        site2 = Site.objects.create(domain='site2.com', name='2')

        category = Category.objects.create(name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)

        unlimited_alias = self._create_alias(
            plugins=None, name='test alias', category=category, static_code="site_limit_alias_code", site=None)
        site_limited_alias = self._create_alias(
            plugins=None, name='test alias', category=category, static_code="site_limit_alias_code", site=site2)

        add_plugin(
            unlimited_alias.get_placeholder(self.language),
            'TextPlugin',
            language=self.language,
            body='unlimited text',
        )
        add_plugin(
            site_limited_alias.get_placeholder(self.language),
            'TextPlugin',
            language=self.language,
            body='site limited text',
        )

        # Should show the contents of the unlimited template
        with override_settings(SITE_ID=site1.pk):
            site1_unlimited_preview = self.render_template_obj(unlimited_template, {}, self.get_request('/'))
            site1_limited_preview = self.render_template_obj(site_limited_template, {}, self.get_request('/'))

        self.assertEqual(site1_unlimited_preview, "unlimited text")
        # FIXME: The limited preview should fall back if no entries exist for the site?
        #self.assertEqual(site1_limited_preview, "unlimited text")

        # Should show the contents of the site limited template
        with override_settings(SITE_ID=site2.pk):
            site2_unlimited_preview = self.render_template_obj(unlimited_template, {}, self.get_request('/'))
            site2_limited_preview = self.render_template_obj(site_limited_template, {}, self.get_request('/'))

        self.assertEqual(site1_unlimited_preview, "unlimited text")
        self.assertEqual(site1_limited_preview, "site limited text")

# TODO:
# - Test with Versions!
#  Static placeholders should:
#  - be fixed to site and not to site

# Generated by code and by template, what about category here? get_or_create static category?
# Get or create in various scenarios
# Versioned draft content won't then create a new grouper!!!

# Category is required so needs to be set.
# Same identifier used for single site and multisite?

# Scenario: Project wide Static Alias "global-alias-1"
#           alias_template = """{% load djangocms_alias_tags %}{% static_alias "global-alias-1" %}"""  # noqa: E501
#           Create generic category constants.STATIC_ALIAS_CATEGORY_NAME
#
