import re
from unittest import skip, skipIf, skipUnless

from cms.api import add_plugin
from cms.models import Placeholder
from cms.toolbar.utils import get_object_edit_url, get_object_preview_url
from cms.utils import get_current_site
from cms.utils.i18n import force_language
from cms.utils.plugins import downcast_plugins
from cms.utils.urlutils import add_url_parameters, admin_reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.test.utils import override_settings

from djangocms_alias.constants import (
    CATEGORY_SELECT2_URL_NAME,
    DELETE_ALIAS_URL_NAME,
    LIST_ALIAS_URL_NAME,
    SELECT2_ALIAS_URL_NAME,
    USAGE_ALIAS_URL_NAME,
)
from djangocms_alias.models import Alias, AliasContent, Category
from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class AliasViewsTestCase(BaseAliasPluginTestCase):
    def test_create_alias_view_get_no_data(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.get_create_alias_endpoint())
            self.assertEqual(response.status_code, 400)

    def test_create_alias_view_non_staff_denied_access(self):
        response = self.client.get(self.get_create_alias_endpoint())
        self.assertEqual(response.status_code, 403)

    def test_create_alias_view_get_show_form_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context["form"].initial["plugin"].pk,
                self.plugin.pk,
            )

    def test_create_alias_view_get_show_form_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_create_alias_endpoint(),
                data={
                    "placeholder": self.placeholder.pk,
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context["form"].initial["placeholder"],
                self.placeholder,
            )

    def test_create_alias_view_show_form_replace_hidden(self):
        user = self.get_staff_user_with_std_permissions()
        user.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(
                    Alias,
                ),
                codename="add_alias",
            )
        )
        with self.login_user_context(user):
            response = self.client.get(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                response.context["form"].fields["replace"].widget.is_hidden,
            )

    def test_create_alias_view_post_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "language": self.language,
                    "name": "test alias",
                },
            )
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            self._publish(alias)
        alias_plugins = alias.get_placeholder(self.language).get_plugins()

        # Source plugin is kept in original placeholder
        self.assertIn(
            self.plugin,
            downcast_plugins(self.placeholder.get_plugins()),
        )

        self.assertEqual(alias_plugins.count(), 1)
        self.assertEqual(alias_plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            alias_plugins[0].get_bound_plugin().body,
            self.plugin.body,
        )

    def test_create_alias_view_post_plugin_replace(self):
        placeholder = self.placeholder
        if is_versioning_enabled():
            # Can only edit page/content that is in DRAFT
            placeholder = self._get_draft_page_placeholder()

        plugin = add_plugin(
            placeholder,
            "TextPlugin",
            language="en",
            body="test 222",
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": plugin.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                    "replace": True,
                },
            )

        self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            self._publish(alias)
        plugins = alias.get_placeholder(self.language).get_plugins()

        self.assertEqual(plugins.count(), 1)
        self.assertEqual(plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            plugins[0].get_bound_plugin().body,
            plugin.body,
        )

    def test_create_alias_view_name(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            self._publish(alias)
        self.assertEqual(alias.name, "test alias")

    def test_create_alias_view_post_no_plugin_or_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context["form"].is_valid())

    def test_create_alias_view_post_both_plugin_and_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "placeholder": self.placeholder.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context["form"].is_valid())

    def test_create_alias_view_post_empty_placeholder(self):
        placeholder = Placeholder(slot="empty")
        placeholder.save()

        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "placeholder": placeholder.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.content.decode(),
                "Plugins are required to create an alias",
            )

    def test_create_alias_view_post_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "placeholder": self.placeholder.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)

        # Source plugins are kept in original placeholder
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        plugin_in_placeholder = plugins[0].get_bound_plugin()
        self.assertEqual(self.plugin, plugin_in_placeholder)

        alias = Alias.objects.first()
        if is_versioning_enabled():
            self._publish(alias)

        source_plugins = self.placeholder.get_plugins()
        alias_plugins = alias.get_placeholder(self.language).get_plugins()

        self.assertEqual(alias_plugins.count(), source_plugins.count())
        for source, target in zip(source_plugins, alias_plugins):
            self.assertEqual(source.plugin_type, target.plugin_type)
            self.assertEqual(
                source.get_bound_plugin().body,
                target.get_bound_plugin().body,
            )

    def test_create_alias_view_post_placeholder_replace(self):
        placeholder = self.placeholder
        if is_versioning_enabled():
            # Can only edit page/content that is in DRAFT
            placeholder = self._get_draft_page_placeholder()

        placeholder.get_plugins().delete()
        text_plugin = add_plugin(
            placeholder,
            "TextPlugin",
            language="en",
            body="test 2",
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "placeholder": placeholder.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                    "replace": True,
                },
            )
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            self._publish(alias)
        alias_plugins = alias.get_placeholder(self.language).get_plugins()

        self.assertEqual(alias_plugins.count(), 1)
        self.assertEqual(alias_plugins[0].plugin_type, self.plugin.plugin_type)
        self.assertEqual(
            alias_plugins[0].get_bound_plugin().body,
            text_plugin.body,
        )

        placeholder_plugins = placeholder.get_plugins()
        self.assertEqual(placeholder_plugins.count(), 1)

        self.assertEqual(
            placeholder_plugins[0].get_bound_plugin().alias,
            alias,
        )

    def test_create_alias_view_post_no_create_permission(self):
        with self.login_user_context(self.get_staff_user_with_no_permissions()):  # noqa: E501
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 403)

    def test_create_alias_view_post_no_replace_permission(self):
        user = self.get_staff_user_with_std_permissions()
        user.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(
                    Alias,
                ),
                codename="add_alias",
            )
        )
        with self.login_user_context(user):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                    "replace": True,
                },
            )
            self.assertEqual(response.status_code, 403)

    def test_detach_view_no_permission_to_add_plugins_from_alias(self):
        response = self.client.post(
            self.get_detach_alias_plugin_endpoint(self.plugin.pk),
        )
        self.assertEqual(response.status_code, 403)

    def test_detach_view_get(self):
        alias = self._create_alias([self.plugin])
        plugin = add_plugin(
            self.placeholder,
            "Alias",
            language="en",
            alias=alias,
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_detach_alias_plugin_endpoint(plugin.pk),
            )
            self.assertEqual(response.status_code, 200)

    def test_detach_view_non_staff_denied_access(self):
        alias = self._create_alias([self.plugin])
        plugin = add_plugin(
            self.placeholder,
            "Alias",
            language="en",
            alias=alias,
        )
        user = self.get_staff_user_with_no_permissions()
        with self.login_user_context(user):
            response = self.client.post(
                self.get_detach_alias_plugin_endpoint(plugin.pk),
            )
        self.assertEqual(response.status_code, 403)

    def test_detach_view_non_alias_plugin(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_detach_alias_plugin_endpoint(self.plugin.pk),
            )
            self.assertEqual(response.status_code, 404)

    def test_detach_view(self):
        placeholder = self.placeholder
        if is_versioning_enabled():
            # Can only edit page/content that is in DRAFT
            placeholder = self._get_draft_page_placeholder()

        placeholder.get_plugins().delete()
        alias = self._create_alias()
        add_plugin(
            placeholder,
            "TextPlugin",
            language=self.language,
            body="test",
        )
        plugin = add_plugin(
            placeholder,
            "Alias",
            language="en",
            alias=alias,
        )
        add_plugin(
            alias.get_placeholder(self.language),
            "TextPlugin",
            language=self.language,
            body="test 2",
        )
        add_plugin(
            alias.get_placeholder(self.language),
            "TextPlugin",
            language=self.language,
            body="test 88",
        )
        plugins = placeholder.get_plugins()
        self.assertEqual(plugins.count(), 2)

        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_detach_alias_plugin_endpoint(plugin.pk),
            )
            self.assertEqual(response.status_code, 200)

        plugins = placeholder.get_plugins()
        self.assertEqual(plugins.count(), 3)
        self.assertEqual(plugins[0].get_bound_plugin().body, "test")
        self.assertEqual(plugins[1].get_bound_plugin().body, "test 2")
        self.assertEqual(plugins[2].get_bound_plugin().body, "test 88")

    def test_alias_content_preview_view(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_edit_url(alias.get_content()), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, alias.name)
        self.assertContains(response, self.plugin.body)

    def test_view_aliases_using_site_filter(self):
        site1 = Site.objects.create(domain="site1.com", name="1")
        site2 = Site.objects.create(domain="site2.com", name="2")
        site1_plugin = add_plugin(
            self.placeholder,
            "TextPlugin",
            language="en",
            body="This is text in English",
        )
        site2_plugin = add_plugin(
            self.placeholder,
            "TextPlugin",
            language="en",
            body="Das ist Text auf Deutsch",
        )
        site1_alias = self._create_alias(
            plugins=[site1_plugin],
            site=site1,
            name="site1_alias",
            category=self.category,
        )
        site2_alias = self._create_alias(
            plugins=[site2_plugin],
            site=site2,
            name="site2_alias",
            category=self.category,
        )
        alias_list_url = admin_reverse(LIST_ALIAS_URL_NAME)

        # when no filter used both objects are displayed
        with self.login_user_context(self.superuser):
            with force_language("en"):
                list_response = self.client.get(alias_list_url)

        self.assertContains(list_response, site1_alias.name)
        self.assertContains(list_response, site2_alias.name)

        # when no filtering by site 1 only first object displayed
        with self.login_user_context(self.superuser):
            with force_language("en"):
                site1_aliases_filter_url = f"{alias_list_url}?site={site1_alias.site.id}"
                list_response = self.client.get(site1_aliases_filter_url)

        self.assertContains(list_response, site1_alias.name)
        self.assertNotContains(list_response, site2_alias.name)

        # when no filtering by site 2 only first object displayed
        with self.login_user_context(self.superuser):
            with force_language("en"):
                site2_aliases_filter_url = f"{alias_list_url}?site={site2_alias.site.id}"
                list_response = self.client.get(site2_aliases_filter_url)

        self.assertNotContains(list_response, site1_alias.name)
        self.assertContains(list_response, site2_alias.name)

    @skipIf(is_versioning_enabled(), "Test only relevant without versioning enabled")
    def test_create_alias_name_unique_per_category_and_language(self):
        self._create_alias(
            name="test alias",
            category=self.category,
        )
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Alias with this Name and Category already exists.",
        )
        self.assertEqual(
            AliasContent.objects.filter(
                name="test alias",
                language=self.language,
                alias__category=self.category,
            ).count(),
            1,
        )

    def test_select2_view_no_permission(self):
        response = self.client.get(
            admin_reverse(
                SELECT2_ALIAS_URL_NAME,
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_select2_view(self):
        alias1 = self._create_alias(name="test 2")
        alias2 = self._create_alias(name="foo", position=1)
        alias3 = self._create_alias(name="foo4", position=1, published=False)

        if is_versioning_enabled():
            from djangocms_versioning.constants import DRAFT
            from djangocms_versioning.models import Version

            # This will show because it's a new draft version of the same alias
            draft_content = alias2.contents.create(name="foo", language=self.language)
            Version.objects.create(content=draft_content, created_by=self.superuser, state=DRAFT)

        # This shouldn't show because it hasn't content in current language
        self._create_alias(name="foo2", language="fr", position=1)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
            )

        result = [alias1.pk, alias2.pk, alias3.pk]
        text_result = ["test 2"]

        if is_versioning_enabled():
            # The following versions have draft content
            text_result.append("foo (Not published)")
            text_result.append("foo4 (Not published)")
        else:
            text_result.append("foo")
            text_result.append("foo4")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([a["id"] for a in response.json()["results"]], result)
        self.assertEqual(
            [a["text"] for a in response.json()["results"]],
            text_result,
        )

    def test_select2_view_order_by_category_and_position(self):
        category2 = Category.objects.create(name="foo")
        alias1 = self._create_alias(name="test 2")
        alias2 = self._create_alias(name="foo", position=1)
        alias3 = self._create_alias(name="bar", category=category2)
        alias4 = self._create_alias(name="baz", category=category2, position=1)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [alias3.pk, alias4.pk, alias1.pk, alias2.pk],
        )

    def test_select2_view_set_limit(self):
        self._create_alias(name="test 2")
        self._create_alias(name="foo", position=1)
        self._create_alias(name="three", position=2)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={"limit": 2},
            )

        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(content["more"])
        self.assertEqual(len(content["results"]), 2)

    def test_select2_view_text_repr(self):
        alias1 = self._create_alias(name="test 2")
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["results"][0]["text"],
            alias1.name,
        )

    def test_select2_view_term(self):
        alias1 = self._create_alias(name="test 2")
        self._create_alias(name="foo", position=1)
        alias3 = self._create_alias(name="three", position=2)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={"term": "t"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [alias1.pk, alias3.pk],
        )

    def test_select2_view_category(self):
        category2 = Category.objects.create(name="test 2")
        alias1 = self._create_alias(name="test 2", category=category2)
        alias2 = self._create_alias(name="foo", category=category2, position=1)
        # This shouldnt show because it's in different Category
        self._create_alias(name="three")
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={"category": category2.pk},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [alias1.pk, alias2.pk],
        )

    def test_select2_view_category_and_term(self):
        category2 = Category.objects.create(name="test 2")
        alias1 = self._create_alias(name="test 2", category=category2)
        self._create_alias(name="foo", category=category2, position=1)
        self._create_alias(name="three")
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={"category": category2.pk, "term": "t"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [alias1.pk],
        )

    def test_select2_view_site(self):
        """
        The list is filtered based on only matching
        alias with a specific site if it is provided
        """
        site = get_current_site()
        alias1 = self._create_alias(site=site)
        alias2 = self._create_alias(site=site, position=1)
        alias3 = self._create_alias(position=2)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={"site": site.pk},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [alias1.pk, alias2.pk, alias3.pk],
        )

    def test_select2_view_site_and_category(self):
        """
        The list is filtered based on only matching
        alias with a specific site and category if it is provided
        """
        category = Category.objects.create(name="category")
        site = get_current_site()
        self._create_alias(site=site)
        alias2 = self._create_alias(site=site, category=category, position=1)
        self._create_alias(position=2)
        self._create_alias(position=3)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={
                    "site": site.pk,
                    "category": category.pk,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [alias2.pk],
        )

    def test_select2_view_pk(self):
        alias1 = self._create_alias(name="test 2")
        self._create_alias(name="foo", position=1)
        self._create_alias(name="three")
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    SELECT2_ALIAS_URL_NAME,
                ),
                data={"pk": alias1.pk},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [alias1.pk],
        )

    @skip(
        "It is not currently possible to add an alias from the django admin changelist issue "
        "#https://github.com/django-cms/djangocms-alias/issues/97#97"
    )
    def test_aliascontent_add_view(self):
        alias = Alias.objects.create(category=self.category)
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse("djangocms_alias_aliascontent_add"),
                data={
                    "language": "de",
                    "name": "alias test de 1",
                    "alias": alias.pk,
                },
            )

        self.assertEqual(response.status_code, 302)
        if is_versioning_enabled():
            self._publish(alias, "de")
        self.assertEqual(alias.contents.count(), 1)
        alias_content = alias.contents.first()
        self.assertEqual(alias_content.language, "de")
        self.assertEqual(alias_content.name, "alias test de 1")

    @skip(
        "It is not currently possible to add an alias from the django admin changelist issue "
        "#https://github.com/django-cms/djangocms-alias/issues/97#97"
    )
    def test_aliascontent_add_view_get(self):
        alias = Alias.objects.create(category=self.category)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                add_url_parameters(
                    admin_reverse(
                        "djangocms_alias_aliascontent_add",
                    ),
                    language="fr",
                    alias=alias.pk,
                )
            )

        self.assertContains(response, 'type="hidden" name="language" value="fr"')
        self.assertContains(response, f'type="hidden" name="alias" value="{alias.pk}"')

    @skip(
        "It is not currently possible to add an alias from the django admin changelist issue "
        "#https://github.com/django-cms/djangocms-alias/issues/97#97"
    )
    def test_aliascontent_add_view_invalid_data(self):
        alias = Alias.objects.create(category=self.category)
        self._create_alias(
            name="test alias",
            category=self.category,
            language=self.language,
            published=True,
        )
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse("djangocms_alias_aliascontent_add"),
                data={
                    "language": self.language,
                    "name": "test alias",
                    "alias": alias.pk,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Alias with this Name and Category already exists",
        )

    @skip(
        "It is not currently possible to add an alias from the django admin changelist issue "
        "#https://github.com/django-cms/djangocms-alias/issues/97#97"
    )
    def test_aliascontent_add_view_valid_data(self):
        alias = Alias.objects.create(category=self.category)
        if is_versioning_enabled():
            self._create_alias(
                name="test alias",
                category=self.category,
                language=self.language,
                published=False,
            )
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse("djangocms_alias_aliascontent_add"),
                data={
                    "language": self.language,
                    "name": "test alias",
                    "alias": alias.pk,
                },
            )

        self.assertEqual(response.status_code, 302)
        if is_versioning_enabled():
            self._publish(alias)
        alias_content = alias.contents.first()
        self.assertEqual(alias_content.name, "test alias")

    def test_alias_usage_view(self):
        alias = self._create_alias()
        root_alias = self._create_alias()
        self.add_alias_plugin_to_page(self.page, alias)
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    USAGE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )

        self.assertContains(response, "<td>Page</td>")
        self.assertNotContains(response, "<td>Alias</td>")

        add_plugin(
            root_alias.get_placeholder(self.language),
            "Alias",
            language=self.language,
            alias=alias,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    USAGE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )

        self.assertContains(response, "<td>Page</td>")
        self.assertContains(response, "<td>Alias</td>")
        self.assertRegex(
            str(response.content),
            rf'href="{re.escape(self.page.get_absolute_url(self.language))}"[\w+]?>{str(self.page)}<\/a>',
        )
        self.assertRegex(
            str(response.content),
            rf'href="{re.escape(get_object_preview_url(root_alias.get_content()))}"[\w+]?>{str(alias)}<\/a>',
        )
        self.assertRegex(
            str(response.content),
            r'href="{}"[\w+]?>{}<\/a>'.format(
                re.escape(
                    add_url_parameters(
                        admin_reverse(
                            USAGE_ALIAS_URL_NAME,
                            args=[root_alias.pk],
                        ),
                        back=1,
                    )
                ),
                "View usage",
            ),
        )

    def test_delete_alias_view_get(self):
        alias = self._create_alias([self.plugin])
        add_plugin(
            self.placeholder,
            "Alias",
            language=self.language,
            alias=alias,
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertContains(
            response,
            f'Are you sure you want to delete the alias "{alias.name}"?',  # noqa: E501
        )

    def test_delete_alias_view_get_using_objects(self):
        alias = self._create_alias([self.plugin])
        add_plugin(
            self.placeholder,
            "Alias",
            language=self.language,
            alias=alias,
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertContains(response, "This alias is used by following objects:")
        test = r"<li>[\s\\n]*Page:[\s\\n]*<a href=\"\/en\/test\/\">test<\/a>[\s\\n]*<\/li>"
        self.assertRegex(str(response.content), test)

    def test_delete_alias_view_get_alias_not_used_on_any_page(self):
        alias = self._create_alias([self.plugin])
        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertContains(response, "This alias wasn't used by any object.")

    def test_delete_alias_view_post(self):
        """Tests the admin delete view (as opposed to the djangocms_alias.views.delete_view)"""
        alias = self._create_alias([self.plugin])
        self.assertIn(alias, Alias.objects.all())
        with self.login_user_context(self.superuser):
            response = self.client.post(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
                data={"post": "yes"},
            )
        self.assertEqual(response.status_code, 302)  # Successful delete returns a redirect
        self.assertFalse(Alias.objects.filter(pk=alias.pk).exists())  # Ensure it's gone

    def test_delete_alias_view_user_with_no_perms(self):
        alias = self._create_alias([self.plugin])
        staff_user = self.get_staff_user_with_no_permissions()
        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertEqual(response.status_code, 403)

        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.post(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
                data={"post": "yes"},
            )
        self.assertEqual(response.status_code, 403)

    def test_delete_alias_view_alias_not_being_used(self):
        alias = self._create_alias([self.plugin])
        staff_user = self.get_staff_user_with_alias_permissions()
        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertContains(response, "Are you sure you want to delete")
        self.assertContains(response, 'type="submit"')
        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.post(  # noqa
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
                data={"post": "yes"},
            )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Alias.objects.filter(pk=alias.pk).exists())

    def test_delete_alias_view_alias_being_used_on_pages(self):
        alias = self._create_alias([self.plugin])
        add_plugin(
            self.placeholder,
            "Alias",
            language=self.language,
            alias=alias,
        )
        # this user only can delete alias when alias not being used anywhere
        staff_user = self.get_staff_user_with_no_permissions()
        self.add_permission(staff_user, "delete_alias")

        with self.login_user_context(staff_user):  # noqa: E501
            response = self.client.get(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
            )
        self.assertEqual(response.status_code, 403)

        with self.login_user_context(staff_user):
            response = self.client.post(
                admin_reverse(
                    DELETE_ALIAS_URL_NAME,
                    args=[alias.pk],
                ),
                data={"post": "yes"},
            )
        self.assertEqual(response.status_code, 403)

    def test_custom_template_alias_view(self):
        alias = self._create_alias()
        add_plugin(
            alias.get_placeholder(self.language),
            "TextPlugin",
            language=self.language,
            body="custom alias content",
        )
        add_plugin(
            self.placeholder,
            "Alias",
            language=self.language,
            alias=alias,
            template="custom_alias_template",
        )

        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, "<b>custom alias content</b>")

    @override_settings(CMS_PLACEHOLDER_CACHE=False)
    def test_alias_multisite_support(self):
        site1 = Site.objects.create(domain="site1.com", name="1")
        site2 = Site.objects.create(domain="site2.com", name="2")
        alias = self._create_alias()
        alias_placeholder = alias.get_placeholder(self.language)
        add_plugin(
            alias_placeholder,
            "TextPlugin",
            language=self.language,
            body="test alias multisite",
        )

        site1_page = self._create_page(
            title="Site1",
            language=self.language,
            site=site1,
        )
        site2_page = self._create_page(
            title="Site2",
            language=self.language,
            site=site2,
        )
        self.add_alias_plugin_to_page(site1_page, alias)
        self.add_alias_plugin_to_page(site2_page, alias)

        with override_settings(SITE_ID=site1.pk):
            response = self.client.get(site1_page.get_absolute_url())
        self.assertContains(response, "test alias multisite")

        with override_settings(SITE_ID=site2.pk):
            response = self.client.get(site2_page.get_absolute_url())
        self.assertContains(response, "test alias multisite")

        add_plugin(
            alias_placeholder,
            "TextPlugin",
            language=self.language,
            body="Another alias plugin",
        )

        with override_settings(SITE_ID=site1.pk):
            response = self.client.get(site1_page.get_absolute_url())
        self.assertContains(response, "test alias multisite")
        self.assertContains(response, "Another alias plugin")

        with override_settings(SITE_ID=site2.pk):
            response = self.client.get(site2_page.get_absolute_url())
        self.assertContains(response, "test alias multisite")
        self.assertContains(response, "Another alias plugin")


class AliasCategorySelect2ViewTestCase(BaseAliasPluginTestCase):
    def test_select2_view_no_permission(self):
        """
        The category list view is private
        and only intended for use in the admin
        """
        response = self.client.get(
            admin_reverse(
                CATEGORY_SELECT2_URL_NAME,
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_select2_view_alias_not_set(self):
        """
        When categories exist but are not attached to an alias
        they are ignored
        """
        Category.objects.create(name="Category 1")
        category_2 = Category.objects.create(name="Category 2")
        Category.objects.create(name="Category 3")
        self._create_alias(category=category_2)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    CATEGORY_SELECT2_URL_NAME,
                ),
            )

        expected_result = [category_2.pk]

        self.assertEqual(response.status_code, 200)
        self.assertEqual([a["id"] for a in response.json()["results"]], expected_result)

    def test_select2_view_alias_site_set(self):
        """
        When a site is supplied only categories with site entries
        are returned
        """
        site = get_current_site()
        second_site = Site.objects.create(domain="other-site.org", name="other site")
        category_1 = Category.objects.create(name="Category 1")
        category_2 = Category.objects.create(name="Category 2")
        category_3 = Category.objects.create(name="Category 3")
        self._create_alias(category=category_1, site=site)
        self._create_alias(category=category_2, site=second_site)
        self._create_alias(category=category_3)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    CATEGORY_SELECT2_URL_NAME,
                ),
                data={"site": site.pk},
            )

        expected_result = [category_1.pk, category_3.pk]

        self.assertEqual(response.status_code, 200)
        self.assertEqual([a["id"] for a in response.json()["results"]], expected_result)

    def test_select2_view_set_limit(self):
        """
        Ensure that the page limit is respected
        """
        category_1 = Category.objects.create(name="Category 1")
        category_2 = Category.objects.create(name="Category 2")
        category_3 = Category.objects.create(name="Category 3")
        self._create_alias(category=category_1)
        self._create_alias(category=category_2, position=1)
        self._create_alias(category=category_3, position=2)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    CATEGORY_SELECT2_URL_NAME,
                ),
                data={"limit": 2},
            )

        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(content["more"])
        self.assertEqual(len(content["results"]), 2)

    def test_select2_view_text_repr(self):
        """
        Ensure that the display / text representation of the object
        is output to the user.
        """
        category = Category.objects.create(name="Category 1")
        self._create_alias(name="test 2", category=category)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    CATEGORY_SELECT2_URL_NAME,
                ),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["results"][0]["text"],
            category.name,
        )

    def test_select2_view_term(self):
        """
        Given a term, the response should return only
        categories that match the term.
        """
        category_1 = Category.objects.create(name="ategory 1")
        category_2 = Category.objects.create(name="Category 2")
        category_3 = Category.objects.create(name="tegory 3")
        category_4 = Category.objects.create(name="tegory 4")
        self._create_alias(category=category_1)
        self._create_alias(category=category_2)
        self._create_alias(category=category_3)
        self._create_alias(category=category_4)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    CATEGORY_SELECT2_URL_NAME,
                ),
                data={"term": "ate"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [category_2.pk, category_1.pk],
        )

    def test_select2_view_pk(self):
        """
        When a pk is provided that record should be returned
        """
        category_1 = Category.objects.create(name="Category 1")
        category_2 = Category.objects.create(name="Category 2")
        category_3 = Category.objects.create(name="Category 3")
        self._create_alias(category=category_1)
        self._create_alias(category=category_2)
        self._create_alias(category=category_3)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    CATEGORY_SELECT2_URL_NAME,
                ),
                data={"pk": category_2.pk},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [a["id"] for a in response.json()["results"]],
            [category_2.pk],
        )


class AliasViewsUsingVersioningTestCase(BaseAliasPluginTestCase):
    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_create_alias_view_name_draft_alias(self):
        with self.login_user_context(self.superuser):
            name = "test alias"
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "name": name,
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        # AliasContent not published
        self.assertEqual(alias.name, f"{name} (Not published)")

    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_create_alias_view_creating_version(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)

        alias = Alias.objects.last()
        if is_versioning_enabled():
            from djangocms_versioning.models import Version

            self.assertEqual(Version.objects.filter_by_grouper(alias).count(), 1)

    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_create_alias_name_without_uniqness(self):
        alias1 = self._create_alias(
            name="test alias",
            category=self.category,
            published=True,
        )
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Alias with this Name and Category already exists.",
        )

        self._unpublish(alias1)

        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "plugin": self.plugin.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "Alias with this Name and Category already exists.",
        )

        alias = Alias.objects.last()
        self._publish(alias)
        qs = AliasContent.objects.filter(
            name="test alias",
            language=self.language,
            alias__category=self.category,
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), alias.get_content(self.language))

    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_create_alias_view_post_placeholder_from_draft_page(self):
        page1 = self._create_page("test alias page")
        placeholder = page1.get_placeholders(self.language).get(
            slot="content",
        )
        plugin = add_plugin(
            placeholder,
            "TextPlugin",
            language=self.language,
            body="test alias",
        )
        self._unpublish(page1)
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "placeholder": placeholder.pk,
                    "category": self.category.pk,
                    "name": "test alias",
                    "language": self.language,
                },
            )
            self.assertEqual(response.status_code, 200)

        # Source plugins are kept in original placeholder
        plugins = placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        plugin_in_placeholder = plugins[0].get_bound_plugin()
        self.assertEqual(plugin, plugin_in_placeholder)

        alias = Alias.objects.first()
        self._publish(alias)

        source_plugins = placeholder.get_plugins()
        alias_plugins = alias.get_placeholder(self.language).get_plugins()

        self.assertEqual(alias_plugins.count(), source_plugins.count())
        for source, target in zip(source_plugins, alias_plugins):
            self.assertEqual(source.plugin_type, target.plugin_type)
            self.assertEqual(
                source.get_bound_plugin().body,
                target.get_bound_plugin().body,
            )

    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_create_alias_with_replace_plugin_with_versioning_checks(self):
        # 403 if you try to edit placeholder of published page
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_create_alias_endpoint(),
                data={
                    "placeholder": self.placeholder.pk,
                    "category": self.category.pk,
                    "name": "test alias 5",
                    "language": self.language,
                    "replace": True,
                },
            )
            self.assertEqual(response.status_code, 403)

    @skipUnless(is_versioning_enabled(), "Test only relevant for versioning")
    def test_detach_view_with_versioning_checks(self):
        # 403 when placeholder from non-draft page
        alias = self._create_alias()
        plugin = add_plugin(
            self.placeholder,
            "Alias",
            language="en",
            alias=alias,
        )
        with self.login_user_context(self.superuser):
            response = self.client.post(
                self.get_detach_alias_plugin_endpoint(plugin.pk),
            )
            self.assertEqual(response.status_code, 403)

    @skipUnless(is_versioning_enabled(), "Only valid in versioning scenario")
    def test_alias_not_shown_when_draft_when_visiting_page(self):
        """
        When visiting a published page with a draft alias the alias
        is not visible
        """
        unpublished_alias = self._create_alias(published=False)
        content = unpublished_alias.contents(manager="admin_manager").filter(language=self.language).first()
        alias_placeholder = content.placeholder

        body = "unpublished alias"
        add_plugin(alias_placeholder, "TextPlugin", language=self.language, body=body)

        page = self._create_page(
            title="New page",
            language=self.language,
        )

        self.add_alias_plugin_to_page(page, unpublished_alias)
        response = self.client.get(page.get_absolute_url())
        self.assertNotContains(response, body)

    def test_view_multilanguage(self):
        """
        Views should only display content related to the selected language
        """
        en_plugin = add_plugin(
            self.placeholder,
            "TextPlugin",
            language="en",
            body="This is text in English",
        )
        de_plugin = add_plugin(
            self.placeholder,
            "TextPlugin",
            language="de",
            body="Das ist Text auf Deutsch",
        )
        fr_plugin = add_plugin(
            self.placeholder,
            "TextPlugin",
            language="fr",
            body="C'est le texte en français",
        )
        alias = self._create_alias([en_plugin], name="English AliasContent object")
        alias_content_de = AliasContent.objects.create(
            alias=alias,
            name="German AliasContent object",
            language="de",
        )
        alias_content_de.populate(plugins=[de_plugin])
        alias_content_fr = AliasContent.objects.create(
            alias=alias,
            name="French AliasContent object",
            language="fr",
        )
        alias_content_fr.populate(plugins=[fr_plugin])

        # when versioning is enabled a Version must be created and published for each language
        if is_versioning_enabled():
            from djangocms_versioning.models import Version

            version_de = Version.objects.create(content=alias_content_de, created_by=self.superuser)
            version_de.publish(user=self.superuser)
            version_fr = Version.objects.create(content=alias_content_fr, created_by=self.superuser)
            version_fr.publish(user=self.superuser)

        with self.login_user_context(self.superuser):
            with force_language("en"):
                if is_versioning_enabled():
                    # we need to call get_object_preview_url on the AliasContent object when versioning is enabled,
                    # since edit is not available for a published content
                    detail_response = self.client.get(
                        get_object_preview_url(alias.get_content(language="en")), follow=True
                    )
                else:
                    detail_response = self.client.get(
                        get_object_edit_url(alias.get_content(language="en")), follow=True
                    )
                list_response = self.client.get(
                    admin_reverse(LIST_ALIAS_URL_NAME),
                )
        self.assertContains(detail_response, en_plugin.body)
        self.assertContains(list_response, alias.name)
        self.assertNotContains(detail_response, fr_plugin.body)
        self.assertNotContains(list_response, alias_content_fr.name)
        self.assertNotContains(detail_response, de_plugin.body)
        self.assertNotContains(list_response, alias_content_de.name)

        with self.login_user_context(self.superuser):
            with force_language("de"):
                if is_versioning_enabled():
                    # we need to call get_object_preview_url on the AliasContent object when versioning is enabled,
                    # since edit is not available for a published content
                    detail_response = self.client.get(get_object_preview_url(alias_content_de), follow=True)
                else:
                    detail_response = self.client.get(get_object_edit_url(alias.get_content()), follow=True)
                list_response = self.client.get(
                    admin_reverse(LIST_ALIAS_URL_NAME),
                )
        self.assertContains(detail_response, de_plugin.body)
        self.assertContains(list_response, alias_content_de.name)
        self.assertNotContains(detail_response, fr_plugin.body)
        self.assertNotContains(list_response, alias_content_fr.name)
        self.assertNotContains(detail_response, en_plugin.body)
        self.assertNotContains(list_response, alias.name)

        with self.login_user_context(self.superuser):
            with force_language("fr"):
                if is_versioning_enabled():
                    # we need to call get_object_preview_url on the AliasContent object when versioning is enabled,
                    # since edit is not available for a published content
                    detail_response = self.client.get(get_object_preview_url(alias_content_fr), follow=True)
                else:
                    detail_response = self.client.get(get_object_edit_url(alias.get_content()), follow=True)
                list_response = self.client.get(
                    admin_reverse(LIST_ALIAS_URL_NAME),  # noqa: E501
                )

        self.assertContains(detail_response, fr_plugin.body)
        self.assertContains(list_response, alias_content_fr.name)
        self.assertNotContains(detail_response, de_plugin.body)
        self.assertNotContains(list_response, alias_content_de.name)
        self.assertNotContains(detail_response, en_plugin.body)
        self.assertNotContains(list_response, alias.name)
