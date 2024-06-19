from cms.utils.permissions import get_model_permission_codename
from cms.utils.urlutils import admin_reverse
from django.apps import apps
from django.contrib import admin, messages
from django.db.models.functions import Lower
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin

from .cms_config import AliasCMSConfig
from .constants import USAGE_ALIAS_URL_NAME
from .filters import CategoryFilter, LanguageFilter, SiteFilter
from .forms import AliasContentForm
from .models import Alias, AliasContent, Category
from .urls import urlpatterns
from .utils import (
    emit_content_change,
    emit_content_delete,
    is_versioning_enabled,
)

__all__ = [
    "AliasAdmin",
    "CategoryAdmin",
    "AliasContentAdmin",
]

alias_content_admin_classes = [admin.ModelAdmin]
alias_content_admin_list_display = (
    "name",
    "get_category",
)
alias_content_admin_list_filter = (
    SiteFilter,
    CategoryFilter,
    LanguageFilter,
)
djangocms_versioning_enabled = AliasCMSConfig.djangocms_versioning_enabled

if djangocms_versioning_enabled:
    from djangocms_versioning.admin import ExtendedVersionAdminMixin

    from .filters import UnpublishedFilter

    alias_content_admin_classes.insert(0, ExtendedVersionAdminMixin)
    alias_content_admin_list_display = (
        "name",
        "get_category",
    )
    alias_content_admin_list_filter = (
        SiteFilter,
        CategoryFilter,
        LanguageFilter,
        UnpublishedFilter,
    )


def is_moderation_enabled():
    """
    Returns True if the AliasContent model is enabled for moderation.
    If it is not, or djangocms_moderation is not installed, returns False.

    :returns: True or False
    """
    try:
        moderation_config = apps.get_app_config("djangocms_moderation")
    except LookupError:
        return False

    return AliasContent in moderation_config.cms_extension.moderated_models


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ["name"]

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
    list_display = ["name", "category"]
    list_filter = ["site", "category"]
    fields = ("category", "site")
    readonly_fields = ("static_code",)

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
                    get_model_permission_codename(self.model, "add"),
                )
            return request.user.is_superuser
        return False

    def get_deleted_objects(self, objs, request):
        (
            deleted_objects,
            model_count,
            perms_needed,
            protected,
        ) = super().get_deleted_objects(objs, request)
        # This is bad and I should feel bad.
        if "placeholder" in perms_needed:
            perms_needed.remove("placeholder")
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

    def has_module_permission(self, request):
        return False


@admin.register(AliasContent)
class AliasContentAdmin(*alias_content_admin_classes):
    form = AliasContentForm
    list_filter = alias_content_admin_list_filter
    list_display = alias_content_admin_list_display
    search_fields = ["name"]
    # Disable dropdown actions
    actions = None
    change_form_template = "admin/djangocms_alias/aliascontent/change_form.html"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Force the category set to Lower, to be able to sort the category in ascending/descending order
        queryset = queryset.annotate(alias_category_translations_ordered=Lower("alias__category__translations__name"))
        return queryset

    # Add Alias category in the admin manager list and order field
    @admin.display(
        description=_("category"),
        ordering="alias_category_translations_ordered",
    )
    def get_category(self, obj):
        return obj.alias.category

    def has_add_permission(self, request, obj=None):
        # FIXME: It is not currently possible to add an alias from the django admin changelist issue #97
        # https://github.com/django-cms/djangocms-alias/issues/97
        return False

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

        if obj.alias._default_manager.filter(language=obj.language).count() == 1:
            message = _(
                "Alias content for language {} deleted. A new empty alias content will be created if needed."
            ).format(obj.language)
            self.message_user(request, message, level=messages.WARNING)

        return super().delete_model(
            request=request,
            obj=obj,
        )

    def get_list_actions(self):
        """
        Collect rendered actions from implemented methods and return as list
        """
        return [
            self._get_preview_link,
            self._get_edit_link,
            self._get_manage_versions_link,
            self._get_change_alias_settings_link,
            self._get_rename_alias_link,
            self._get_alias_usage_link,
        ]

    def get_list_display_links(self, request, list_display):
        """
        Remove the linked text when versioning is enabled, because versioning adds actions
        """
        if is_versioning_enabled():
            self.list_display_links = None
        return super().get_list_display_links(request, list_display)

    def _get_rename_alias_link(self, obj, request, disabled=False):
        url = admin_reverse(
            f"{obj._meta.app_label}_{obj._meta.model_name}_change",
            args=(obj.pk,),
        )
        return render_to_string(
            "admin/djangocms_alias/icons/rename_alias.html",
            {"url": url, "disabled": disabled},
        )

    def _get_alias_usage_link(self, obj, request, disabled=False):
        url = admin_reverse(USAGE_ALIAS_URL_NAME, args=[obj.alias.pk])
        return render_to_string(
            "admin/djangocms_alias/icons/view_usage.html",
            {"url": url, "disabled": disabled},
        )

    def _get_change_alias_settings_link(self, obj, request, disabled=False):
        url = admin_reverse(
            f"{obj._meta.app_label}_{obj.alias._meta.model_name}_change",
            args=(obj.alias.pk,),
        )
        return render_to_string(
            "admin/djangocms_alias/icons/change_alias_settings.html",
            {"url": url, "disabled": disabled},
        )

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

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        # Provide additional context to the changeform
        extra_context["is_versioning_enabled"] = is_versioning_enabled()
        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

    def get_actions(self, request):
        """
        If djangocms-moderation is enabled, adds admin action to allow multiple pages to be added to a moderation
        collection.

        :param request: Request object
        :returns: dict of admin actions
        """
        actions = super().get_actions(request)
        if not is_moderation_enabled():
            return actions

        from djangocms_moderation.admin_actions import add_items_to_collection

        actions["add_items_to_collection"] = (
            add_items_to_collection,
            "add_items_to_collection",
            add_items_to_collection.short_description,
        )
        return actions
