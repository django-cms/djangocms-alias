from unittest import skipUnless

from cms.api import add_plugin

from djangocms_alias.cms_plugins import Alias
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
    alias_template = """{% load djangocms_alias_tags %}{% alias_placeholder "some_uniquer_id" %}"""  # noqa: E501

    def test_no_alias_rendered_when_no_alias_exists(self):
        alias = self._create_alias(identifier="")
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
        alias = self._create_alias(identifier="some_uniquer_id")
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
