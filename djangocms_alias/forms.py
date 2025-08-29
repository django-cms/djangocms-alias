from cms.models import CMSPlugin, Placeholder
from cms.utils import get_current_site
from cms.utils.permissions import (
    get_model_permission_codename,
    has_plugin_permission,
)
from cms.utils.urlutils import admin_reverse
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import (
    AdminTextInputWidget,
    AutocompleteSelect,
    RelatedFieldWidgetWrapper,
)
from django.contrib.sites.models import Site
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from parler.forms import TranslatableModelForm

from .constants import CATEGORY_SELECT2_URL_NAME, SELECT2_ALIAS_URL_NAME
from .models import (
    Alias,
    AliasContent,
    AliasPlugin,
    Category,
)
from .models import (
    Alias as AliasModel,
)
from .utils import emit_content_change

__all__ = [
    "AliasPluginForm",
    "BaseCreateAliasForm",
    "CreateAliasForm",
    "CreateAliasWizardForm",
    "CreateCategoryWizardForm",
]


def get_category_widget(formfield, user):
    dbfield = AliasModel._meta.get_field("category")
    return RelatedFieldWidgetWrapper(
        formfield.widget,
        dbfield.remote_field,
        admin_site=admin.site,
        can_add_related=user.has_perm(
            get_model_permission_codename(Category, "add"),
        ),
        can_change_related=user.has_perm(
            get_model_permission_codename(Category, "change"),
        ),
        can_delete_related=user.has_perm(
            get_model_permission_codename(Category, "delete"),
        ),
    )


class BaseCreateAliasForm(forms.Form):
    plugin = forms.ModelChoiceField(
        queryset=CMSPlugin.objects.exclude(plugin_type="Alias"),
        required=False,
        widget=forms.HiddenInput(),
    )
    placeholder = forms.ModelChoiceField(
        queryset=Placeholder.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    language = forms.CharField(widget=forms.HiddenInput())

    class Media:
        js = ("djangocms_alias/js/databridge.js",)

    def clean(self):
        cleaned_data = super().clean()

        plugin = cleaned_data.get("plugin")
        placeholder = cleaned_data.get("placeholder")

        if not plugin and not placeholder:
            raise forms.ValidationError(_("A plugin or placeholder is required to create an alias."))

        if plugin and placeholder:
            raise forms.ValidationError(
                _(
                    "An alias can only be created from a plugin or placeholder, "  # noqa: E501
                    "not both."
                )
            )

        return cleaned_data


class CreateAliasForm(BaseCreateAliasForm):
    name = forms.CharField(required=True, widget=AdminTextInputWidget())
    site = forms.ModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
    )
    replace = forms.BooleanField(
        label=_("Replace current plugin"),
        help_text=_("Replace current plugin with alias"),
        required=False,
    )

    def __init__(self, *args, initial=None, **kwargs):
        self.user = kwargs.pop("user")

        super().__init__(*args, initial=initial, **kwargs)

        self.fields["site"].widget = AutocompleteSelect(
            Alias.site.field,
            admin.site,
            choices=self.fields["site"].choices,
            attrs={"data-placeholder": _("Select a site")},
        )
        self.fields["category"].widget = AutocompleteSelect(
            Alias.category.field,
            admin.site,
            choices=self.fields["category"].choices,
            attrs={"data-placeholder": _("Select a category")},
        )

        # Remove the replace option, if user does not have permission to add "Alias"
        if not has_plugin_permission(self.user, "Alias", "add"):
            self.fields["replace"].widget = forms.HiddenInput()

        # Remove the replace option, if "Alias" cannot be a child of parent plugin
        initial = initial or {}
        plugin = initial.get("plugin")
        if plugin and plugin.parent:
            plugin_class = plugin.parent.get_plugin_class()
            allowed_children = plugin_class.get_child_classes(plugin.placeholder.slot, instance=plugin.parent)
            if allowed_children and "Alias" not in allowed_children:
                self.fields["replace"].widget = forms.HiddenInput()

        self.set_category_widget(self.user)
        self.fields["site"].initial = get_current_site()

    def clean(self):
        cleaned_data = super().clean()

        if AliasContent.objects.filter(
            name=cleaned_data.get("name"),
            language=cleaned_data.get("language"),
            alias__category=cleaned_data.get("category"),
        ).exists():
            raise forms.ValidationError(_("Alias with this Name and Category already exists."))

        return cleaned_data

    def set_category_widget(self, user):
        formfield = self.fields["category"]
        formfield.widget = get_category_widget(formfield, user)

    def get_plugins(self):
        plugin = self.cleaned_data.get("plugin")
        placeholder = self.cleaned_data.get("placeholder")

        if placeholder:
            plugins = placeholder.get_plugins(
                self.cleaned_data.get("language"),
            )
        else:
            plugins = [plugin] + list(plugin.get_descendants())
        return list(plugins)

    def save(self):
        alias = AliasModel.objects.create(
            category=self.cleaned_data.get("category"),
            site=self.cleaned_data.get("site"),
        )
        alias_content = AliasContent.objects.with_user(self.user).create(
            alias=alias,
            name=self.cleaned_data.get("name"),
            language=self.cleaned_data.get("language"),
        )
        if self.cleaned_data.get("replace"):
            placeholder = self.cleaned_data.get("placeholder")
            plugin = self.cleaned_data.get("plugin")
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
    name = forms.CharField(label=_("Name"), required=True, widget=AdminTextInputWidget())
    site = forms.ModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not getattr(self, "user", None):
            self.user = self._request.user
        self.set_category_widget(self.user)
        self.fields["site"].initial = get_current_site()

    def set_category_widget(self, user):
        formfield = self.fields["category"]
        formfield.widget = get_category_widget(formfield, user)

    @transaction.atomic
    def save(self):
        alias = AliasModel.objects.create(
            category=self.cleaned_data.get("category"),
            site=self.cleaned_data.get("site"),
        )
        alias_content = AliasContent.objects.with_user(self._request.user).create(
            alias=alias,
            name=self.cleaned_data.get("name"),
            language=self.language_code,
        )

        emit_content_change([alias_content])
        return alias


class CreateCategoryWizardForm(TranslatableModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
        ]


class Select2Mixin:
    class Media:
        css = {
            "screen": ("cms/js/select2/select2.css",),
        }
        js = (
            "admin/js/jquery.init.js",
            "cms/js/select2/select2.js",
            "djangocms_alias/js/create.js",
            "djangocms_alias/js/alias_plugin.js",
        )


class CategorySelectWidget(Select2Mixin, forms.TextInput):
    def get_url(self):
        return admin_reverse(CATEGORY_SELECT2_URL_NAME)

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.setdefault("data-select2-url", self.get_url())
        return attrs


class AliasSelectWidget(Select2Mixin, forms.TextInput):
    def get_url(self):
        return admin_reverse(SELECT2_ALIAS_URL_NAME)

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.setdefault("data-select2-url", self.get_url())
        return attrs


class AliasPluginForm(forms.ModelForm):
    site = forms.ModelChoiceField(
        label=_("Site"),
        queryset=Site.objects.all(),
        widget=forms.HiddenInput,
        required=False,
    )

    category = forms.ModelChoiceField(
        label=_("Category"),
        queryset=Category.objects.all(),
        widget=CategorySelectWidget(
            attrs={
                "data-placeholder": _("Select category to restrict the list of aliases below"),  # noqa: E501
            },
        ),
        empty_label="",
        required=False,
    )
    alias = forms.ModelChoiceField(
        label=_("Alias"),
        queryset=AliasModel.objects.all(),
        widget=AliasSelectWidget(
            attrs={
                "data-placeholder": _("Select an alias"),
            },
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_category_widget_value()

    def _set_category_widget_value(self):
        """
        When the user loads the form the site and category should be pre-selected
        """
        # If the form is changing an existing Alias
        # Be sure to show the values for an Alias
        if self.instance and self.instance.pk:
            self.fields["category"].initial = self.instance.alias.category
        # Otherwise this is creation
        # Set the site to the current site by default
        else:
            pass
        self.fields["site"].initial = get_current_site()

    class Meta:
        model = AliasPlugin
        fields = (
            "site",
            "category",
            "alias",
            "template",
        )


class AliasGrouperAdminForm(forms.ModelForm):
    class Meta:
        model = Alias
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if AliasContent.admin_manager.filter(
            name=cleaned_data.get("name"),
            language=cleaned_data.get("language"),
            alias__category=cleaned_data.get("category"),
        ).exists():
            raise forms.ValidationError(_("Alias with this Name and Category already exists."))

        return cleaned_data
