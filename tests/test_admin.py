from unittest import skipUnless

from django.utils.formats import localize
from django.utils.timezone import localtime

from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import admin_reverse

from bs4 import BeautifulSoup as bs

from djangocms_alias.constants import USAGE_ALIAS_URL_NAME
from djangocms_alias.models import Alias as AliasModel, AliasContent, Category
from djangocms_alias.utils import is_versioning_enabled


class AliasContentManagerTestCase(CMSTestCase):
    def setUp(self):
        self.superuser = self.get_superuser()

    @skipUnless(not is_versioning_enabled(), 'Test only relevant when no versioning')
    def test_alias_content_manager_rendering_without_versioning_actions(self):
        """
        When rendering aliascontent manager without versioning
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
        self.assertNotIn(
            expected_en_content.get_absolute_url(),
            response_content_decoded,
        )

        usage_url = admin_reverse(USAGE_ALIAS_URL_NAME, args=[expected_en_content.alias.pk])
        change_category_and_site_url = admin_reverse(
            '{}_{}_change'.format(
                expected_en_content._meta.app_label,
                expected_en_content.alias._meta.model_name
            ), args=(expected_en_content.alias.pk,)
        )

        self.assertNotIn(
            usage_url,
            response_content_decoded,
        )
        self.assertNotIn(
            change_category_and_site_url,
            response_content_decoded,
        )
        # check for add content admin link
        add_alias_link = admin_reverse(
            '{}_{}_add'.format(
                expected_en_content._meta.app_label,
                expected_en_content._meta.model_name
            )
        )
        self.assertNotIn(
            # It is not currently possible to add an alias from the django admin changelist issue #97
            # https://github.com/django-cms/djangocms-alias/issues/97
            add_alias_link,
            response_content_decoded,
        )
        self.assertNotIn(
            '<option value="delete_selected">Delete selected alias contents</option>',  # noqa: E501
            response_content_decoded
        )

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
    def test_alias_content_manager_rendering_with_versioning_actions(self):
        """
        When rendering aliascontent manager with versioning actions
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

        usage_url = admin_reverse(USAGE_ALIAS_URL_NAME, args=[expected_en_content.alias.pk])
        change_category_and_site_url = admin_reverse(
            '{}_{}_change'.format(
                expected_en_content._meta.app_label,
                expected_en_content.alias._meta.model_name
            ), args=(expected_en_content.alias.pk,)
        )
        rename_alias_url = admin_reverse(
            '{}_{}_change'.format(
                expected_en_content._meta.app_label,
                expected_en_content._meta.model_name
            ), args=(expected_en_content.pk,)
        )

        self.assertIn(
            usage_url,
            response_content_decoded,
        )
        self.assertIn(
            rename_alias_url,
            response_content_decoded,
        )
        self.assertIn(
            change_category_and_site_url,
            response_content_decoded,
        )

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
    def test_alias_content_manager_rendering_preview_add_url(self):
        """
        When rendering aliascontent manager with versioning actions and preview
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

        from djangocms_versioning.models import Version

        Version.objects.create(content=expected_en_content, created_by=self.superuser)

        with self.login_user_context(self.superuser):
            base_url = self.get_admin_url(AliasContent, "changelist")
            # en is the default language configured for the site
            response = self.client.get(base_url)

        response_content_decoded = response.content.decode()

        self.assertIn(
            expected_en_content.get_absolute_url(),
            response_content_decoded,
        )
        self.assertNotIn(
            '<option value="delete_selected">Delete selected alias contents</option>',  # noqa: E501
            response_content_decoded
        )
        # check for add content admin link
        add_aliascontent_url = admin_reverse(
            '{}_{}_add'.format(
                expected_en_content._meta.app_label,
                expected_en_content._meta.model_name
            )
        )
        self.assertNotIn(
            add_aliascontent_url,
            response_content_decoded,
        )

    def _create_alias_and_categories(self, category_name, alias_content_name=None):
        if not alias_content_name:
            alias_content_name = category_name
        category = Category.objects.create(name=category_name)
        alias = AliasModel.objects.create(category=category, position=0)
        alias_content = AliasContent.objects.create(
            alias=alias,
            name=alias_content_name,
            language="en"
        )
        return category, alias, alias_content

    def test_category_field_ordering(self):
        """
        Category can be ordered by name, both in ascending and descending order
        """
        # Create a number of categories, aliases, and alias content to order
        first_category, first_alias, first_alias_content = self._create_alias_and_categories("First Order Test Case")
        # Previously lowercase and upper case would be sorted separately, test they are ordered together
        first_category_lower, first_alias_lower, first_alias_content_lower = self._create_alias_and_categories(
            "first order test case lower"
        )
        middle_category, middle_alias, middle_alias_content = self._create_alias_and_categories(
            "Middle Order Test Case"
        )
        # Previously lowercase and upper case would be sorted separately, test they are ordered together
        last_category_lower, last_alias_lower, last_alias_content_lower = self._create_alias_and_categories(
            "z order test case lower"
        )
        last_category, last_alias, last_alias_content = self._create_alias_and_categories(
            "Z Order Test Case Upper"
        )

        # Create the versions for each alias content
        from djangocms_versioning.models import Version
        Version.objects.create(content=first_alias_content, created_by=self.superuser)
        Version.objects.create(content=first_alias_content_lower, created_by=self.superuser)
        Version.objects.create(content=middle_alias_content, created_by=self.superuser)
        Version.objects.create(content=last_alias_content_lower, created_by=self.superuser)
        Version.objects.create(content=last_alias_content, created_by=self.superuser)

        with self.login_user_context(self.superuser):
            base_url = self.get_admin_url(AliasContent, "changelist")
            base_url += "?o=1"
            # en is the default language configured for the site
            response = self.client.get(base_url)
        soup = bs(response.content, "html.parser")
