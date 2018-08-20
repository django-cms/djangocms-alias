from django.contrib.sites.models import Site

from cms.api import add_plugin, create_page
from cms.test_utils.util.fuzzy_int import FuzzyInt

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.models import Alias as AliasModel, Category

from .base import BaseAliasPluginTestCase


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

    def test_pages_using_this_alias(self):
        site1 = Site.objects.create(domain='site1.com', name='1')
        site2 = Site.objects.create(domain='site2.com', name='2')
        alias = self._create_alias(name='root alias')
        nested_alias = self._create_alias(name='nested alias')
        deep_nested_alias = self._create_alias(name='deep nested alias')
        add_plugin(
            alias.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=nested_alias,
        )
        add_plugin(
            nested_alias.get_placeholder(self.language),
            'Alias',
            language=self.language,
            alias=deep_nested_alias,
        )

        site1_page = create_page(
            title='Site1',
            template='page.html',
            language=self.language,
            published=True,
            in_navigation=True,
            site=site1,
        )
        self.add_alias_plugin_to_page(site1_page, alias)
        site1_page.publish(self.language)  # Should show on the list (draft, public)

        nested_page1 = create_page(
            title='Site1 nested page 1',
            template='page.html',
            language=self.language,
            published=True,
            in_navigation=True,
            site=site1,
            parent=site1_page,
        )
        self.add_alias_plugin_to_page(nested_page1, alias)
        self.add_alias_plugin_to_page(nested_page1, alias)
        nested_page1.publish(self.language)  # Should show on the list only once (draft, public)

        nested_page2 = create_page(
            title='Site1 nested page 2',
            template='page.html',
            language=self.language,
            published=True,
            in_navigation=True,
            site=site1,
            parent=site1_page,
        )
        self.add_alias_plugin_to_page(nested_page2, alias)
        # Not published change but will be shown on the list. (draft)

        nested_page3 = create_page(
            title='Site1 nested page 3',
            template='page.html',
            language=self.language,
            published=True,
            in_navigation=True,
            site=site1,
            parent=site1_page,
        )  # Not show on the list

        deep_nested_page4 = create_page(
            title='Site1 deep nested page 4',
            template='page.html',
            language=self.language,
            published=True,
            in_navigation=True,
            site=site1,
            parent=nested_page3,
        )
        self.add_alias_plugin_to_page(deep_nested_page4, alias)
        deep_nested_page4.publish(self.language)  # Should show on the list (draft, public)

        site2_page = create_page(
            title='Site2',
            template='page.html',
            language='de',
            published=True,
            in_navigation=True,
            site=site2,
        )
        self.add_alias_plugin_to_page(site2_page, alias, 'de')
        site2_page.publish('de')  # Should show on the list (draft, public)

        result_list = [
            site1_page.pk,
            site1_page.publisher_public.pk,
            nested_page1.pk,
            nested_page1.publisher_public.pk,
            nested_page2.pk,
            deep_nested_page4.pk,
            deep_nested_page4.publisher_public.pk,
            site2_page.pk,
            site2_page.publisher_public.pk,
        ]

        with self.assertNumQueries(FuzzyInt(0, 3)):
            alias_pages = alias.pages_using_this_alias

        self.assertEqual(
            [page.pk for page in sorted(alias_pages, key=lambda obj: obj.pk)],
            result_list,
        )

        # with self.assertNumQueries(FuzzyInt(0, 3)):
        #     nested_alias_pages = nested_alias.pages_using_this_alias
        # self.assertEqual(nested_alias_pages, result_list)

        with self.assertNumQueries(FuzzyInt(0, 3)):
            deep_nested_alias_pages = deep_nested_alias.pages_using_this_alias
        self.assertEqual(deep_nested_alias_pages, result_list)
