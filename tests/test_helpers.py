import datetime

from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.test import override_settings, RequestFactory

from cms.test_utils.testcases import CMSTestCase

from djangocms_alias.models import Alias as AliasModel, AliasContent, Category
from djangocms_alias.helpers import _get_excluded_alias_site_list
from djangocms_alias.utils import is_versioning_enabled


class ContentExpirySiteAliasHelperTestCase(CMSTestCase):

    @classmethod
    def setUpTestData(cls):
        # Site 1
        cls.site_1 = Site.objects.get(id=1)
        # Site 2
        cls.site_2 = Site(id=2, domain='example-2.com', name='example-2.com')
        cls.site_2.save()

        cls.category = Category.objects.create(name='site test category')

    def setUp(self):
        self.superuser = self.get_superuser()
        Site.objects.clear_cache()
        # Record that is expired by 1 day
        from_date = datetime.datetime.now()
        expire_at = from_date + datetime.timedelta(days=10)
        language = "en"
        # Create contents unbound to a site
        alias_1 = AliasModel.objects.create(
            category=self.category,
        )
        self.alias_content_1 = AliasContent.objects.create(
            alias=alias_1,
            name="no site alias 1",
            language=language,
        )
        if is_versioning_enabled():
            from djangocms_versioning.models import Version
            self.alias_1_version = Version.objects.create(content=self.alias_content_1, created_by=self.superuser)
            self.alias_1_version.publish(self.superuser)
        # Create contents on site 1
        alias_2 = AliasModel.objects.create(
            category=self.category,
            site=self.site_1,
        )
        self.alias_content_2 = AliasContent.objects.create(
            alias=alias_2,
            name="site 1 alias 1",
            language=language,
        )
        if is_versioning_enabled():
            from djangocms_versioning.models import Version
            self.alias_2_version = Version.objects.create(content=self.alias_content_2, created_by=self.superuser)
            self.alias_2_version.publish(self.superuser)
        # Create contents on site 2
        alias_3 = AliasModel.objects.create(
            category=self.category,
            site=self.site_2,
        )
        self.alias_content_3 = AliasContent.objects.create(
            alias=alias_3,
            name="site 1 alias 1",
            language=language,
        )
        if is_versioning_enabled():
            from djangocms_versioning.models import Version
            self.alias_3_version = Version.objects.create(content=self.alias_content_3, created_by=self.superuser)
            self.alias_3_version.publish(self.superuser)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_helper_alias_exclusion_list_current_site(self):
        """
        The list of Alias objects must be filtered by the default / current site
        """
        alias_exclusion_list = _get_excluded_alias_site_list(self.site_1)

        self.assertNotIn(self.alias_content_1.pk, alias_exclusion_list)
        self.assertNotIn(self.alias_content_2.pk, alias_exclusion_list)
        self.assertIn(self.alias_content_3.pk, alias_exclusion_list)

    @override_settings(SITE_ID=2)
    def test_helper_alias_exclusion_list_other_site(self):
        """
        The list of Alias objects must be filtered by a different site
        """
        alias_exclusion_list = _get_excluded_alias_site_list(self.site_2)

        self.assertNotIn(self.alias_content_1.pk, alias_exclusion_list)
        self.assertIn(self.alias_content_2.pk, alias_exclusion_list)
        self.assertNotIn(self.alias_content_3.pk, alias_exclusion_list)
