from cms.api import add_plugin

from djangocms_alias.models import Category

from .base import BaseAliasPluginTestCase


class AliasModelsTestCase(BaseAliasPluginTestCase):

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
            self.alias_plugin_base.__class__,
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
            self.alias_plugin_base.__class__,
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
        alias2cat1 = self._create_alias(name='2', category=category1)
        alias1cat2 = self._create_alias(name='1', category=category2)
        alias2cat2 = self._create_alias(name='2', category=category2)
        alias3cat1 = self._create_alias(name='3', category=category1)
        alias4cat1 = self._create_alias(name='4', category=category1)
        alias1cat1.refresh_from_db()
        alias2cat1.refresh_from_db()
        alias3cat1.refresh_from_db()
        alias4cat1.refresh_from_db()
        alias1cat2.refresh_from_db()
        alias2cat2.refresh_from_db()
        self.assertEqual(alias1cat1.position, 0)
        self.assertEqual(alias2cat1.position, 1)
        self.assertEqual(alias3cat1.position, 2)
        self.assertEqual(alias4cat1.position, 3)
        self.assertEqual(alias1cat2.position, 0)
        self.assertEqual(alias2cat2.position, 1)

    def test_save_and_delete_inc_dec_of_position(self):
        alias1 = self._create_alias(name='1')
        alias2 = self._create_alias(name='2')
        alias3 = self._create_alias(name='3')
        alias4 = self._create_alias(name='4')

        alias1.delete()
        alias2.refresh_from_db()
        alias3.refresh_from_db()
        alias4.refresh_from_db()
        self.assertEqual(alias2.position, 0)
        self.assertEqual(alias3.position, 1)
        self.assertEqual(alias4.position, 2)

        alias5 = self._create_alias(name='5')
        self.assertEqual(alias2.position, 0)
        self.assertEqual(alias3.position, 1)
        self.assertEqual(alias4.position, 2)
        self.assertEqual(alias5.position, 3)

        alias3.delete()
        alias2.refresh_from_db()
        alias4.refresh_from_db()
        alias5.refresh_from_db()
        self.assertEqual(alias2.position, 0)
        self.assertEqual(alias4.position, 1)
        self.assertEqual(alias5.position, 2)

        alias5.delete()
        alias2.refresh_from_db()
        alias4.refresh_from_db()
        self.assertEqual(alias2.position, 0)
        self.assertEqual(alias4.position, 1)

    def test_change_position_dont_change_position_in_other_categories(self):
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

        alias1cat1.change_position(alias2cat1.position)
        alias1cat1.refresh_from_db()
        alias2cat1.refresh_from_db()
        alias1cat2.refresh_from_db()
        alias2cat2.refresh_from_db()

        self.assertEqual(alias1cat1.position, 1)
        self.assertEqual(alias2cat1.position, 0)

        self.assertEqual(alias1cat2.position, 0)
        self.assertEqual(alias2cat2.position, 1)

    def test_change_position_moving_up(self):
        alias1 = self._create_alias(name='1')  # 0
        alias2 = self._create_alias(name='2')  # 1
        alias3 = self._create_alias(name='3')  # 2
        alias4 = self._create_alias(name='4')  # 3
        alias5 = self._create_alias(name='5')  # 4

        alias4.change_position(1)
        alias1.refresh_from_db()
        alias2.refresh_from_db()
        alias3.refresh_from_db()
        alias4.refresh_from_db()
        alias5.refresh_from_db()

        self.assertEqual(alias1.position, 0)
        self.assertEqual(alias4.position, 1)
        self.assertEqual(alias2.position, 2)
        self.assertEqual(alias3.position, 3)
        self.assertEqual(alias5.position, 4)

    def test_change_position_moving_up_from_end_to_start(self):
        alias1 = self._create_alias(name='1')  # 0
        alias2 = self._create_alias(name='2')  # 1
        alias3 = self._create_alias(name='3')  # 2
        alias4 = self._create_alias(name='4')  # 3
        alias5 = self._create_alias(name='5')  # 4

        alias5.change_position(0)
        alias1.refresh_from_db()
        alias2.refresh_from_db()
        alias3.refresh_from_db()
        alias4.refresh_from_db()
        alias5.refresh_from_db()

        self.assertEqual(alias5.position, 0)
        self.assertEqual(alias1.position, 1)
        self.assertEqual(alias2.position, 2)
        self.assertEqual(alias3.position, 3)
        self.assertEqual(alias4.position, 4)

    def test_change_position_moving_down(self):
        alias1 = self._create_alias(name='1')  # 0
        alias2 = self._create_alias(name='2')  # 1
        alias3 = self._create_alias(name='3')  # 2
        alias4 = self._create_alias(name='4')  # 3
        alias5 = self._create_alias(name='5')  # 4

        alias2.change_position(3)
        alias1.refresh_from_db()
        alias2.refresh_from_db()
        alias3.refresh_from_db()
        alias4.refresh_from_db()
        alias5.refresh_from_db()

        self.assertEqual(alias1.position, 0)
        self.assertEqual(alias3.position, 1)
        self.assertEqual(alias4.position, 2)
        self.assertEqual(alias2.position, 3)
        self.assertEqual(alias5.position, 4)

    def test_change_position_moving_down_from_start_to_end(self):
        alias1 = self._create_alias(name='1')  # 0
        alias2 = self._create_alias(name='2')  # 1
        alias3 = self._create_alias(name='3')  # 2
        alias4 = self._create_alias(name='4')  # 3
        alias5 = self._create_alias(name='5')  # 4

        alias1.change_position(4)
        alias1.refresh_from_db()
        alias2.refresh_from_db()
        alias3.refresh_from_db()
        alias4.refresh_from_db()
        alias5.refresh_from_db()

        self.assertEqual(alias2.position, 0)
        self.assertEqual(alias3.position, 1)
        self.assertEqual(alias4.position, 2)
        self.assertEqual(alias5.position, 3)
        self.assertEqual(alias1.position, 4)
