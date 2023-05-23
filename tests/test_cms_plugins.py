from operator import attrgetter
from unittest import skipUnless
from urllib.parse import urlparse

from cms.api import add_plugin, create_title
from cms.utils import get_current_site
from cms.utils.plugins import downcast_plugins
from cms.utils.urlutils import admin_reverse

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.constants import SELECT2_ALIAS_URL_NAME
from djangocms_alias.forms import AliasPluginForm, AliasSelectWidget
from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class AliasPluginTestCase(BaseAliasPluginTestCase):

    def test_extra_plugin_items_for_regular_plugins(self):
        extra_items = Alias.get_extra_plugin_menu_items(
            self.get_request(self.page.get_absolute_url()),
            self.plugin,
        )
        self.assertEqual(len(extra_items), 1)
        extra_item = extra_items[0]
        self.assertEqual(extra_item.name, 'Create Alias')
        self.assertEqual(extra_item.action, 'modal')
        parsed_url = urlparse(extra_item.url)
        self.assertEqual(parsed_url.path, self.get_create_alias_endpoint())
        self.assertIn(f'plugin={self.plugin.pk}', parsed_url.query)

    def test_extra_plugin_items_for_alias_plugins(self):
        alias = self._create_alias()

        placeholder = self.placeholder
        page_content = None
        if is_versioning_enabled():
            # Can only edit page/content that is in DRAFT
            page_content = create_title(self.language, 'Draft Page', self.page, created_by=self.superuser)
            placeholder = page_content.get_placeholders().get(slot='content')

        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=placeholder,
        )
        extra_items = Alias.get_extra_plugin_menu_items(
            self.get_page_request(page=self.page, obj=page_content, user=self.superuser),
            alias_plugin,
        )

        self.assertEqual(len(extra_items), 2)
        first, second = extra_items
        self.assertEqual(first.name, 'Edit Alias')
        self.assertEqual(first.url, alias.get_absolute_url())
        self.assertEqual(first.action, 'sideframe')

        self.assertEqual(second.name, 'Detach Alias')
        self.assertEqual(second.action, 'modal')
        self.assertEqual(
            second.url,
            self.get_detach_alias_plugin_endpoint(alias_plugin.pk),
        )

    def test_extra_plugin_items_for_placeholder(self):
        extra_items = Alias.get_extra_placeholder_menu_items(
            self.get_page_request(page=self.page, user=self.superuser),
            self.placeholder,
        )
        self.assertEqual(len(extra_items), 1)
        extra_item = extra_items[0]
        self.assertEqual(extra_item.name, 'Create Alias')
        self.assertEqual(extra_item.action, 'modal')
        parsed_url = urlparse(extra_item.url)
        self.assertEqual(parsed_url.path, self.get_create_alias_endpoint())
        self.assertIn(
            f'placeholder={self.placeholder.pk}',
            parsed_url.query,
        )

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
    def test_extra_plugin_items_with_versioning_checks(self):
        alias = self._create_alias()
        alias_plugin = alias.get_content(self.language).populate(
            replaced_placeholder=self.placeholder,
        )
        try:
            _obj = self.page.get_title_obj()
        except AttributeError:
            _obj = self.page.get_content_obj()
        extra_items = Alias.get_extra_plugin_menu_items(
            self.get_page_request(page=self.page, obj=_obj, user=self.superuser),
            alias_plugin,
        )

        self.assertEqual(len(extra_items), 1)
        first = extra_items[0]
        # We cannot detach alias on undraft page
        self.assertEqual(first.name, 'Edit Alias')
        self.assertEqual(first.url, alias.get_absolute_url())

    def test_rendering_plugin_on_page(self):
        alias = self._create_alias(published=True)
        add_plugin(
            alias.get_placeholder(self.language),
            'TextPlugin',
            language=self.language,
            body='Content Alias 1234',
        )
        add_plugin(
            alias.get_placeholder(self.language),
            Alias,
            language=self.language,
            alias=alias,
        )
        add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(self.page.get_absolute_url(self.language))

        self.assertContains(response, 'Content Alias 1234')

    def test_detach_alias(self):
        alias = self._create_alias()
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        alias_plugin = add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )

        self.assertEqual(plugins.count(), 2)
        Alias.detach_alias_plugin(alias_plugin, self.language)
        self.assertEqual(plugins.count(), 4)

    def test_detach_alias_correct_position(self):
        alias = self._create_alias([])
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias_placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        alias_plugin = add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        self.assertEqual(plugins.count(), 3)
        Alias.detach_alias_plugin(alias_plugin, self.language)
        self.assertEqual(plugins.count(), 4)

        ordered_plugins = sorted(
            downcast_plugins(plugins),
            key=attrgetter('position'),
        )
        self.assertEqual(
            [str(plugin) for plugin in ordered_plugins],
            ['test', 'test 1', 'test 2', 'test 3'],
        )

    def test_create_alias_with_default_render_template(self):
        alias = self._create_alias()
        add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        self.assertEqual(alias.cms_plugins.first().template, 'default')

    def test_create_alias_with_custom_render_template(self):
        alias_template = 'custom_alias_template'
        alias = self._create_alias()
        add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
            template=alias_template,
        )
        self.assertEqual(alias.cms_plugins.first().template, alias_template)

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
        self.assertEqual(form.fields['category'].initial, alias.category)

    def test_create_alias_plugin_form_empty_category(self):
        form = AliasPluginForm()
        self.assertEqual(form.fields['category'].initial, None)

    def test_alias_widget_attrs_include_select2_view_url(self):
        widget = AliasSelectWidget()
        attrs = widget.build_attrs({})
        self.assertIn('data-select2-url', attrs)
        self.assertEqual(
            attrs['data-select2-url'],
            admin_reverse(SELECT2_ALIAS_URL_NAME),
        )

    def test_create_alias_from_plugin_list(self):
        plugins = self.placeholder.get_plugins()
        alias = self._create_alias(plugins)
        self.assertEqual(
            plugins[0].plugin_type,
            alias.get_placeholder(self.language).get_plugins()[0].plugin_type,
        )
        self.assertEqual(
            plugins[0].get_bound_plugin().body,
            alias.get_placeholder(self.language).get_plugins()[0].get_bound_plugin().body,
        )

    def test_replace_plugin_with_alias(self):
        alias = self._create_alias([self.plugin])
        alias_content = alias.get_content(self.language)
        alias_plugin = alias_content.populate(
            replaced_plugin=self.plugin,
        )
        plugins = self.placeholder.get_plugins()
        self.assertNotIn(
            self.plugin,
            plugins,
        )
        self.assertEqual(plugins[0].get_bound_plugin(), alias_plugin)
        self.assertEqual(alias_content.placeholder.get_plugins()[0].get_bound_plugin().body, 'test')  # noqa: E501

    def test_replace_plugin_with_alias_correct_position(self):
        second_plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        alias = self._create_alias()
        alias_plugin = alias.get_content(self.language).populate(replaced_plugin=second_plugin)
        plugins = self.placeholder.get_plugins()
        self.assertNotIn(
            self.plugin,
            plugins,
        )
        self.assertEqual(plugins[1].get_bound_plugin(), alias_plugin)

        ordered_plugins = sorted(
            downcast_plugins(plugins),
            key=attrgetter('position'),
        )

        self.assertEqual(
            [plugin.plugin_type for plugin in ordered_plugins],
            ['TextPlugin', 'Alias', 'TextPlugin'],
        )

    def test_replace_placeholder_content_with_alias(self):
        add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        alias = self._create_alias()
        alias_content = alias.get_content(self.language)
        alias_content.populate(replaced_placeholder=self.placeholder)
        plugins = self.placeholder.get_plugins()

        self.assertEqual(plugins.count(), 1)
        self.assertEqual(alias_content.placeholder.get_plugins().count(), 2)
        self.assertEqual(
            alias_content.placeholder.get_plugins()[1].get_bound_plugin().body,
            'test 2',
        )

    def test_create_alias_plugin_form_initial_site(self):
        """
        By default the initial values should be set
        for the current site preselected and with no
        category set.
        """
        current_site = get_current_site()

        # Initially load the empty add form
        form = AliasPluginForm(data={})

        self.assertEqual(form.fields['site'].initial, current_site)
        self.assertEqual(form.fields['category'].initial, None)

    def test_change_alias_plugin_form_initial_site(self):
        """
        By default, the initial values should be set
        that are taken from the alias object currently selected
        """
        current_site = get_current_site()
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

        self.assertNotEqual(form.fields['site'].initial, alias.site)
        self.assertEqual(form.fields['site'].initial, current_site)
        self.assertEqual(form.fields['category'].initial, alias.category)
        self.assertNotEqual(form.fields['category'].initial, None)
