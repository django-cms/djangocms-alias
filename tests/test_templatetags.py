from cms.api import add_plugin

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.templatetags.djangocms_alias_tags import get_alias_url

from .base import BaseAliasPluginTestCase


class AliasTemplateTagsTestCase(BaseAliasPluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% render_alias plugin.alias %}"""  # noqa: E501

    def test_get_alias_url(self):
        alias = self._create_alias([self.plugin])
        self.assertEqual(
            get_alias_url(alias),
            self.DETAIL_ALIAS_ENDPOINT(alias.pk),
        )

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
        self.assertEqual(output, 'test\n')
