from unittest import skipUnless

from cms.api import add_plugin

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


# TODO:
# Fixed to site and not to site

# Generated by code and by template, what about category here? get_or_create static category?
# Get or create in various scenarios
# Versioned draft content won't then create a new grouper!!!
# Should not be able to delete a static alias!

# Category is required so needs to be set.
# Same identifier used for single site and multisite?

# Scenario: Project wide Static Alias "global-alias-1"
#           alias_template = """{% load djangocms_alias_tags %}{% static_alias "global-alias-1" %}"""  # noqa: E501
#           Create generic category constants.STATIC_ALIAS_CATEGORY_NAME
#
