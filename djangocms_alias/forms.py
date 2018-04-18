from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import (
    AdminTextInputWidget,
    RelatedFieldWidgetWrapper,
)
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin, Placeholder
from cms.utils.permissions import get_model_permission_codename

from .cms_plugins import Alias
from .models import Alias as AliasModel
from .models import Category


__all__ = [
    'BaseCreateAliasForm',
    'CreateAliasForm',
    'CreateAliasWizardForm',
    'DetachAliasPluginForm',
]


def get_category_widget(formfield, user):
    dbfield = AliasModel._meta.get_field('category')
    return RelatedFieldWidgetWrapper(
        formfield.widget,
        dbfield.rel,
        admin_site=admin.site,
        can_add_related=user.has_perm(
            get_model_permission_codename(Category, 'add'),
        ),
        can_change_related=user.has_perm(
            get_model_permission_codename(Category, 'change'),
        ),
        can_delete_related=user.has_perm(
            get_model_permission_codename(Category, 'delete'),
        ),
    )


class BaseCreateAliasForm(forms.Form):
    plugin = forms.ModelChoiceField(
        queryset=CMSPlugin.objects.exclude(plugin_type='Alias'),
        required=False,
        widget=forms.HiddenInput(),
    )
    placeholder = forms.ModelChoiceField(
        queryset=Placeholder.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        cleaned_data = super().clean()

        plugin = cleaned_data.get('plugin')
        placeholder = cleaned_data.get('placeholder')

        if not plugin and not placeholder:
            raise forms.ValidationError(
                _('A plugin or placeholder is required to create an alias.')
            )

        if plugin and placeholder:
            raise forms.ValidationError(
                _(
                    'An alias can only be created from a plugin or placeholder, '  # noqa: E501
                    'not both.'
                )
            )

        return cleaned_data


class CreateAliasForm(BaseCreateAliasForm):
    name = forms.CharField(required=True, widget=AdminTextInputWidget())
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
    )
    replace = forms.BooleanField(
        label=_('Replace current plugin'),
        help_text=_('Replace current plugin with alias'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        can_replace = kwargs.pop('can_replace')
        self.user = kwargs.pop('user')

        super().__init__(*args, **kwargs)

        if not can_replace:
            self.fields['replace'].widget = forms.HiddenInput()

        self.set_category_widget(self.user)

    def set_category_widget(self, user):
        formfield = self.fields['category']
        formfield.widget = get_category_widget(formfield, user)

    def get_plugins(self):
        plugin = self.cleaned_data.get('plugin')
        placeholder = self.cleaned_data.get('placeholder')

        if placeholder:
            plugins = placeholder.get_plugins()
        else:
            plugins = plugin.get_tree(plugin).order_by('path')
        return list(plugins)


class CreateAliasWizardForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
    )

    class Meta:
        model = AliasModel
        fields = [
            'name',
            'category',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_category_widget(self.user)

    def media(self):
        return Alias().media

    def set_category_widget(self, user):
        formfield = self.fields['category']
        formfield.widget = get_category_widget(formfield, user)


class DetachAliasPluginForm(forms.Form):
    plugin = forms.ModelChoiceField(
        queryset=CMSPlugin.objects.filter(plugin_type='Alias'),
        widget=forms.HiddenInput(),
    )
    use_draft = forms.BooleanField(required=False)
    language = forms.CharField(widget=forms.HiddenInput)
