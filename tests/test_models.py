from cms.api import add_plugin

from .base import BaseAlias2PluginTestCase


class Alias2PluginMenuTestCase(BaseAlias2PluginTestCase):

    def test_alias_placeholder_slot_save_again(self):
        alias = self._create_alias(self.placeholder.get_plugins())
        slot_name = alias.placeholder.slot
        alias.save()
        self.assertEqual(alias.placeholder.slot, slot_name)

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
            language='en',
            alias=alias,
        )
        self.assertFalse(alias_plugin.is_recursive())

    def test_alias_is_recursive(self):
        alias = self._create_alias(
            self.placeholder.get_plugins(),
        )
        recursed_alias_plugin = add_plugin(
            alias.placeholder,
            self.alias_plugin_base.__class__,
            language='en',
            alias=alias,
        )
        self.assertTrue(recursed_alias_plugin.is_recursive())
