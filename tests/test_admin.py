from unittest import skipUnless

from django.utils.formats import localize
from django.utils.timezone import localtime

from cms.test_utils.testcases import CMSTestCase

from freezegun import freeze_time

from djangocms_alias.models import Alias as AliasModel, AliasContent, Category
from djangocms_alias.utils import is_versioning_enabled


class FiltersTestCase(CMSTestCase):
    def setUp(self):
        self.superuser = self.get_superuser()

    def test_language_filter(self):
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
            qs_default = response_default.context["cl"].queryset
            # en should have a result
            response_en = self.client.get(base_url + "?language=en")
            qs_en = response_en.context["cl"].queryset
            # de should have a result
            response_de = self.client.get(base_url + "?language=de")
            qs_de = response_de.context["cl"].queryset
            # fr should have no result and be empty because nothing was created
            response_fr = self.client.get(base_url + "?language=fr")
            qs_fr = response_fr.context["cl"].queryset

        self.assertEqual(set(qs_default), set([expected_en_content]))
        self.assertEqual(set(qs_en), set([expected_en_content]))
        self.assertEqual(set(qs_de), set([expected_de_content]))
        self.assertEqual(set(qs_fr), set([]))


class AliasContentManagerTestCase(CMSTestCase):
    def setUp(self):
        self.superuser = self.get_superuser()

    @skipUnless(not is_versioning_enabled(), 'Test only relevant when no versioning')
    def test_alias_content_manager_rendering_without_versioning_actions(self):
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

        base_url = self.get_admin_url(AliasContent, "changelist")

        with self.login_user_context(self.superuser):
            # en is the default language configured for the site
            response = self.client.get(base_url)

        response_content_decoded = response.content.decode()

        # Check Column Headings
        self.assertInHTML(
            'Category',
            response_content_decoded,
        )

        # Check Alias content row values
        self.assertIn(
            category.name,
            response_content_decoded
        )
        self.assertIn(
            expected_en_content.name,
            response_content_decoded,
        )

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
    def test_alias_content_manager_rendering_with_versioning_actions(self):
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
        #create a version

        from djangocms_versioning.models import Version

        Version.objects.create(content=expected_en_content, created_by=self.superuser)

        with self.login_user_context(self.superuser):

            base_url = self.get_admin_url(AliasContent, "changelist")
            # en is the default language configured for the site
            response = self.client.get(base_url)

        response_content_decoded = response.content.decode()

        # Check Column Headings
        self.assertInHTML(
            'Category',
            response_content_decoded,
        )
        self.assertInHTML(
            'Author',
            response_content_decoded,
        )
        self.assertInHTML(
            'Modified',
            response_content_decoded,
        )
        self.assertInHTML(
            'State',
            response_content_decoded,
        )
        self.assertInHTML(
            'Actions',
            response_content_decoded,
        )

        # Check Alias content row values
        self.assertIn(
            category.name,
            response_content_decoded
        )
        self.assertIn(
            expected_en_content.name,
            response_content_decoded,
        )

        latest_alias_content_version = expected_en_content.versions.all()[0]

        self.assertInHTML(
            f'<td class="field-get_author">{latest_alias_content_version.created_by.username}</td>',  # noqa: E501
            response_content_decoded,
        )
        self.assertIn(
            latest_alias_content_version.get_state_display(),
            response_content_decoded,
        )

        self.assertIn(
            localize(localtime(latest_alias_content_version.modified)),
            response_content_decoded,
        )
