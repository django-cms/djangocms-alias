from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from cms.api import add_plugin

from djangocms_alias.models import Alias

from .base import BaseAliasPluginTestCase


class AliasPermissionsTestCase(BaseAliasPluginTestCase):

    def test_can_create_alias_superuser(self):
        self.assertTrue(
            self.alias_plugin_base.can_create_alias(
                self.get_superuser(),
                [self.plugin],
            ),
        )

    def test_can_create_alias_standard_user(self):
        self.assertFalse(
            self.alias_plugin_base.can_create_alias(
                self.get_standard_user(),
                [self.plugin],
            ),
        )

    def test_can_create_alias_staff_no_permissions(self):
        self.assertFalse(
            self.alias_plugin_base.can_create_alias(
                self.get_staff_user_with_no_permissions(),
                [self.plugin],
            ),
        )

    def test_can_create_alias_staff_partial_permissions(self):
        user = self.get_staff_user_with_no_permissions()
        user.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(
                    Alias,
                ),
                codename='add_alias',
            )
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(
                    self.alias_plugin_base.model,
                ),
                codename='add_aliasplugin',
            )
        )
        alias = self._create_alias(self.placeholder.get_plugins())
        add_plugin(
            self.placeholder,
            self.alias_plugin_base.__class__,
            language=self.language,
            alias=alias,
        )
        self.assertFalse(
            self.alias_plugin_base.can_create_alias(
                user,
                self.placeholder.get_plugins(),
            ),
        )

    def test_can_create_alias_staff_enough_permissions(self):
        user = self.get_staff_user_with_std_permissions()
        user.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(
                    Alias,
                ),
                codename='add_alias',
            )
        )
        self.assertTrue(
            self.alias_plugin_base.can_create_alias(
                user,
                self.placeholder.get_plugins(),
            ),
        )

    def test_can_detach_no_permission(self):
        user = self.get_staff_user_with_no_permissions()
        alias = self._create_alias(self.placeholder.get_plugins())
        self.assertFalse(
            self.alias_plugin_base.can_detach(
                user,
                alias.draft_content.get_plugins(),
            ),
        )

    def test_can_detach_has_permission(self):
        user = self.get_staff_user_with_std_permissions()
        alias = self._create_alias(self.placeholder.get_plugins())
        self.assertTrue(
            self.alias_plugin_base.can_detach(
                user,
                alias.draft_content.get_plugins(),
            ),
        )
