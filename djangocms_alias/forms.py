from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import (
    AdminTextInputWidget,
    RelatedFieldWidgetWrapper,
)
from django.utils.translation import ugettext_lazy as _
from django_select2.forms import Select2Widget, ModelSelect2Widget

from cms.models import CMSPlugin, Placeholder
from cms.utils.permissions import has_plugin_permission
from cms.utils.permissions import get_model_permission_codename

from .constants import SELECT2_ALIAS_URL_NAME
from .models import Alias as AliasModel
from .models import AliasPlugin, Category
from .utils import alias_plugin_reverse


__all__ = [
    'AliasPluginForm',
    'BaseCreateAliasForm',
    'CreateAliasForm',
    'CreateAliasWizardForm',
    'CreateCategoryWizardForm',
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
    language = forms.CharField(widget=forms.HiddenInput())

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


class CreateAliasForm(BaseCreateAliasForm, forms.ModelForm):
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

    class Meta:
        model = AliasModel
        fields = [
            'name',
            'category',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')

        super().__init__(*args, **kwargs)

        if not has_plugin_permission(self.user, 'Alias', 'add'):
            self.fields['replace'].widget = forms.HiddenInput()

        self.set_category_widget(self.user)

    def set_category_widget(self, user):
        formfield = self.fields['category']
        formfield.widget = get_category_widget(formfield, user)

    def get_plugins(self):
        plugin = self.cleaned_data.get('plugin')
        placeholder = self.cleaned_data.get('placeholder')

        if placeholder:
            plugins = placeholder.get_plugins(
                self.cleaned_data.get('language'),
            )
        else:
            plugins = plugin.get_tree(plugin).order_by('path')
        return list(plugins)

    def save(self):
        from .cms_plugins import Alias

        alias = AliasModel.objects.create(
            name=self.cleaned_data.get('name'),
            category=self.cleaned_data.get('category'),
        )
        if self.cleaned_data.get('replace'):
            placeholder = self.cleaned_data.get('placeholder')
            plugin = self.cleaned_data.get('plugin')
            source_plugins = None
        else:
            placeholder, plugin = None, None
            source_plugins = self.get_plugins()
        new_plugin = Alias.populate_alias(
            alias=alias,
            replaced_placeholder=placeholder,
            replaced_plugin=plugin,
            language=self.cleaned_data.get('language'),
            plugins=source_plugins,
        )
        return new_plugin


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

    @property
    def media(self):
        from .cms_plugins import Alias
        return Alias().media

    def set_category_widget(self, user):
        formfield = self.fields['category']
        formfield.widget = get_category_widget(formfield, user)


class CreateCategoryWizardForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            'name',
        ]

    @property
    def media(self):
        from .cms_plugins import Alias
        return Alias().media


class AliasSelect2Widget(ModelSelect2Widget):

    def get_url(self):
        return alias_plugin_reverse(SELECT2_ALIAS_URL_NAME)


class AliasPluginForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=Select2Widget(
            attrs={
                'data-placeholder': _('Select category to restrict the list of aliases below'),  # noqa: E501
            },
        ),
        required=False,
    )
    alias = forms.ModelChoiceField(
        queryset=AliasModel.objects.all(),
        widget=AliasSelect2Widget(
            model=AliasModel,
            dependent_fields={'category': 'category'},
            search_fields=('name__icontains', ),
            attrs={
                'data-placeholder': _('Select an alias'),
            },
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['category'].initial = self.instance.alias.category_id

    class Meta:
        model = AliasPlugin
        fields = (
            'category',
            'alias',
        )
