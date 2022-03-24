from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import (
    AdminTextInputWidget,
    RelatedFieldWidgetWrapper,
)
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin, Placeholder
from cms.utils.permissions import (
    get_model_permission_codename,
    has_plugin_permission,
)
from cms.utils.urlutils import admin_reverse

from parler.forms import TranslatableModelForm

from .constants import SELECT2_ALIAS_URL_NAME
from .models import Alias as AliasModel, AliasContent, AliasPlugin, Category
from .utils import emit_content_change, is_versioning_enabled


__all__ = [
    'AliasPluginForm',
    'BaseCreateAliasForm',
    'CreateAliasForm',
    'CreateAliasWizardForm',
    'CreateCategoryWizardForm',
    'SetAliasPositionForm',
]


def get_category_widget(formfield, user):
    dbfield = AliasModel._meta.get_field('category')
    return RelatedFieldWidgetWrapper(
        formfield.widget,
        dbfield.remote_field,
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
        self.user = kwargs.pop('user')

        super().__init__(*args, **kwargs)

        if not has_plugin_permission(self.user, 'Alias', 'add'):
            self.fields['replace'].widget = forms.HiddenInput()

        self.set_category_widget(self.user)

    def clean(self):
        cleaned_data = super().clean()

        if AliasContent.objects.filter(
            name=cleaned_data.get('name'),
            language=cleaned_data.get('language'),
            alias__category=cleaned_data.get('category'),
        ).exists():
            raise forms.ValidationError(
                _('Alias with this Name and Category already exists.')
            )

        return cleaned_data

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
            plugins = [plugin] + list(plugin.get_descendants())
        return list(plugins)

    def save(self):
        alias = AliasModel.objects.create(
            category=self.cleaned_data.get('category'),
        )
        alias_content = AliasContent.objects.create(
            alias=alias,
            name=self.cleaned_data.get('name'),
            language=self.cleaned_data.get('language'),
        )
        if is_versioning_enabled():
            from djangocms_versioning.models import Version
            Version.objects.create(content=alias_content, created_by=self.user)
        if self.cleaned_data.get('replace'):
            placeholder = self.cleaned_data.get('placeholder')
            plugin = self.cleaned_data.get('plugin')
            source_plugins = None
        else:
            placeholder, plugin = None, None
            source_plugins = self.get_plugins()
        new_plugin = alias_content.populate(
            replaced_placeholder=placeholder,
            replaced_plugin=plugin,
            plugins=source_plugins,
        )
        return alias, alias_content, new_plugin


class CreateAliasWizardForm(forms.Form):
    name = forms.CharField(
        label=_('Name'),
        required=True,
        widget=AdminTextInputWidget()
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not getattr(self, 'user', None):
            self.user = self._request.user
        self.set_category_widget(self.user)

    def set_category_widget(self, user):
        formfield = self.fields['category']
        formfield.widget = get_category_widget(formfield, user)

    @transaction.atomic
    def save(self):
        alias = AliasModel.objects.create(
            category=self.cleaned_data.get('category'),
        )
        alias_content = AliasContent.objects.create(
            alias=alias,
            name=self.cleaned_data.get('name'),
            language=self.language_code,
        )

        if is_versioning_enabled():
            from djangocms_versioning.models import Version
            Version.objects.create(content=alias_content, created_by=self._request.user)

        emit_content_change([alias_content])
        return alias


class CreateCategoryWizardForm(TranslatableModelForm):

    class Meta:
        model = Category
        fields = [
            'name',
        ]


class SetAliasPositionForm(forms.Form):
    alias = forms.ModelChoiceField(queryset=AliasModel.objects.all())
    position = forms.IntegerField(min_value=0)

    def clean(self):
        cleaned_data = super().clean()
        position = cleaned_data.get('position')
        alias = cleaned_data.get('alias')

        if position is not None and alias:
            if position == alias.position:
                raise forms.ValidationError({
                    'position': _(
                        'Argument position have to be different than current '
                        'alias position'
                    ),
                })

            alias_count = alias.category.aliases.count()
            if position > alias_count - 1:
                raise forms.ValidationError({
                    'position': _(
                        'Invalid position in category list, '
                        'available positions are: {}'
                    ).format([i for i in range(0, alias_count)])
                })

        return cleaned_data

    def save(self, *args, **kwargs):
        position = self.cleaned_data['position']
        alias = self.cleaned_data['alias']
        alias._set_position(position)
        return alias


class Select2Mixin:

    class Media:
        css = {
            'all': ('cms/js/select2/select2.css', ),
        }
        js = (
            'admin/js/jquery.init.js',
            'cms/js/select2/select2.js',
            'djangocms_alias/js/dist/bundle.alias.create.min.js',
        )


class CategorySelectWidget(Select2Mixin, forms.Select):
    pass


class AliasSelectWidget(Select2Mixin, forms.TextInput):

    def get_url(self):
        return admin_reverse(SELECT2_ALIAS_URL_NAME)

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.setdefault('data-select2-url', self.get_url())
        return attrs


class AliasPluginForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        label=_('Category'),
        queryset=Category.objects.all(),
        widget=CategorySelectWidget(
            attrs={
                'data-placeholder': _('Select category to restrict the list of aliases below'),  # noqa: E501
            },
        ),
        empty_label='',
        required=False,
    )
    alias = forms.ModelChoiceField(
        label=_('Alias'),
        queryset=AliasModel.objects.all(),
        widget=AliasSelectWidget(
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
            'template',
        )


class AliasContentForm(forms.ModelForm):

    alias = forms.ModelChoiceField(
        queryset=AliasModel.objects.all(),
        required=True,
        widget=forms.HiddenInput(),
    )
    language = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = AliasContent
        fields = ('name',)

    def clean(self):
        cleaned_data = super().clean()

        alias = cleaned_data.get('alias')
        if not alias:
            return cleaned_data

        if AliasContent.objects.filter(
            name=cleaned_data.get('name'),
            language=cleaned_data.get('language'),
            alias__category=alias.category,
        ).exists():
            raise forms.ValidationError(
                _('Alias with this Name and Category already exists.')
            )

        return cleaned_data
