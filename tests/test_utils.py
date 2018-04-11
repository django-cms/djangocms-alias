from djangocms_alias.utils import alias_plugin_reverse

from .base import BaseAlias2PluginTestCase

from djangocms_alias.constants import DETAIL_ALIAS_URL_NAME


class AliasPluginReverseTestCase(BaseAlias2PluginTestCase):

    def test_detail_reverse_url_to_add_structure_mode(self):
        alias = self._create_alias([self.plugin])
        url = alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk])
        self.assertIn('?structure', url)
