from cms.api import add_plugin

from djangocms_alias.constants import DRAFT_ALIASES_SESSION_KEY
from djangocms_alias.cms_plugins import Alias

from .base import BaseAliasPluginTestCase


class AliasDraftLiveTestCase(BaseAliasPluginTestCase):

    def test_uses_live_content_by_default(self):
        alias = self._create_alias()
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        alias.publish(self.language)
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        self.page.publish(self.language)
        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, 'test 1')
        self.assertContains(response, 'test 2')
        self.assertNotContains(response, 'test 3')

    def test_draft_aliases(self):
        alias = self._create_alias()
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 1',
        )
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 2',
        )
        alias.publish(self.language)
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        add_plugin(
            self.placeholder,
            Alias,
            language=self.language,
            alias=alias,
        )
        self.page.publish(self.language)
        with self.login_user_context(self.superuser):
            self.client.post(
                self.SET_ALIAS_DRAFT_ENDPOINT,
                data={'enable': 1},
            )
            response = self.client.get(
                self.page.get_absolute_url(),
            )
        self.assertContains(response, 'test 1')
        self.assertContains(response, 'test 2')
        self.assertContains(response, 'test 3')

    def test_set_draft_view_no_permission(self):
        response = self.client.post(
            self.SET_ALIAS_DRAFT_ENDPOINT,
        )
        self.assertEqual(response.status_code, 403)

    def test_set_draft_view_no_param(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.SET_ALIAS_DRAFT_ENDPOINT,
            )
            self.assertEqual(response.status_code, 400)

    def test_set_draft_view_enable(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.SET_ALIAS_DRAFT_ENDPOINT,
                data={'enable': 1},
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                self.client.session[DRAFT_ALIASES_SESSION_KEY],
            )

    def test_set_draft_view_disable(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.SET_ALIAS_DRAFT_ENDPOINT,
                data={'enable': 0},
            )
            self.assertEqual(response.status_code, 200)
            self.assertFalse(
                self.client.session.get(DRAFT_ALIASES_SESSION_KEY, False),
            )
