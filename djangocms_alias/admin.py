from django.contrib import admin
from django.db import models
from django.db.models import OuterRef, Subquery, functions
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from cms.admin.utils import GrouperModelAdmin
from cms.utils.permissions import get_model_permission_codename
from cms.utils.urlutils import admin_reverse, static_with_version

from parler.admin import TranslatableAdmin

from .cms_config import AliasCMSConfig
from .constants import (
    CHANGE_ALIAS_URL_NAME,
    DELETE_ALIAS_URL_NAME,
    LIST_ALIAS_URL_NAME,
    USAGE_ALIAS_URL_NAME,
)
from .filters import CategoryFilter, SiteFilter
from .forms import AliasGrouperAdminForm
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

alias_admin_classes = [GrouperModelAdmin]
alias_admin_list_display = ['content__name', 'category', 'admin_list_actions']
djangocms_versioning_enabled = AliasCMSConfig.djangocms_versioning_enabled

if djangocms_versioning_enabled:
    from djangocms_versioning.admin import StateIndicatorMixin
    from djangocms_versioning.helpers import get_latest_admin_viewable_content
    from djangocms_versioning.models import Version
    from djangocms_versioning.versionables import for_content

    class ExtendedGrouperVersioningMixin:
        def get_queryset(self, request):
            alias_content_types = for_content(AliasContent).content_types
            qs = super().get_queryset(request)
            versions = Version.objects.filter(object_id=OuterRef("pk"), content_type__in=alias_content_types)
            contents = AliasContent.admin_manager.latest_content(
                alias=OuterRef("pk"), language=self.language,
            ).annotate(
                content_created_by=Subquery(versions.values("created_by")[:1]),
                content_modified=functions.Lower(Subquery(versions.values("modified")[:1])),
            )
            qs = qs.annotate(
                content_created_by=Subquery(contents.values("content_created_by")[:1]),
                content_modified=Subquery(contents.values("content_modified")[:1]),
            )
            return qs

        def get_version(self, obj):
            """
            Return the latest version of a given object
            :param obj: Versioned Content instance
            :return: Latest Version linked with content instance
            """
            content = get_latest_admin_viewable_content(obj, language=self.language)
            return content.versions.first() if content else None

        def get_author(self, obj):
            """
            Return the author who created a version
            :param obj: Versioned content model Instance
            :return: Author
            """
            return getattr(self.get_version(obj), "created_by", None)

        # This needs to target the annotation, or ordering will be alphabetically, with uppercase then lowercase
        get_author.admin_order_field = "content_created_by"
        get_author.short_description = _("Author")

        def get_modified_date(self, obj):
            """
            Get the last modified date of a version
            :param obj: Versioned content model Instance
            :return: Modified Date
            """
            return getattr(self.get_version(obj), "modified", None)

        get_modified_date.admin_order_field = "content_modified"
        get_modified_date.short_description = _("Modified")

    alias_admin_classes.insert(0, ExtendedGrouperVersioningMixin)
    alias_admin_classes.insert(0, StateIndicatorMixin)
    alias_admin_list_display.insert(-1, "get_author")
    alias_admin_list_display.insert(-1, "get_modified_date")
    alias_admin_list_display.insert(-1, "state_indicator")


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
class AliasAdmin(*alias_admin_classes):
    list_display = alias_admin_list_display
    list_display_links = None
    list_filter = (SiteFilter, CategoryFilter, )
    fields = ('content__name', 'category', 'site', 'content__language')
    readonly_fields = ('static_code', )
    form = AliasGrouperAdminForm
    extra_grouping_fields = ("language",)
    EMPTY_CONTENT_VALUE = mark_safe(_("<i>Missing language</i>"))

    def get_urls(self):
        return urlpatterns + super().get_urls()

    def get_actions_list(self):
        """Add alias usage list actions"""
        return super().get_actions_list() + [self._get_alias_usage_link,]

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

        # Only emit content changes if Versioning is not installed because
        # Versioning emits its own signals for changes
        if not is_versioning_enabled():
            emit_content_change(
                AliasContent._base_manager.filter(alias=obj),
                sender=self.model,
            )

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # This is bad and I should feel bad.
        if 'placeholder' in perms_needed:
            perms_needed.remove('placeholder')
        return deleted_objects, model_count, perms_needed, protected

    def delete_model(self, request, obj):
        super().delete_model(request, obj)

        # Only emit content changes if Versioning is not installed because
        # Versioning emits it' own signals for changes
        if not is_versioning_enabled():
            emit_content_delete(
                AliasContent._base_manager.filter(alias=obj),
                sender=self.model,
            )

    def _get_alias_usage_link(self, obj, request, disabled=False):
        url = admin_reverse(USAGE_ALIAS_URL_NAME, args=[obj.pk])
        return self.admin_action_button(url, "info", _("View usage"), disabled=disabled)

    def _get_alias_delete_link(self, obj, request):
        url = admin_reverse(DELETE_ALIAS_URL_NAME, args=[obj.pk])
        return self.admin_action_button(url, "bin", _("Delete Alias"),
                                        disabled=not self.has_delete_permission(request, obj))


@admin.register(AliasContent)
class AliasContentAdmin(admin.ModelAdmin):
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
    @admin.display(
        description=_('category'),
        ordering="alias_category_translations_ordered",
    )
    def get_category(self, obj):
        return obj.alias.category

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
