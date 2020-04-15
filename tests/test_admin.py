from cms.test_utils.testcases import CMSTestCase

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
