from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class AliasMenuTestCase(BaseAliasPluginTestCase):

    def test_pages_keep_their_menu_nodes(self):
        """Tests that AliasDisableMenu modifier does not affect
        non-alias pages"""

        response = self.client.get(self.page.get_absolute_url())

        self.assertInHTML(
            '<ul class="nav"><li class="child selected"><a href="/en/test/">test</a></li></ul>',  # noqa: E501
            response.content.decode(),
        )
