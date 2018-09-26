from django.contrib.sites.models import Site

from cms.wizards.forms import WizardStep2BaseForm, step2_form_factory
from cms.wizards.helpers import get_entries as get_wizard_entires

from djangocms_alias.utils import is_versioning_enabled

from .base import BaseAliasPluginTestCase


class WizardsTestCase(BaseAliasPluginTestCase):

    def _get_wizard_instance(self, wizard_name):
        return [
            wizard
            for wizard in get_wizard_entires()
            if wizard.__class__.__name__ == wizard_name
        ][0]

    def _get_form_kwargs(self, data, language=None):
        language = language or self.language
        request = self.get_request('/', language=language)
        request.user = self.superuser
        return {
            'data': data,
            'wizard_language': language,
            'wizard_site': Site.objects.get_current(),
            'wizard_request': request,
        }

    def test_create_alias_wizard_instance(self):
        wizard = self._get_wizard_instance('CreateAliasWizard')
        self.assertEqual(wizard.title, 'New alias')

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
        wizard = self._get_wizard_instance('CreateAliasWizard')
        data = {
            'name': 'Content #1',
            'category': self.category.pk,
        }

        form_class = step2_form_factory(
            mixin_cls=WizardStep2BaseForm,
            entry_form_class=wizard.form,
        )
        form = form_class(**self._get_form_kwargs(data))

        self.assertTrue(form.is_valid())
        alias = form.save()

        with self.login_user_context(self.superuser):
            response = self.client.get(alias.get_absolute_url())
        self.assertContains(response, data['name'])

        if is_versioning_enabled():
            from djangocms_versioning.models import Version
            self.assertEqual(Version.objects.filter_by_grouper(alias).count(), 1)

    def test_create_alias_category_wizard_instance(self):
        wizard = self._get_wizard_instance('CreateAliasCategoryWizard')
        self.assertEqual(wizard.title, 'New alias category')

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
        wizard = self._get_wizard_instance('CreateAliasCategoryWizard')
        data = {
            'name': 'Category 1',
        }

        form_class = step2_form_factory(
            mixin_cls=WizardStep2BaseForm,
            entry_form_class=wizard.form,
        )
        form = form_class(**self._get_form_kwargs(data))

        self.assertTrue(form.is_valid())
        category = form.save()

        with self.login_user_context(self.superuser):
            response = self.client.get(category.get_absolute_url())
        self.assertContains(response, data['name'])
