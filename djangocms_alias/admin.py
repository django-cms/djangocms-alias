from cms.admin.grouper import GrouperAdminMixin
from django.contrib import admin
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _, get_language

from cms.utils.permissions import get_model_permission_codename
from cms.utils.urlutils import admin_reverse, static_with_version

from parler.admin import TranslatableAdmin

from .cms_config import AliasCMSConfig
from .constants import USAGE_ALIAS_URL_NAME, LIST_ALIAS_URL_NAME, CHANGE_ALIAS_URL_NAME
from .filters import CategoryFilter, LanguageFilter, SiteFilter
from .forms import AliasContentForm, AliasGrouperAdminForm
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
alias_content_admin_list_filter = (SiteFilter, CategoryFilter, LanguageFilter,)
djangocms_versioning_enabled = AliasCMSConfig.djangocms_versioning_enabled

if djangocms_versioning_enabled:
    from djangocms_versioning.admin import ExtendedIndicatorVersionAdminMixin, StateIndicatorMixin

    from .filters import UnpublishedFilter
    alias_content_admin_classes.insert(0, ExtendedIndicatorVersionAdminMixin)
    alias_content_admin_list_display = ('name', 'get_category',)
    alias_content_admin_list_filter = (SiteFilter, CategoryFilter, LanguageFilter, UnpublishedFilter)


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['name']

    def save_model(self, request, obj, form, change):
        change = not obj._state.adding
        super().save_model(request, obj, form, change)
        if change:
            # Don't emit delete content because there is on_delete=PROTECT for
            # category FK on alias
            emit_content_change(
                AliasContent._base_manager.filter(alias__in=obj.aliases.all()),
                sender=self.model,
            )


@admin.register(Alias)
class AliasAdmin(GrouperAdminMixin, StateIndicatorMixin, admin.ModelAdmin):
    list_display = ['name', 'category', 'state_indicator',]
    list_filter = ['site', 'category']
    fields = ('name', 'category', 'site', 'language')
    readonly_fields = ('static_code', )
    form = AliasGrouperAdminForm
    extra_grouping_fields = ("language",)

    class Media:
        js = (
            "admin/js/jquery.init.js",
            "cms/js/admin/actions.js",
        )
        css = {"all": (
            "djangocms_versioning/css/actions.css",
        )}

    def get_urls(self):
        return urlpatterns + super().get_urls()

    def get_list_actions(self):
        """
        Collect rendered actions from implemented methods and return as list
        """
        if hasattr(super(), "get_list_actions"):
            list_actions = super().get_list_actions()
        else:
            list_actions = []
        return list_actions + [
            self._get_alias_usage_link,
        ]

    def get_list_display_links(self, request, list_display):
        """
        Remove the linked text when versioning is enabled, because versioning adds actions
        """
        if is_versioning_enabled():
            self.list_display_links = None
        return super().get_list_display_links(request, list_display)

    def can_change_content(self, request, content_obj):
        """Returns True if user can change content_obj"""
        if content_obj and is_versioning_enabled():
            from djangocms_versioning.models import Version

            version = Version.objects.get_for_content(content_obj)
            return version.check_modify.as_bool(request.user)
        return True

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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        emit_content_change(
            AliasContent._base_manager.filter(alias=obj),
            sender=self.model,
        )

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        emit_content_delete(
            AliasContent._base_manager.filter(alias=self.get_content_obj(obj)),
            sender=self.model,
        )
    def _get_alias_usage_link(self, obj, request, disabled=False):
        url = admin_reverse(USAGE_ALIAS_URL_NAME, args=[obj.pk])
        return render_to_string(
            "admin/djangocms_alias/icons/view_usage.html",
            {"url": url, "disabled": disabled},
        )


@admin.register(AliasContent)
class AliasContentAdmin(*alias_content_admin_classes):
    form = AliasContentForm
    list_filter = alias_content_admin_list_filter
    list_display = alias_content_admin_list_display
    # Disable dropdown actions
    actions = None
    change_form_template = "admin/djangocms_alias/aliascontent/change_form.html"

    class Media:
        css = {
            "all": (
                static_with_version("cms/css/cms.icons.css"),
            )
        }

    # Add Alias category in the admin manager list and order field
    def get_category(self, obj):
        return obj.alias.category

    get_category.short_description = _('category')
    get_category.admin_order_field = "alias_category_translations_ordered"

    # def has_add_permission(self, request, obj=None):
    #     # FIXME: It is not currently possible to add an alias from the django admin changelist issue #97
    #     # https://github.com/django-cms/djangocms-alias/issues/97
    #     return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Only emit content changes if Versioning is not installed because
        # Versioning emits its own signals for changes
        if not is_versioning_enabled():
            emit_content_change([obj], sender=self.model)

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # This is bad and I should feel bad.
        if 'placeholder' in perms_needed:
            perms_needed.remove('placeholder')
        return deleted_objects, model_count, perms_needed, protected

    def delete_model(self, request, obj):
        super().delete_model(request, obj)

        # Only emit content changes if Versioning is not installed because
        # Versioning emits it's own signals for changes
        if not is_versioning_enabled():
            emit_content_delete([obj], sender=self.model)

    def changelist_view(self, request, extra_context=None):
        """Needed for the Alias Content Admin breadcrumbs"""
        return HttpResponseRedirect(admin_reverse(
                LIST_ALIAS_URL_NAME,
            ))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Needed for the Alias Content Admin breadcrumbs"""
        obj = get_object_or_404(self.model, pk=object_id)
        return HttpResponseRedirect(admin_reverse(
            CHANGE_ALIAS_URL_NAME, args=(obj.alias_id,)
        ) + f"?language={obj.language}")

    def has_module_permission(self, request):
        """Hides admin class in admin site overview"""
        return False
