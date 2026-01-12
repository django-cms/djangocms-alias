from __future__ import annotations

from collections.abc import Iterable

from cms.admin.utils import GrouperModelAdmin
from cms.utils.permissions import get_model_permission_codename
from cms.utils.urlutils import admin_reverse
from django import forms
from django.contrib import admin, messages
from django.db import models
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin

from .constants import (
    CHANGE_ALIAS_URL_NAME,
    DELETE_ALIAS_URL_NAME,
    LIST_ALIAS_URL_NAME,
    USAGE_ALIAS_URL_NAME,
)
from .filters import CategoryFilter, SiteFilter, UsedFilter
from .models import Alias, AliasContent, Category
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


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ["name"]
    search_fields = ["translations__name"]

    def save_model(self, request, obj, form, change):
        change = not obj._state.adding
        super().save_model(request, obj, form, change)
        if change:
            # Don't emit delete content because there is on_delete=PROTECT for
            # category FK on alias
            emit_content_change(
                AliasContent.admin_manager.filter(alias__in=obj.aliases.all()),
                sender=self.model,
            )


@admin.register(Alias)
class AliasAdmin(GrouperModelAdmin):
    list_display = ["content_name", "category", "static", "used", "admin_list_actions"]
    list_display_links = None
    list_filter = (
        SiteFilter,
        CategoryFilter,
        UsedFilter,
    )
    fields = ("content__name", "category", "site", "content__language")
    readonly_fields = ("static_code",)
    search_fields = ["content__name"]
    autocomplete_fields = ["category", "site"]
    extra_grouping_fields = ("language",)
    EMPTY_CONTENT_VALUE = mark_safe(_("<i>Missing language</i>"))

    def get_actions_list(self) -> list:
        """Add alias usage list actions"""
        return super().get_actions_list() + [self._get_alias_usage_link, self._get_alias_delete_link]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet:
        qs = super().get_queryset(request)
        # Annotate each Alias with a boolean indicating if related cmsplugins exist
        return qs.annotate(cmsplugins_count=models.Count("cms_plugins"))

    def get_list_display(self, request: HttpRequest) -> Iterable[str]:
        list_display = super().get_list_display(request)
        list_display = list(list_display)
        if hasattr(self, "get_author"):
            list_display.insert(-1, "get_author")
        if hasattr(self, "get_modified_date"):
            list_display.insert(-1, "get_modified_date")
        return list_display

    @admin.display(description=_("Name"), ordering=models.functions.Lower("contents__name"))
    def content_name(self, obj: Alias) -> str:
        return self.get_content_field(obj, "name") or obj.static_code or self.EMPTY_CONTENT_VALUE

    @admin.display(description=_("Used"), boolean=True, ordering="cmsplugins_count")
    def used(self, obj: Alias) -> bool | None:
        if obj.static_code and obj.cmsplugins_count == 0:
            return None
        return obj.cmsplugins_count > 0

    @admin.display(description=_("Static"), boolean=True)
    def static(self, obj: Alias) -> bool:
        return bool(obj.static_code)

    def has_delete_permission(self, request: HttpRequest, obj: Alias = None) -> bool:
        # Alias can be deleted by users who can add aliases,
        # if that alias is not referenced anywhere.
        if obj:
            if not obj.is_in_use:
                return request.user.has_perm(
                    get_model_permission_codename(self.model, "add"),
                )
            return request.user.is_superuser
        return True

    def save_model(self, request: HttpRequest, obj: Alias, form: forms.Form, change: bool) -> None:
        super().save_model(request, obj, form, change)

        # Only emit content changes if Versioning is not installed because
        # Versioning emits its own signals for changes
        if not is_versioning_enabled():
            emit_content_change(
                AliasContent.admin_manager.filter(alias=obj),
                sender=self.model,
            )

    def get_deleted_objects(self, objs, request: HttpRequest) -> tuple:
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

    def delete_model(self, request: HttpRequest, obj: Alias):
        pk = obj.pk
        super().delete_model(request, obj)

        # Only emit content changes if Versioning is not installed because
        # Versioning emits it' own signals for changes
        if not is_versioning_enabled():
            emit_content_delete(
                AliasContent.admin_manager.filter(alias_id=pk),
                sender=self.model,
            )

    def _get_alias_usage_link(self, obj: Alias, request: HttpRequest) -> str:
        url = admin_reverse(USAGE_ALIAS_URL_NAME, args=[obj.pk])
        return self.admin_action_button(url, "info", _("View usage"))

    def _get_alias_delete_link(self, obj: Alias, request: HttpRequest) -> str:
        url = admin_reverse(DELETE_ALIAS_URL_NAME, args=[obj.pk])
        return self.admin_action_button(
            url,
            "bin",
            _("Delete Alias"),
            disabled=not self.has_delete_permission(request, obj),
        )


@admin.register(AliasContent)
class AliasContentAdmin(admin.ModelAdmin):
    # Disable dropdown actions
    actions = None
    change_form_template = "admin/djangocms_alias/aliascontent/change_form.html"

    def changelist_view(self, request: HttpRequest, extra_context: dict = None) -> HttpResponse:
        """Needed for the Alias Content Admin breadcrumbs"""
        return HttpResponseRedirect(
            admin_reverse(
                LIST_ALIAS_URL_NAME,
            )
        )

    def change_view(
        self,
        request: HttpRequest,
        object_id: int,
        form_url: str = "",
        extra_context: dict = None,
    ) -> HttpResponse:
        """Needed for the Alias Content Admin breadcrumbs"""
        obj = self.model.admin_manager.filter(pk=object_id).first()
        if not obj:
            raise Http404()
        return HttpResponseRedirect(
            admin_reverse(CHANGE_ALIAS_URL_NAME, args=(obj.alias_id,)) + f"?language={obj.language}"
        )

    def has_module_permission(self, request: HttpRequest) -> bool:
        """Hides admin class in admin site overview"""

        return False

    def delete_model(self, request: HttpRequest, obj: AliasContent):
        if obj.alias._default_manager.filter(language=obj.language).count() == 1:
            message = _(
                "Alias content for language {} deleted. A new empty alias content will be created if needed."
            ).format(obj.language)
            self.message_user(request, message, level=messages.WARNING)

        return super().delete_model(
            request=request,
            obj=obj,
        )
