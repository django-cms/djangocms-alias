from cms.api import add_plugin

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.constants import SELECT2_ALIAS_URL_NAME
from djangocms_alias.forms import AliasPluginForm, AliasSelectWidget
from djangocms_alias.utils import alias_plugin_reverse

from .base import BaseAliasPluginTestCase


class AliasCreatePluginTestCase(BaseAliasPluginTestCase):

    def test_create_alias_plugin_form_initial_category(self):
        alias = self._create_alias(
            self.placeholder.get_plugins(),
        )
        alias_plugin = add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        form = AliasPluginForm(instance=alias_plugin)
        self.assertEqual(form.fields['category'].initial, alias.category_id)

    def test_get_alias_content_default_render_template(self):
        alias = self._create_alias(
            self.placeholder.get_plugins(),
        )
        alias_content = alias.get_content(self.language)

        self.assertEqual(alias_content.template, 'default')

    def test_create_alias_plugin_form_empty_category(self):
        form = AliasPluginForm()
        self.assertEqual(form.fields['category'].initial, None)

    def test_alias_widget_attrs_include_select2_view_url(self):
        widget = AliasSelectWidget()
        attrs = widget.build_attrs({})
        self.assertIn('data-select2-url', attrs)
        self.assertEqual(
            attrs['data-select2-url'],
            alias_plugin_reverse(SELECT2_ALIAS_URL_NAME),
        )
