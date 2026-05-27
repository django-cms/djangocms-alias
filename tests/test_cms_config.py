from importlib import reload
from unittest import skipIf, skipUnless

from django.apps import apps
from django.conf import settings
from django.test import TestCase, override_settings

from djangocms_alias import cms_config
from djangocms_alias.utils import get_versionable_item, is_versioning_enabled


class ReferenceConfigTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        reload(cms_config)
        super().tearDownClass()

    @override_settings(REFERENCES_ALIAS_MODELS_ENABLED=False)
    def test_references_setting_affects_cms_config_false(self):
        reload(cms_config)
        self.assertFalse(cms_config.AliasCMSConfig.djangocms_references_enabled)

    @override_settings(REFERENCES_ALIAS_MODELS_ENABLED=True)
    def test_references_setting_affects_cms_config_true(self):
        reload(cms_config)
        self.assertTrue(cms_config.AliasCMSConfig.djangocms_references_enabled)

    @override_settings()
    def test_references_setting_affects_cms_config_default(self):
        del settings.REFERENCES_ALIAS_MODELS_ENABLED
        reload(cms_config)
        self.assertTrue(cms_config.AliasCMSConfig.djangocms_references_enabled)


class GetVersionableItemTestCase(TestCase):
    def setUp(self):
        get_versionable_item.cache_clear()

    def tearDown(self):
        get_versionable_item.cache_clear()

    @skipUnless(is_versioning_enabled(), "Test only relevant when versioning is installed")
    def test_returns_versionable_item_when_versioning_installed(self):
        from djangocms_versioning.datastructures import VersionableItem

        alias_cms_config = apps.get_app_config("djangocms_alias").cms_config
        result = get_versionable_item(alias_cms_config)

        self.assertIsNotNone(result)
        self.assertTrue(issubclass(result, VersionableItem) or result is VersionableItem)

    @skipIf(is_versioning_enabled(), "Test only relevant when versioning is not installed")
    def test_returns_none_when_versioning_not_installed(self):
        alias_cms_config = apps.get_app_config("djangocms_alias").cms_config
        result = get_versionable_item(alias_cms_config)

        self.assertIsNone(result)
