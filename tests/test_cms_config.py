from importlib import reload

from django.conf import settings
from django.test import TestCase, override_settings

from djangocms_alias import cms_config


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
