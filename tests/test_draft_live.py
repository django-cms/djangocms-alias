from cms.api import add_plugin

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
        self.alias_plugin_base.publish_alias(alias, self.language)
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        add_plugin(
            self.placeholder,
            self.alias_plugin_base.__class__,
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
        self.alias_plugin_base.publish_alias(alias, self.language)
        add_plugin(
            alias.draft_content,
            'TextPlugin',
            language=self.language,
            body='test 3',
        )
        add_plugin(
            self.placeholder,
            self.alias_plugin_base.__class__,
            language=self.language,
            alias=alias,
        )
        self.page.publish(self.language)
        self.client.post(self.SET_ALIAS_DRAFT_ENDPOINT, data={'enable': True})
        response = self.client.get(
            self.page.get_absolute_url(),
        )
        self.assertContains(response, 'test 1')
        self.assertContains(response, 'test 2')
        self.assertContains(response, 'test 3')
