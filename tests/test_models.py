from distutils.version import LooseVersion

from django import get_version
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.urls import reverse

from cms.api import add_plugin, create_title
from cms.models import Placeholder

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.models import Alias as AliasModel, AliasContent, Category
from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


DJANGO_VERSION = get_version()
DJANGO_4_0 = LooseVersion(DJANGO_VERSION) < LooseVersion('4.1')


class AliasModelsTestCase(BaseAliasPluginTestCase):

    def _get_aliases_positions(self, category):
        return dict(category.aliases.values_list('position', 'pk'))

    def test_alias_placeholder_slot_save_again(self):
        alias = self._create_alias(self.placeholder.get_plugins())
        alias_placeholder = alias.get_placeholder(self.language)
        slot_name = alias_placeholder.slot
        alias.save()
        self.assertEqual(alias_placeholder.slot, slot_name)

    def test_alias_placeholder_name(self):
        alias = self._create_alias(
            self.placeholder.get_plugins(),
            name='test alias 2',
        )
        self.assertEqual(str(alias), 'test alias 2')

    def test_alias_is_not_recursive(self):
        alias = self._create_alias(
            self.placeholder.get_plugins(),
        )
        alias_plugin = add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        self.assertFalse(alias_plugin.is_recursive())

    def test_alias_is_recursive(self):
        alias = self._create_alias(
            self.placeholder.get_plugins(),
        )
        recursed_alias_plugin = add_plugin(
            alias.get_placeholder(self.language),
            Alias,
            language=self.language,
            alias=alias,
        )
        self.assertTrue(recursed_alias_plugin.is_recursive())

    def test_alias_is_recursive_with_custom_template(self):
        alias = self._create_alias(
            self.placeholder.get_plugins(),
        )
        recursive_alias_plugin = add_plugin(
            alias.get_placeholder(self.language),
            Alias,
            language=self.language,
            alias=alias,
            template='custom_alias_template'
        )
        self.assertTrue(recursive_alias_plugin.is_recursive())

    def test_increment_position_for_newly_created_instances(self):
        category1 = Category.objects.create(
            name='Cat 1',
        )
        category2 = Category.objects.create(
            name='Cat 2',
        )
        alias1cat1 = AliasModel.objects.create(category=category1)
        alias1cat2 = AliasModel.objects.create(category=category2)
        alias2cat2 = AliasModel.objects.create(category=category2)
        alias2cat1 = AliasModel.objects.create(category=category1)

        self.assertEqual(
            self._get_aliases_positions(alias1cat1.category),
            {0: alias1cat1.pk, 1: alias2cat1.pk},
        )
        self.assertEqual(
            self._get_aliases_positions(alias1cat2.category),
            {0: alias1cat2.pk, 1: alias2cat2.pk},
        )

    def test_save_and_delete_inc_dec_of_position_delete_first(self):
        alias1 = AliasModel.objects.create(category=self.category)
        alias2 = AliasModel.objects.create(category=self.category)
        alias3 = AliasModel.objects.create(category=self.category)
        alias4 = AliasModel.objects.create(category=self.category)

        alias1.delete()
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias2.pk, 1: alias3.pk, 2: alias4.pk},
        )

    def test_save_and_delete_inc_dec_of_position_delete_in_the_middle(self):
        alias1 = AliasModel.objects.create(category=self.category)
        alias2 = AliasModel.objects.create(category=self.category)
        alias3 = AliasModel.objects.create(category=self.category)

        alias2.delete()
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias1.pk, 1: alias3.pk},
        )

    def test_save_and_delete_inc_dec_of_position_delete_last(self):
        alias1 = AliasModel.objects.create(category=self.category)
        alias2 = AliasModel.objects.create(category=self.category)
        alias3 = AliasModel.objects.create(category=self.category)

        alias3.delete()
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias1.pk, 1: alias2.pk},
        )

    def test_set_position_dont_change_position_in_other_categories(self):
        category1 = Category.objects.create(
            name='Cat 1',
        )
        category2 = Category.objects.create(
            name='Cat 2',
        )
        alias1cat1 = AliasModel.objects.create(category=category1)  # 0
        alias2cat1 = AliasModel.objects.create(category=category1)  # 1
        alias1cat2 = AliasModel.objects.create(category=category2)  # 0
        alias2cat2 = AliasModel.objects.create(category=category2)  # 1

        alias1cat1._set_position(alias2cat1.position)
        self.assertEqual(
            self._get_aliases_positions(alias1cat1.category),
            {0: alias2cat1.pk, 1: alias1cat1.pk},
        )
        self.assertEqual(
            self._get_aliases_positions(alias1cat2.category),
            {0: alias1cat2.pk, 1: alias2cat2.pk},
        )

    def test_set_position_moving_up(self):
        alias1 = AliasModel.objects.create(category=self.category)  # 0
        alias2 = AliasModel.objects.create(category=self.category)  # 1
        alias3 = AliasModel.objects.create(category=self.category)  # 2
        alias4 = AliasModel.objects.create(category=self.category)  # 3

        alias3._set_position(1)
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias1.pk, 1: alias3.pk, 2: alias2.pk, 3: alias4.pk},
        )

    def test_set_position_moving_down(self):
        alias1 = AliasModel.objects.create(category=self.category)  # 0
        alias2 = AliasModel.objects.create(category=self.category)  # 1
        alias3 = AliasModel.objects.create(category=self.category)  # 2
        alias4 = AliasModel.objects.create(category=self.category)  # 3

        alias2._set_position(2)
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias1.pk, 1: alias3.pk, 2: alias2.pk, 3: alias4.pk},
        )

    def test_set_position_moving_up_from_end_to_start(self):
        alias1 = AliasModel.objects.create(category=self.category)  # 0
        alias2 = AliasModel.objects.create(category=self.category)  # 1
        alias3 = AliasModel.objects.create(category=self.category)  # 2
        alias4 = AliasModel.objects.create(category=self.category)  # 3

        alias4._set_position(0)
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias4.pk, 1: alias1.pk, 2: alias2.pk, 3: alias3.pk},
        )

    def test_set_position_moving_down_from_start_to_end(self):
        alias1 = AliasModel.objects.create(category=self.category)  # 0
        alias2 = AliasModel.objects.create(category=self.category)  # 1
        alias3 = AliasModel.objects.create(category=self.category)  # 2
        alias4 = AliasModel.objects.create(category=self.category)  # 3

        alias1._set_position(3)
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias2.pk, 1: alias3.pk, 2: alias4.pk, 3: alias1.pk},
        )

    def test_pages_using_alias(self):
        site1 = Site.objects.create(domain='site1.com', name='1')
        site2 = Site.objects.create(domain='site2.com', name='2')
        alias = self._create_alias(name='alias')

        site1_page = self._create_page(
            title='Site1',
            language=self.language,
            site=site1,
        )
        self.add_alias_plugin_to_page(site1_page, alias)
        # Should show on the list

        nested_page1 = self._create_page(
            title='Site1 nested page 1',
            language=self.language,
            site=site1,
            parent=site1_page,
        )
        self.add_alias_plugin_to_page(nested_page1, alias)
        self.add_alias_plugin_to_page(nested_page1, alias)
        # Should show on the list only once

        nested_page2 = self._create_page(
            title='Site1 nested page 2',
            language=self.language,
            site=site1,
            parent=site1_page,
        )
        self.add_alias_plugin_to_page(nested_page2, alias)
        # Should show on the list

        nested_page3 = self._create_page(
            title='Site1 nested page 3',
            language=self.language,
            site=site1,
            parent=site1_page,
        )  # Not show on the list

        deep_nested_page4 = self._create_page(
            title='Site1 deep nested page 4',
            language=self.language,
            site=site1,
            parent=nested_page3,
        )
        self.add_alias_plugin_to_page(deep_nested_page4, alias)
        # Should show on the list

        site2_page = self._create_page(
            title='Site2',
            language='de',
            site=site2,
        )
        self.add_alias_plugin_to_page(site2_page, alias, 'de')

        if is_versioning_enabled():
            create_title('en', 'Site2 EN', site2_page, created_by=self.superuser)
            self._publish(site2_page, 'en')
        else:
            create_title('en', 'Site2 EN', site2_page)

        self.add_alias_plugin_to_page(site2_page, alias, 'en')
        # Should show on the list only once

        with self.assertNumQueries(3):
            objects = alias.objects_using

        self.assertEqual(
            sorted(obj.pk for obj in objects),
            [
                site1_page.pk,
                nested_page1.pk,
                nested_page2.pk,
                deep_nested_page4.pk,
                site2_page.pk,
            ]
        )

    def test_aliases_using_alias(self):
        root_alias = self._create_alias(name='root alias')
        if not is_versioning_enabled():
            # TODO: fix it after versioning will have multilanguage support
            AliasContent.objects.create(
                name='root alias de',
                alias=root_alias,
                language='de',
            )
            AliasContent.objects.create(
                name='root alias it',
                alias=root_alias,
                language='it',
            )
        root_alias2 = self._create_alias(name='root alias 2')

        alias1 = self._create_alias(name='alias 1')
        alias2 = self._create_alias(name='alias 2')
        alias3 = self._create_alias(name='alias 3')
        alias4 = self._create_alias(name='alias 4')

        add_plugin(
            root_alias.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=alias1,
        )
        if not is_versioning_enabled():
            # TODO: fix it after versioning will have multilanguage support
            add_plugin(
                root_alias.get_placeholder('de'),
                'Alias',
                language='de',
                alias=alias1,
            )
            add_plugin(
                root_alias.get_placeholder('it'),
                'Alias',
                language='it',
                alias=alias1,
            )
        # Alias1 should show only once
        add_plugin(
            root_alias.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=alias2,
        )
        add_plugin(
            root_alias2.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=alias2,
        )
        add_plugin(
            alias2.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=alias3,
        )
        add_plugin(
            alias3.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=alias4,
        )

        with self.assertNumQueries(3):
            objects = alias1.objects_using
        self.assertEqual(
            sorted(obj.pk for obj in objects),
            [root_alias.pk],
        )

        with self.assertNumQueries(3):
            objects = alias2.objects_using
        self.assertEqual(
            sorted(obj.pk for obj in objects),
            [root_alias.pk, root_alias2.pk],
        )

        with self.assertNumQueries(3):
            objects = alias3.objects_using
        self.assertEqual(
            sorted(obj.pk for obj in objects),
            [alias2.pk],
        )

        with self.assertNumQueries(3):
            objects = alias4.objects_using
        self.assertEqual(
            sorted(obj.pk for obj in objects),
            [alias3.pk],
        )

    def test_pages_and_aliases_using_objects(self):
        alias = self._create_alias()
        root_alias = self._create_alias(name='root alias')
        add_plugin(
            root_alias.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=alias,
        )
        self.add_alias_plugin_to_page(self.page, alias, 'en')
        with self.assertNumQueries(5):
            objects = alias.objects_using
        self.assertEqual(
            sorted(obj.pk for obj in objects),
            [self.page.pk, root_alias.pk],
        )

    def test_delete(self):
        self.page.delete()

        alias = self._create_alias([self.plugin])
        add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        self.assertEqual(Placeholder.objects.count(), 1)
        alias.delete()
        self.assertFalse(alias.__class__.objects.filter(pk=alias.pk).exists())
        if DJANGO_4_0:
            self.assertEqual(alias.cms_plugins.count(), 0)
        self.assertEqual(Placeholder.objects.count(), 0)
        alias.save()  # Django 4.1+ disallows to use relations (cmsplugins) of unsaved objects.
        self.assertEqual(alias.cms_plugins.count(), 0)

    def test_category_get_absolute_url(self):
        """
        Category uses the admin change view as its absolute url
        """
        category = Category.objects.create(name="Test Category")

        app_label = category._meta.app_label
        expected = reverse(
            f"admin:{app_label}_category_change", args=[category.pk]
        )

        self.assertEqual(category.get_absolute_url(), expected)

    def test_category_name_same_across_languages(self):
        """
        Category name may be the same across languages
        """
        category = Category.objects.create(name='Samename A')
        category.set_current_language('de')
        category.name = "Samename A"
        try:
            category.validate_unique()
        except ValidationError:
            self.fail("Same Category name should be allowed across two languages.")

        category.set_current_language('en')
        self.assertEqual(category.name, 'Samename A')
        category.set_current_language('de')
        self.assertEqual(category.name, 'Samename A')

    def test_category_name_unique_for_language(self):
        """
        Category name can't be the same in one language for two different categories
        """
        with self.login_user_context(self.superuser):
            Category.objects.create(name='Samename B')
            c = Category(name='Samename B')
            self.assertRaises(ValidationError, c.validate_unique)
