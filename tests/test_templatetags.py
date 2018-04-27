from cms.api import add_plugin

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.models import Category
from djangocms_alias.templatetags.djangocms_alias_tags import (
    get_alias_categories,
    get_alias_url,
)

from .base import BaseAliasPluginTestCase


class AliasTemplateTagsTestCase(BaseAliasPluginTestCase):
    alias_template = """{% load djangocms_alias_tags %}{% render_alias plugin.alias %}"""  # noqa: E501
    breadcrumb_template = """{% load djangocms_alias_tags %}{% show_alias_breadcrumb %}"""  # noqa: E501

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

    def test_render_alias_nopublished(self):
        alias = self._create_alias()
        alias_plugin = alias.populate(
            language=self.language,
            replaced_placeholder=self.placeholder,
        )

        output = self.render_template_obj(
            self.alias_template,
            {
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, '<div class="cms-alias"></div>\n')

    def test_render_alias_published(self):
        alias = self._create_alias()
        alias_plugin = alias.populate(
            language=self.language,
            replaced_placeholder=self.placeholder,
        )
        alias.publish(self.language)

        output = self.render_template_obj(
            self.alias_template,
            {
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, '<div class="cms-alias">test</div>\n')

    def test_render_alias_includes_recursed_alias(self):
        alias = self._create_alias()
        add_plugin(
            alias.draft_content,
            Alias,
            language=self.language,
            alias=alias,
        )
        alias_plugin = alias.populate(
            language=self.language,
            replaced_placeholder=self.placeholder,
        )
        alias.publish(self.language)

        output = self.render_template_obj(
            self.alias_template,
            {
                'plugin': alias_plugin,
            },
            self.get_request('/'),
        )
        self.assertEqual(output, '<div class="cms-alias">test\n</div>\n')

    def test_show_alias_breadcrumb(self):
        alias = self._create_alias()

        output = self.render_template_obj(
            self.breadcrumb_template,
            {'object': alias},
            self.get_alias_request(alias, user=self.superuser),
        )
        self.assertIn('Categories', output)
        self.assertIn(self.LIST_CATEGORY_ENDPOINT, output)
        self.assertIn(alias.category.name, output)
        self.assertIn(self.DETAIL_CATEGORY_ENDPOINT(alias.category.pk), output)
        self.assertIn(alias.name, output)
        self.assertNotIn(self.DETAIL_ALIAS_ENDPOINT(alias.pk), output)

        output = self.render_template_obj(
            self.breadcrumb_template,
            {'object': alias.category},
            self.get_alias_request(alias, user=self.superuser),
        )
        self.assertIn('Categories', output)
        self.assertIn(self.LIST_CATEGORY_ENDPOINT, output)
        self.assertIn(alias.category.name, output)
        self.assertNotIn(self.DETAIL_CATEGORY_ENDPOINT(alias.category.pk), output)  # noqa: E501
        self.assertNotIn(alias.name, output)
        self.assertNotIn(self.DETAIL_ALIAS_ENDPOINT(alias.pk), output)

        output = self.render_template_obj(
            self.breadcrumb_template,
            {},
            self.get_alias_request(alias, user=self.superuser),
        )
        self.assertIn('Categories', output)
        self.assertNotIn(self.LIST_CATEGORY_ENDPOINT, output)
        self.assertNotIn(alias.category.name, output)
        self.assertNotIn(self.DETAIL_CATEGORY_ENDPOINT(alias.category.pk), output)  # noqa: E501
        self.assertNotIn(alias.name, output)
        self.assertNotIn(self.DETAIL_ALIAS_ENDPOINT(alias.pk), output)
