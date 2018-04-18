from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import (
    AdminTextInputWidget,
    RelatedFieldWidgetWrapper,
)
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin, Placeholder

from .models import Alias, Category


__all__ = [
    'BaseCreateAliasForm',
    'CreateAliasForm',
    'DetachAliasPluginForm',
]


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
        super().__init__(*args, **kwargs)
        if not can_replace:
            self.fields['replace'].widget = forms.HiddenInput()

    def set_category_widget(self, request):
        related_modeladmin = admin.site._registry.get(Category)
        dbfield = Alias._meta.get_field('category')
        formfield = self.fields['category']
        formfield.widget = RelatedFieldWidgetWrapper(
            formfield.widget,
            dbfield.rel,
            admin_site=admin.site,
            can_add_related=related_modeladmin.has_add_permission(request),
            can_change_related=related_modeladmin.has_change_permission(
                request,
            ),
            can_delete_related=related_modeladmin.has_delete_permission(
                request,
            ),
        )

    def get_plugins(self):
        plugin = self.cleaned_data.get('plugin')
        placeholder = self.cleaned_data.get('placeholder')

        if placeholder:
            plugins = placeholder.get_plugins()
        else:
            plugins = plugin.get_tree(plugin).order_by('path')
        return list(plugins)


class DetachAliasPluginForm(forms.Form):
    plugin = forms.ModelChoiceField(
        queryset=CMSPlugin.objects.filter(plugin_type='Alias'),
        widget=forms.HiddenInput(),
    )
    use_draft = forms.BooleanField(required=False)
    language = forms.CharField(widget=forms.HiddenInput)
