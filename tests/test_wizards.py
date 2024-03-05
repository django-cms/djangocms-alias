from cms.toolbar.utils import get_object_edit_url
from cms.utils import get_current_site
from cms.wizards.forms import WizardStep2BaseForm, step2_form_factory
from cms.wizards.helpers import get_entries as get_wizard_entires
from django.contrib.sites.models import Site
from django.utils import translation

from djangocms_alias.models import Category
from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class WizardsTestCase(BaseAliasPluginTestCase):
    def _get_wizard_instance(self, wizard_name):
        return [wizard for wizard in get_wizard_entires() if wizard.__class__.__name__ == wizard_name][0]

    def _get_form_kwargs(self, data, language=None):
        language = language or self.language
        request = self.get_request("/", language=language)
        request.user = self.superuser
        return {
            "data": data,
            "wizard_language": language,
            "wizard_site": Site.objects.get_current(),
            "wizard_request": request,
        }

    def test_create_alias_wizard_instance(self):
        wizard = self._get_wizard_instance("CreateAliasWizard")
        self.assertEqual(wizard.title, "New alias")

        self.assertTrue(wizard.user_has_add_permission(self.superuser))
        self.assertTrue(
            wizard.user_has_add_permission(self.get_staff_user_with_alias_permissions()),  # noqa: E501
        )
        self.assertFalse(
            wizard.user_has_add_permission(self.get_staff_user_with_no_permissions()),  # noqa: E501
        )
        self.assertFalse(
            wizard.user_has_add_permission(self.get_standard_user()),
        )

    def test_create_alias_wizard_form(self):
        wizard = self._get_wizard_instance("CreateAliasWizard")
        data = {
            "name": "Content #1",
            "category": self.category.pk,
            "site": get_current_site().pk,
        }
        form_class = step2_form_factory(
            mixin_cls=WizardStep2BaseForm,
            entry_form_class=wizard.form,
        )
        form = form_class(**self._get_form_kwargs(data))

        self.assertTrue(form.is_valid())
        alias = form.save()

        self.assertEqual(form.fields["site"].initial, get_current_site())

        with self.login_user_context(self.superuser):
            url = get_object_edit_url(alias.get_content(show_draft_content=True))
            response = self.client.get(url)
        self.assertContains(response, data["name"])

        if is_versioning_enabled():
            from djangocms_versioning.models import Version

            self.assertEqual(Version.objects.filter_by_grouper(alias).count(), 1)

    def test_create_alias_wizard_form_with_no_category_fallback_language(self):
        """When creating an Alias via the Wizard an error can occur if the category
        doesn't have a valid translation
        """
        translation.activate("en")
        # A japanese translation that does not have any fallback settings!
        Category.objects.language("ja").create(name="Japanese category")

        wizard = self._get_wizard_instance("CreateAliasWizard")
        data = {
            "name": "Content #1",
            "category": None,
        }
        form_class = step2_form_factory(
            mixin_cls=WizardStep2BaseForm,
            entry_form_class=wizard.form,
        )
        form = form_class(**self._get_form_kwargs(data))
        category_form_queryset = form.declared_fields["category"].queryset

        self.assertEqual(form.fields["site"].initial, get_current_site())

        # Be sure that we have untranslated categories that enforces a fair test
        self.assertNotEqual(
            category_form_queryset.all().count(),
            category_form_queryset.active_translations().count(),
        )

        for category in category_form_queryset.all():
            # Each category string representation can be accessed without an error
            category_name = str(category)

            self.assertTrue(category_name)

    def test_create_alias_category_wizard_instance(self):
        wizard = self._get_wizard_instance("CreateAliasCategoryWizard")
        self.assertEqual(wizard.title, "New alias category")

        self.assertTrue(wizard.user_has_add_permission(self.superuser))
        self.assertTrue(
            wizard.user_has_add_permission(self.get_staff_user_with_alias_permissions()),  # noqa: E501
        )
        self.assertFalse(
            wizard.user_has_add_permission(self.get_staff_user_with_no_permissions()),  # noqa: E501
        )
        self.assertFalse(
            wizard.user_has_add_permission(self.get_standard_user()),
        )

    def test_create_alias_category_wizard_form(self):
        wizard = self._get_wizard_instance("CreateAliasCategoryWizard")
        data = {
            "name": "Category 1",
        }

        form_class = step2_form_factory(
            mixin_cls=WizardStep2BaseForm,
            entry_form_class=wizard.form,
        )
        form = form_class(**self._get_form_kwargs(data))

        self.assertTrue(form.is_valid())
        category = form.save()

        with self.login_user_context(self.superuser):
            response = self.client.get(category.get_admin_change_url())
        self.assertContains(response, data["name"])
