from unittest import skipUnless

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.formats import localize
from django.utils.timezone import localtime

from cms.api import add_plugin
from cms.utils.i18n import force_language
from cms.utils.urlutils import add_url_parameters, admin_reverse

from bs4 import BeautifulSoup

from djangocms_alias.constants import (
    CHANGE_ALIAS_URL_NAME,
    USAGE_ALIAS_URL_NAME,
)
from djangocms_alias.models import (
    Alias,
    Alias as AliasModel,
    AliasContent,
    Category,
)
from djangocms_alias.utils import is_versioning_enabled
from tests.base import BaseAliasPluginTestCase


class AliasContentManagerTestCase(BaseAliasPluginTestCase):

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
    def test_alias_changelist_rendering_with_versioning_actions(self):
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

            base_url = self.get_admin_url(Alias, "changelist")
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
        settings_url = admin_reverse(
            '{}_{}_change'.format(
                expected_en_content._meta.app_label,
                expected_en_content.alias._meta.model_name
            ), args=(expected_en_content.alias.pk,)
        )

        self.assertIn(
            usage_url,
            response_content_decoded,
        )
        self.assertIn(
            settings_url,
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
            base_url = self.get_admin_url(Alias, "changelist")
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

    @skipUnless(is_versioning_enabled(), 'Test only relevant for versioning')
    def test_category_field_ordering_versioned(self):
        """
        Related category can be ordered by name, both in ascending and descending order, with versioning
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
            base_url = self.get_admin_url(Alias, "changelist")
            # o=1 indicates ascending alphabetical order on list_displays second entry
            base_url += "?o=1"
            # en is the default language configured for the site
            response = self.client.get(base_url)
        soup = BeautifulSoup(response.content, "html.parser")
        results = soup.find_all("td", class_="field-category")

        # Test results are in ascending alphabetical order
        self.assertEqual(results[0].text, first_alias_content.name)
        self.assertEqual(results[1].text, first_alias_content_lower.name)
        self.assertEqual(results[2].text, middle_alias_content.name)
        self.assertEqual(results[3].text, last_alias_content_lower.name)
        self.assertEqual(results[4].text, last_alias_content.name)

        with self.login_user_context(self.superuser):
            base_url = self.get_admin_url(Alias, "changelist")
            # o=-1 indicates descending alphabetical order on list_displays second entry
            base_url += "?o=-1"
            # en is the default language configured for the site
            response = self.client.get(base_url)
        soup = BeautifulSoup(response.content, "html.parser")
        results = soup.find_all("td", class_="field-category")
        # Test results are in descending alphabetical order
        self.assertEqual(results[4].text, first_alias_content.name)
        self.assertEqual(results[3].text, first_alias_content_lower.name)
        self.assertEqual(results[2].text, middle_alias_content.name)
        self.assertEqual(results[1].text, last_alias_content_lower.name)
        self.assertEqual(results[0].text, last_alias_content.name)

    @skipUnless(not is_versioning_enabled(), 'Test only relevant for versioning')
    def test_category_field_ordering_unversioned(self):
        """
        Related category can be ordered by name, both in ascending and descending order, without versioning
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

        with self.login_user_context(self.superuser):
            base_url = self.get_admin_url(AliasContent, "changelist")
            # o=1 indicates ascending alphabetical order on list_displays second entry
            base_url += "?o=1"
            # en is the default language configured for the site
            response = self.client.get(base_url)
        soup = BeautifulSoup(response.content, "html.parser")
        results = soup.find_all("td", class_="field-get_category")

        # Test results are in ascending alphabetical order
        self.assertEqual(results[0].text, first_alias_content.name)
        self.assertEqual(results[1].text, first_alias_content_lower.name)
        self.assertEqual(results[2].text, middle_alias_content.name)
        self.assertEqual(results[3].text, last_alias_content_lower.name)
        self.assertEqual(results[4].text, last_alias_content.name)

        with self.login_user_context(self.superuser):
            base_url = self.get_admin_url(AliasContent, "changelist")
            # o=-1 indicates descending alphabetical order on list_displays second entry
            base_url += "?o=-1"
            # en is the default language configured for the site
            response = self.client.get(base_url)
        soup = BeautifulSoup(response.content, "html.parser")
        results = soup.find_all("td", class_="field-get_category")

        # Test results are in descending alphabetical order
        self.assertEqual(results[4].text, first_alias_content.name)
        self.assertEqual(results[3].text, first_alias_content_lower.name)
        self.assertEqual(results[2].text, middle_alias_content.name)
        self.assertEqual(results[1].text, last_alias_content_lower.name)
        self.assertEqual(results[0].text, last_alias_content.name)

    def test_aliascontent_list_view(self):
        """
        The AliasContent admin change list displays correct details
        about the objects
        """
        category1 = Category.objects.create(
            name='Category 1',
        )
        category2 = Category.objects.create(
            name='Category 2',
        )

        plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='This is basic content',
        )

        alias1 = self._create_alias(
            [plugin],
            name='Alias 1',
            category=category1,
        )
        alias2 = self._create_alias(
            [plugin],
            name='Alias 2',
            category=category2,
        )
        alias3 = self._create_alias(
            [plugin],
            name='Alias 3',
            category=category1,
            published=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_list_alias_endpoint(),
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, category1.name)
        self.assertContains(response, category2.name)
        self.assertContains(response, 'Alias 1')
        self.assertContains(response, 'Alias 2')
        self.assertContains(response, 'Alias 3')

        if is_versioning_enabled():
            # we have both published and draft aliases so both should
            # be displayed
            self.assertContains(response, "Published")
            self.assertContains(response, "Draft")
        else:
            self.assertNotContains(response, "Published")
            self.assertNotContains(response, "Draft")

        aliascontent1_url = alias1.get_absolute_url()
        aliascontent2_url = alias2.get_absolute_url()
        aliascontent3_url = alias3.get_absolute_url()

        # when versioning is not enabled, the django admin change form
        # is used which used links to the aliascontent_change view
        if not is_versioning_enabled():
            alias1_content = alias1.get_content(language=self.language)
            alias2_content = alias2.get_content(language=self.language)
            alias3_content = alias3.get_content(language=self.language)
            aliascontent1_url = admin_reverse(
                CHANGE_ALIAS_URL_NAME, args=[alias1_content.pk]
            )
            aliascontent2_url = admin_reverse(
                CHANGE_ALIAS_URL_NAME, args=[alias2_content.pk]
            )
            aliascontent3_url = admin_reverse(
                CHANGE_ALIAS_URL_NAME, args=[alias3_content.pk]
            )

        self.assertContains(response, aliascontent1_url)
        self.assertContains(response, aliascontent2_url)
        self.assertContains(response, aliascontent3_url)


class CategoryAdminViewsTestCase(BaseAliasPluginTestCase):

    def test_changelist(self):
        Category.objects.all().delete()
        category1 = Category.objects.create()
        category2 = Category.objects.create()
        category1.translations.create(language_code='en', name='Category 1')
        category2.translations.create(language_code='en', name='Category 2')
        category1.translations.create(language_code='de', name='Kategorie 1')
        category2.translations.create(language_code='fr', name='Catégorie 2')
        category1.translations.create(language_code='it', name='Categoria 1')

        with self.login_user_context(self.superuser):
            with force_language('en'):
                en_response = self.client.get(self.get_category_list_endpoint())
            with force_language('de'):
                de_response = self.client.get(self.get_category_list_endpoint())
            with force_language('fr'):
                fr_response = self.client.get(self.get_category_list_endpoint())
            with force_language('it'):
                it_response = self.client.get(self.get_category_list_endpoint())

        self.assertContains(en_response, 'Category 1')
        self.assertContains(en_response, 'Category 2')
        self.assertNotContains(en_response, 'Kategorie 1')
        self.assertNotContains(en_response, 'Catégorie 2')
        self.assertNotContains(en_response, 'Categoria 1')

        self.assertContains(de_response, 'Kategorie 1')
        self.assertContains(de_response, 'Category 2')  # fallback
        self.assertNotContains(de_response, 'Category 1')
        self.assertNotContains(de_response, 'Catégorie 2')
        self.assertNotContains(de_response, 'Categoria 1')

        self.assertContains(fr_response, 'Category 1')  # fallback
        self.assertContains(fr_response, 'Catégorie 2')
        self.assertNotContains(fr_response, 'Category 2')
        self.assertNotContains(fr_response, 'Kategorie 1')
        self.assertNotContains(fr_response, 'Categoria 2')

        self.assertContains(it_response, 'Catégorie 2')  # fallback
        self.assertNotContains(it_response, 'Category 1')
        self.assertNotContains(it_response, 'Category 2')
        self.assertNotContains(it_response, 'Kategorie 1')
        self.assertNotContains(it_response, 'Categoria 2')

    def test_changelist_standard_user(self):
        """
        Expect a 302 redirect as the view is handled by the django admin
        """
        with self.login_user_context(self.get_standard_user()):
            response = self.client.get(self.get_category_list_endpoint())
        self.assertEqual(response.status_code, 302)

    def test_changelist_staff_user_without_permission(self):
        url = self.get_category_list_endpoint()
        with self.login_user_context(self.get_staff_user_with_std_permissions()):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_changelist_staff_user_with_permission(self):
        user = self.get_staff_user_with_std_permissions()
        user.user_permissions.add(Permission.objects.get(
            content_type__app_label='djangocms_alias',
            codename='change_category'))
        with self.login_user_context(user):
            response = self.client.get(self.get_category_list_endpoint())
        self.assertEqual(response.status_code, 200)

    def test_changelist_edit_button(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.get_category_list_endpoint())

        self.assertContains(
            response,
            '<a href="/en/admin/djangocms_alias/category/1/change/"'
        )

    def test_change_view(self):
        with self.login_user_context(self.superuser):
            self.client.post(
                add_url_parameters(
                    admin_reverse(
                        'djangocms_alias_category_change',
                        args=[self.category.pk],
                    ),
                    language='de',
                ),
                data={
                    'name': 'Alias Kategorie',
                },
            )

        self.assertEqual(self.category.name, 'test category')
        self.category.set_current_language('de')
        self.assertEqual(self.category.name, 'Alias Kategorie')


class AliasesManagerTestCase(BaseAliasPluginTestCase):

    def test_aliases_admin_entry_is_hidden(self):
        """
        Aliases admin entry should not be available via the admin menu
        """
        index_url = reverse('admin:index')

        self.client.force_login(self.superuser)

        response = self.client.get(index_url)

        unexpected_content = '<th scope="row"><a href="/en/admin/djangocms_alias/aliascontent/">Alias contents</a></th>'
        expected_content = '<th scope="row"><a href="/en/admin/djangocms_alias/alias/">Aliases</a></th>'

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_content)
        self.assertNotContains(response, unexpected_content)

    def test_aliases_endpoint_accessible_via_url(self):
        """
        Aliases admin endpoint should still be accessible via the endpoint
        """
        base_url = self.get_admin_url(AliasModel, "changelist")

        with self.login_user_context(self.superuser):
            response = self.client.get(base_url)

        module_name = response.context_data['module_name']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(module_name, 'aliases')
