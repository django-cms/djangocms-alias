from unittest import skipUnless

from djangocms_alias.compat import CMS_36
from djangocms_alias.constants import DETAIL_ALIAS_URL_NAME
from djangocms_alias.utils import alias_plugin_reverse

from .base import BaseAliasPluginTestCase


class AliasPluginReverseTestCase(BaseAliasPluginTestCase):

    @skipUnless(CMS_36, 'Only for CMS < 3.7')
    def test_detail_reverse_url_to_add_structure_mode(self):
        alias = self._create_alias([self.plugin])
        url = alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk])
        self.assertIn('?structure', url)
