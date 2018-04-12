from djangocms_alias.utils import alias_plugin_reverse

from .base import BaseAliasPluginTestCase

from djangocms_alias.constants import DETAIL_ALIAS_URL_NAME


class AliasPluginReverseTestCase(BaseAliasPluginTestCase):

    def test_detail_reverse_url_to_add_structure_mode(self):
        alias = self._create_alias([self.plugin])
        url = alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk])
        self.assertIn('?structure', url)
