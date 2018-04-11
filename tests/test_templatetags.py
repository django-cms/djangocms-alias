from cms.api import add_plugin

from djangocms_alias.models import Category
from djangocms_alias.templatetags.djangocms_alias_tags import (
    get_alias_categories,
    get_alias_url,
)

from .base import BaseAlias2PluginTestCase


class Alias2TemplateTagsTestCase(BaseAlias2PluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% render_alias2_plugin plugin %}"""  # noqa: E501

    def test_get_alias_categories(self):
        Category.objects.bulk_create(
            Category(name=name) for name in (
                'foo', 'bar', 'baz',
            )
        )
        categories = get_alias_categories()
        self.assertEqual(
            list(categories.values_list('name', flat=True)),
            ['bar', 'baz', 'foo', 'test category'],
        )

    def test_get_alias_url(self):
        alias = self._create_alias(
            [self.plugin],
        )
        self.assertEqual(
            get_alias_url(alias),
            self.DETAIL_ALIAS_ENDPOINT(alias.pk),
        )

    def test_render_alias2_plugin_no_plugin(self):
        output = self.render_template_obj(
            self.alias_template,
            {},
            self.get_request('/'),
        )
        self.assertEqual(output, '')

    def test_render_alias2_plugin(self):
        alias = self._create_alias(
            [self.plugin],
        )
        alias_plugin = self.alias_plugin_base.replace_placeholder_content_with_alias(  # noqa: E501
            self.placeholder,
            alias,
            self.language,
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, 'test')

    def test_render_alias2_plugin_no_placeholder(self):
        alias = self._create_alias(
            [self.plugin],
        )
        alias.placeholder.delete()
        alias_plugin = self.alias_plugin_base.replace_placeholder_content_with_alias(  # noqa: E501
            self.placeholder,
            alias,
            self.language,
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, '')

    def test_render_alias2_plugin_includes_recursed_alias(self):
        alias = self._create_alias(
            [self.plugin],
        )
        add_plugin(
            alias.placeholder,
            self.alias_plugin_base.__class__,
            language=self.language,
            alias=alias,
        )
        alias_plugin = self.alias_plugin_base.replace_placeholder_content_with_alias(  # noqa: E501
            self.placeholder,
            alias,
            self.language,
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, 'test\n')
