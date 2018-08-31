from cms.api import add_plugin

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
