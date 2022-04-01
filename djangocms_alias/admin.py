from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from cms.utils.permissions import get_model_permission_codename

from parler.admin import TranslatableAdmin

from .cms_config import AliasCMSConfig
from .filters import LanguageFilter
from .forms import AliasContentForm
from .models import Alias, AliasContent, Category
from .urls import urlpatterns
from .utils import (
    emit_content_change,
    emit_content_delete,
    is_versioning_enabled,
)


__all__ = [
    'AliasAdmin',
    'CategoryAdmin',
    'AliasContentAdmin',
]

alias_content_admin_classes = [admin.ModelAdmin]
alias_content_admin_list_display = ('name', 'get_category',)
djangocms_versioning_enabled = AliasCMSConfig.djangocms_versioning_enabled

if djangocms_versioning_enabled:
    from djangocms_versioning.admin import ExtendedVersionAdminMixin
    alias_content_admin_classes.insert(0, ExtendedVersionAdminMixin)
    alias_content_admin_list_display = ('name', 'get_category',)


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['name']

    def save_model(self, request, obj, form, change):
        change = not obj._state.adding
        super().save_model(request, obj, form, change)
        if change:
            # Dont emit delete content because there is on_delete=PROTECT for
            # category FK on alias
            emit_content_change(
                AliasContent._base_manager.filter(alias__in=obj.aliases.all()),
                sender=self.model,
            )


@admin.register(Alias)
class AliasAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['site', 'category']
    fields = ('category',)
    readonly_fields = ('static_code', 'site')

    def get_urls(self):
        return urlpatterns + super().get_urls()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Alias can be deleted by users who can add aliases,
        # if that alias is not referenced anywhere.
        if obj:
            if not obj.is_in_use:
                return request.user.has_perm(
                    get_model_permission_codename(self.model, 'add'),
                )
            return request.user.is_superuser
        return False

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # This is bad and I should feel bad.
        if 'placeholder' in perms_needed:
            perms_needed.remove('placeholder')
        return deleted_objects, model_count, perms_needed, protected

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        emit_content_change(
            AliasContent._base_manager.filter(alias=obj),
            sender=self.model,
        )

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        emit_content_delete(
            AliasContent._base_manager.filter(alias=obj),
            sender=self.model,
        )


@admin.register(AliasContent)
class AliasContentAdmin(*alias_content_admin_classes):
    form = AliasContentForm
    list_filter = (LanguageFilter, )
    list_display = alias_content_admin_list_display
    change_form_template = "admin/djangocms_alias/aliascontent/change_form.html"

    # Add Alias category in the admin manager list and order field
    def get_category(self, obj):
        return obj.alias.category

    class Media:
        css = {
            "all": ("djangocms_versioning/css/actions.css",)
        }

    def _get_references_link(self, obj, request):
        content_type_id = ContentType.objects.get(app_label="djangocms_alias", model="aliascontent").id

        url = reverse(
            "djangocms_references:references-index",
            kwargs={"content_type_id": content_type_id, "object_id": obj.id},
        )

        return render_to_string("admin/djangocms_references/references_icon.html", {"url": url})

    def get_list_display(self, request):
        # get configured list_display
        list_display = self.list_display
        # Add versioning information and action fields
        list_display += [
            self._list_actions(request)
        ]
        return list_display

    get_category.short_description = _('category')
    get_category.admin_order_field = "alias__category"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Only emit content changes if Versioning is not installed because
        # Versioning emits it's own signals for changes
        if not is_versioning_enabled():
            emit_content_change([obj], sender=self.model)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)

        # Only emit content changes if Versioning is not installed because
        # Versioning emits it's own signals for changes
        if not is_versioning_enabled():
            emit_content_delete([obj], sender=self.model)

    def get_list_actions(self):
        """
        Collect rendered actions from implemented methods and return as list
        """
        return [
            self._get_preview_link,
            self._get_manage_versions_link,
            self._get_references_link,
        ]

    def _get_preview_link(self, obj, request, disabled=False):
        """
        Return a user friendly button for previewing the content model
        :param obj: Instance of versioned content model
        :param request: The request to admin menu
        :param disabled: Should the link be marked disabled?
        :return: Preview icon template
        """
        preview_url = obj.get_absolute_url()
        if not preview_url:
            disabled = True

        return render_to_string(
            "djangocms_versioning/admin/icons/preview.html",
            {"url": preview_url, "disabled": disabled, "keepsideframe": False},
        )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        # Provide additional context to the changeform
        extra_context['is_versioning_enabled'] = is_versioning_enabled()
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )
