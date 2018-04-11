from .base import BaseAlias2PluginTestCase


class AliasToolbarTestCase(BaseAlias2PluginTestCase):

    def test_add_aliases_link_to_admin_menu(self):
        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(self.page.get_absolute_url())

        self.assertNotContains(response, '<a href="{}"><span>Aliases'.format(
            self.LIST_ALIASES_ENDPOINT,
        ))

        page_structure_url = self.get_obj_structure_url(
            self.page.get_absolute_url(),
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(page_structure_url)

        self.assertContains(response, '<a href="{}"><span>Aliases'.format(
            self.LIST_ALIASES_ENDPOINT,
        ))
        # TODO: placement

    def test_add_alias_menu(self):
        # TODO create alias
        # TODO only in current app
        # TODO showing if has perms
        # TODO delete alias
        pass

    def test_create_alias(self):
        pass

    def test_delete_alias(self):
        pass
