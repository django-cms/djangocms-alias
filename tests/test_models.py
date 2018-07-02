from cms.api import add_plugin
from cms.models import Placeholder

from djangocms_alias.models import _get_alias_placeholder_slot

from djangocms_alias.cms_plugins import Alias
from djangocms_alias.models import Category

from .base import BaseAliasPluginTestCase


class AliasModelsTestCase(BaseAliasPluginTestCase):

    def _get_aliases_positions(self, category):
        return dict(category.aliases.values_list('position', 'pk'))

    def test_alias_placeholder_slot_save_again(self):
        alias = self._create_alias(self.placeholder.get_plugins())
        slot_name = alias.draft_content.slot
        alias.save()
        self.assertEqual(alias.draft_content.slot, slot_name)

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
            alias.draft_content,
            Alias,
            language=self.language,
            alias=alias,
        )
        self.assertTrue(recursed_alias_plugin.is_recursive())

    def test_increment_position_for_newly_created_instances(self):
        category1 = Category.objects.create(
            name='Cat 1',
        )
        category2 = Category.objects.create(
            name='Cat 2',
        )
        alias1cat1 = self._create_alias(name='1', category=category1)
        alias1cat2 = self._create_alias(name='1', category=category2)
        alias2cat2 = self._create_alias(name='2', category=category2)
        alias2cat1 = self._create_alias(name='2', category=category1)

        self.assertEqual(
            self._get_aliases_positions(alias1cat1.category),
            {0: alias1cat1.pk, 1: alias2cat1.pk},
        )
        self.assertEqual(
            self._get_aliases_positions(alias1cat2.category),
            {0: alias1cat2.pk, 1: alias2cat2.pk},
        )

    def test_save_and_delete_inc_dec_of_position_delete_first(self):
        alias1 = self._create_alias(name='1')
        alias2 = self._create_alias(name='2')
        alias3 = self._create_alias(name='3')
        alias4 = self._create_alias(name='4')

        alias1.delete()
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias2.pk, 1: alias3.pk, 2: alias4.pk},
        )

    def test_save_and_delete_inc_dec_of_position_delete_in_the_middle(self):
        alias1 = self._create_alias(name='1')
        alias2 = self._create_alias(name='2')
        alias3 = self._create_alias(name='3')

        alias2.delete()
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias1.pk, 1: alias3.pk},
        )

    def test_save_and_delete_inc_dec_of_position_delete_last(self):
        alias1 = self._create_alias(name='1')
        alias2 = self._create_alias(name='2')
        alias3 = self._create_alias(name='3')

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
        alias1cat1 = self._create_alias(name='1', category=category1)  # 0
        alias2cat1 = self._create_alias(name='2', category=category1)  # 1
        alias1cat2 = self._create_alias(name='1', category=category2)  # 0
        alias2cat2 = self._create_alias(name='2', category=category2)  # 1

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
        alias1 = self._create_alias(name='1')  # 0
        alias2 = self._create_alias(name='2')  # 1
        alias3 = self._create_alias(name='3')  # 2
        alias4 = self._create_alias(name='4')  # 3

        alias3._set_position(1)
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias1.pk, 1: alias3.pk, 2: alias2.pk, 3: alias4.pk},
        )

    def test_set_position_moving_down(self):
        alias1 = self._create_alias(name='1')  # 0
        alias2 = self._create_alias(name='2')  # 1
        alias3 = self._create_alias(name='3')  # 2
        alias4 = self._create_alias(name='4')  # 3

        alias2._set_position(2)
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias1.pk, 1: alias3.pk, 2: alias2.pk, 3: alias4.pk},
        )

    def test_set_position_moving_up_from_end_to_start(self):
        alias1 = self._create_alias(name='1')  # 0
        alias2 = self._create_alias(name='2')  # 1
        alias3 = self._create_alias(name='3')  # 2
        alias4 = self._create_alias(name='4')  # 3

        alias4._set_position(0)
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias4.pk, 1: alias1.pk, 2: alias2.pk, 3: alias3.pk},
        )

    def test_set_position_moving_down_from_start_to_end(self):
        alias1 = self._create_alias(name='1')  # 0
        alias2 = self._create_alias(name='2')  # 1
        alias3 = self._create_alias(name='3')  # 2
        alias4 = self._create_alias(name='4')  # 3

        alias1._set_position(3)
        self.assertEqual(
            self._get_aliases_positions(alias1.category),
            {0: alias2.pk, 1: alias3.pk, 2: alias4.pk, 3: alias1.pk},
        )

    def test_delete(self):
        alias = self._create_alias([self.plugin])
        add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        alias.delete()
        self.assertFalse(alias.__class__.objects.filter(pk=alias.pk).exists())
        self.assertEqual(alias.cms_plugins.count(), 0)
        self.assertEqual(
            Placeholder.objects.filter(
                slot=_get_alias_placeholder_slot(alias),
            ).count(),
            0,
        )
