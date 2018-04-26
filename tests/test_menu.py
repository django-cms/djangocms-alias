from .base import BaseAliasPluginTestCase


class AliasMenuTestCase(BaseAliasPluginTestCase):

    def test_alias_pages_have_no_menu_nodes(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.CATEGORY_LIST_ENDPOINT)
        self.assertInHTML('<ul class="nav"></ul>', response.content.decode())
