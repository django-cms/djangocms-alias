from unittest import skipUnless

from django.contrib import admin
from django.contrib.sites.models import Site

from cms.utils import get_current_site

from djangocms_alias.constants import (
    SITE_FILTER_NO_SITE_VALUE,
    SITE_FILTER_URL_PARAM,
    UNPUBLISHED_FILTER_URL_PARAM,
)
from djangocms_alias.filters import CategoryFilter
from djangocms_alias.models import Alias as AliasModel, AliasContent, Category
from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class LanguageFiltersTestCase(BaseAliasPluginTestCase):

    def test_language_filter(self):
        """
        When rendering aliascontent manager language filter changing the language
        should filter the results.
        """
        category = Category.objects.create(name='Language Filter Category')
        alias = AliasModel.objects.create(
            category=category,
            position=0,
        )
        expected_en_content = AliasContent.objects.create(
            alias=alias,
            name="EN Alias Content",
            language="en",
        )
        expected_de_content = AliasContent.objects.create(
            alias=alias,
            name="DE Alias Content",
            language="de",
        )
        # If versioning is enabled be sure to create a version
        if is_versioning_enabled():
            from djangocms_versioning.models import Version

            Version.objects.create(content=expected_en_content, created_by=self.superuser)
            Version.objects.create(content=expected_de_content, created_by=self.superuser)

        base_url = self.get_admin_url(AliasContent, "changelist")

        with self.login_user_context(self.superuser):
            # en is the default language configured for the site
            response_default = self.client.get(base_url)
            # en should have a result
            response_en = self.client.get(base_url + "?language=en")
            # de should have a result
            response_de = self.client.get(base_url + "?language=de")
            # fr should have no result and be empty because nothing was created
            response_fr = self.client.get(base_url + "?language=fr")

        self.assertEqual(
            set(response_default.context["cl"].queryset),
            set([expected_en_content])
        )
        self.assertEqual(
            set(response_en.context["cl"].queryset),
            set([expected_en_content])
        )
        self.assertEqual(
            set(response_de.context["cl"].queryset),
            set([expected_de_content])
        )
        self.assertEqual(
            set(response_fr.context["cl"].queryset),
            set([])
        )


class SiteFiltersTestCase(BaseAliasPluginTestCase):

    def test_site_filter(self):
        """
        When rendering aliascontent manager site filter changing the site
        should filter the results.
        """
        current_site = get_current_site()
        another_site = Site.objects.create(
            name="Other site",
            domain="othersite.here"
        )
        empty_site = Site.objects.create(
            name="Empty site",
            domain="emptysite.here"
        )
        category = Category.objects.create(name='Site Filter Category')
        current_site_alias = AliasModel.objects.create(
            category=category,
            site=current_site,
        )
        current_site_alias_content = AliasContent.objects.create(
            alias=current_site_alias,
            name="Current Site Alias Content",
            language="en",
        )
        another_site_alias = AliasModel.objects.create(
            category=category,
            site=another_site,
        )
        another_site_alias_content = AliasContent.objects.create(
            alias=another_site_alias,
            name="Another Site Alias Content",
            language="en",
        )
        no_site_alias = AliasModel.objects.create(
            category=category,
        )
        no_site_alias_content = AliasContent.objects.create(
            alias=no_site_alias,
            name="No Site Alias Content",
            language="en",
        )

        # If versioning is enabled be sure to create a version
        if is_versioning_enabled():
            from djangocms_versioning.models import Version

            Version.objects.create(content=current_site_alias_content, created_by=self.superuser)
            Version.objects.create(content=another_site_alias_content, created_by=self.superuser)
            Version.objects.create(content=no_site_alias_content, created_by=self.superuser)

        base_url = self.get_admin_url(AliasContent, "changelist")

        with self.login_user_context(self.superuser):
            # en is the default language configured for the site
            response_default = self.client.get(base_url)
            # filter by aliases with the current site
            response_current_site = self.client.get(f"{base_url}?{SITE_FILTER_URL_PARAM}={current_site.pk}")
            # filter by aliases with a different site set
            response_other_site = self.client.get(f"{base_url}?{SITE_FILTER_URL_PARAM}={another_site.pk}")
            # filter by aliases with an empty site set
            response_empty_site = self.client.get(f"{base_url}?{SITE_FILTER_URL_PARAM}={empty_site.pk}")
            # filter by aliases with no site set
            response_no_site = self.client.get(f"{base_url}?{SITE_FILTER_URL_PARAM}={SITE_FILTER_NO_SITE_VALUE}")

        # By default all alias are shown
        self.assertEqual(
            set(response_default.context["cl"].queryset),
            set([
                current_site_alias_content,
                another_site_alias_content,
                no_site_alias_content,
            ])
        )
        # Only alias attached to the current site are shown when filtered by the current site
        self.assertEqual(
            set(response_current_site.context["cl"].queryset),
            set([current_site_alias_content])
        )
        # Only alias attached to the current site are shown when filtered by another site
        self.assertEqual(
            set(response_other_site.context["cl"].queryset),
            set([another_site_alias_content])
        )
        # Only alias attached to the current site are shown when filtered by no site
        self.assertEqual(
            set(response_no_site.context["cl"].queryset),
            set([no_site_alias_content])
        )
        # No are shown when filtered by an empty site
        self.assertEqual(
            set(response_empty_site.context["cl"].queryset),
            set([])
        )


@skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
class UnpublishedFiltersTestCase(BaseAliasPluginTestCase):

    def test_unpublished_filter(self):
        """
        When rendering aliascontent manager unpublished filter changing the show/hide unblished version option
        should filter the results.
        """
        from djangocms_versioning.constants import UNPUBLISHED
        from djangocms_versioning.models import Version

        category = Category.objects.create(name='Alias Filter Category')
        alias = AliasModel.objects.create(
            category=category,
            position=0
        )
        unpublished_alias = AliasModel.objects.create(
            category=category,
            position=0)
        expected_en_content = AliasContent.objects.create(
            alias=alias,
            name="EN Alias Content",
            language="en"
        )
        Version.objects.create(content=expected_en_content, created_by=self.superuser)
        expected_unpublished = AliasContent.objects.create(
            alias=unpublished_alias,
            name="EN Alias Content unpublished",
            language="en",
        )
        Version.objects.create(content=expected_unpublished, created_by=self.superuser, state=UNPUBLISHED)
        base_url = self.get_admin_url(AliasContent, "changelist")

        with self.login_user_context(self.get_superuser()):
            # en is the default language configured for the site
            response_default = self.client.get(base_url)
            # filter by unpublished hide
            qs_default = response_default.context["cl"].queryset
            response_unpublished = self.client.get(f"{base_url}?{UNPUBLISHED_FILTER_URL_PARAM}=1")
            qs_unpublished = response_unpublished.context["cl"].queryset
            # filter by unpublished show

        # show all alias contents  excluding unpublished versions
        self.assertEqual(set(qs_default), set([expected_en_content]))
        # show all aliase contents including unpublished versions
        self.assertEqual(set(qs_unpublished), set([expected_unpublished]))


class CatergoryFiltersTestCase(BaseAliasPluginTestCase):

    @skipUnless(not is_versioning_enabled(), 'Test only relevant when no versioning')
    def test_category_filter_no_verisoning(self):
        """
        When rendering aliascontent manager category filter, changing the category
        should filter the results.
        """
        category_one = Category.objects.create(name='one')
        alias_one = AliasModel.objects.create(
            category=category_one,
            position=0,
        )
        expected_category_one_content = AliasContent.objects.create(
            alias=alias_one,
            name="EN Alias Content one",
            language="en",
        )
        category_two = Category.objects.create(name='two')
        alias_two = AliasModel.objects.create(
            category=category_two,
            position=1,
        )
        expected_category_two_content = AliasContent.objects.create(
            alias=alias_two,
            name="EN Alias Content two",
            language="en",
        )
        base_url = self.get_admin_url(AliasContent, "changelist")

        with self.login_user_context(self.superuser):
            response_default = self.client.get(base_url)
            # category one should have a result
            category_one_filter_response = self.client.get(f"{base_url}?category={category_one.id}")
            # category two should have a result
            category_two_filter_response = self.client.get(f"{base_url}?category={category_two.id}")

        # By default all alias contents are shown
        self.assertEqual(
            set(response_default.context["cl"].queryset),
            set([
                expected_category_one_content,
                expected_category_two_content,
            ])
        )
        # show alias contents filter by category one
        self.assertEqual(
            set(category_one_filter_response.context["cl"].queryset),
            set([expected_category_one_content])
        )
        # show alias contents filter by category two
        self.assertEqual(
            set(category_two_filter_response.context["cl"].queryset),
            set([expected_category_two_content])
        )

    @skipUnless(is_versioning_enabled(), 'Test only relevant when versioning enabled')
    def test_category_filter_with_verisoning(self):
        """
        When rendering aliascontent manager category filter, changing the category
        should filter the results.
        """
        from djangocms_versioning.models import Version

        category_one = Category.objects.create(name='one')
        alias_one = AliasModel.objects.create(
            category=category_one,
            position=0,
        )
        expected_category_one_content = AliasContent.objects.create(
            alias=alias_one,
            name="EN Alias Content one",
            language="en",
        )
        Version.objects.create(content=expected_category_one_content, created_by=self.superuser)
        category_two = Category.objects.create(name='two')
        alias_two = AliasModel.objects.create(
            category=category_two,
            position=1,
        )
        expected_category_two_content = AliasContent.objects.create(
            alias=alias_two,
            name="EN Alias Content two",
            language="en",
        )
        Version.objects.create(content=expected_category_two_content, created_by=self.superuser)
        base_url = self.get_admin_url(AliasContent, "changelist")

        with self.login_user_context(self.superuser):
            response_default = self.client.get(base_url)
            # category one should have a result
            category_one_filter_response = self.client.get(f"{base_url}?category={category_one.id}")
            # categopry two should have a result
            category_two_filter_response = self.client.get(f"{base_url}?category={category_two.id}")

        # By default all alias contents are shown
        self.assertEqual(
            set(response_default.context["cl"].queryset),
            set([
                expected_category_one_content,
                expected_category_two_content,
            ])
        )
        # show alias contents filter by category one
        self.assertEqual(
            set(category_one_filter_response.context["cl"].queryset),
            set([expected_category_one_content])
        )
        # show alias contents filter by category two
        self.assertEqual(
            set(category_two_filter_response.context["cl"].queryset),
            set([expected_category_two_content])
        )

    def test_category_filter_lookups_ordered_alphabetical(self):
        """
        Category filter lookup choices should be ordered in alphabetical order
        """
        category_one = Category.objects.create(name='b - category')
        alias_one = AliasModel.objects.create(
            category=category_one,
            position=0,
        )
        AliasContent.objects.create(
            alias=alias_one,
            name="EN Alias Content one",
            language="en",
        )
        category_two = Category.objects.create(name='a - category')
        alias_two = AliasModel.objects.create(
            category=category_two,
            position=1,
        )
        AliasContent.objects.create(
            alias=alias_two,
            name="EN Alias Content two",
            language="en",
        )

        version_admin = admin.site._registry[AliasContent]
        category_filter = CategoryFilter(None, {"category": ""}, AliasContent, version_admin)
        # Get the first choice in the filter lookup object
        first_lookup_value = category_filter.lookup_choices[0][1]
        # Lookup value should match the category name linked to alias content
        self.assertEquals(
            first_lookup_value, category_two.name
        )
        self.assertNotEqual(
            first_lookup_value, category_one.name
        )

    def test_category_filter_lookup_should_only_show_aliases_linked_to_content(self):
        """
        Category not linked to content should not be listed in the category filter lookups
        """
        category_one = Category.objects.create(name='b - category')
        alias_one = AliasModel.objects.create(
            category=category_one,
            position=0,
        )
        AliasContent.objects.create(
            alias=alias_one,
            name="EN Alias Content one",
            language="en",
        )
        category_two = Category.objects.create(name='a - category')
        AliasModel.objects.create(
            category=category_two,
            position=1,
        )

        version_admin = admin.site._registry[AliasContent]
        category_filter = CategoryFilter(None, {"category": ""}, AliasContent, version_admin)

        # Get the first choice in the filter lookup object
        first_lookup_value = category_filter.lookup_choices[0][1]
        # Lookup choices should only display the category linked to content
        self.assertEqual(len(category_filter.lookup_choices), 1)
        # Lookup value should match the category name linked to alias content
        self.assertEqual(
            first_lookup_value, category_one.name
        )
        # Category not linked to alias content should not be listed in the choices
        self.assertNotEqual(
            first_lookup_value, category_two.name
        )
