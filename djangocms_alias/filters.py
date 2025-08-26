from cms.forms.utils import get_sites
from django.contrib import admin
from django.utils.encoding import smart_str
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from .cms_config import AliasCMSConfig
from .constants import (
    CATEGORY_FILTER_PARAM,
    SITE_FILTER_NO_SITE_VALUE,
    SITE_FILTER_URL_PARAM,
)
from .models import Category

djangocms_versioning_enabled = AliasCMSConfig.djangocms_versioning_enabled


class SiteFilter(admin.SimpleListFilter):
    title = _("Site")
    parameter_name = SITE_FILTER_URL_PARAM

    def lookups(self, request, model_admin):
        return [(site.pk, site.name) for site in get_sites()]

    def queryset(self, request, queryset):
        chosen_site = self.value()
        if chosen_site and chosen_site == SITE_FILTER_NO_SITE_VALUE:
            return queryset.filter(site__isnull=True)
        elif chosen_site:
            return queryset.filter(site__pk=int(chosen_site))
        return queryset

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("All"),
        }
        yield {
            "selected": self.value() == SITE_FILTER_NO_SITE_VALUE,
            "query_string": changelist.get_query_string({self.parameter_name: SITE_FILTER_NO_SITE_VALUE}),
            "display": _("No site"),
        }
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }


class CategoryFilter(admin.SimpleListFilter):
    title = _("Category")
    parameter_name = CATEGORY_FILTER_PARAM

    def lookups(self, request, model_admin):
        # Only offer categories available
        qs = model_admin.get_queryset(request)
        cat_id = qs.values_list("category", flat=True)
        # Ensure the category is ordered by the name alphabetically by default
        cat = Category.objects.filter(pk__in=cat_id).translated(get_language()).order_by("translations__name")
        for obj in cat:
            yield str(obj.pk), smart_str(obj)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category=self.value()).distinct()

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("All"),
        }
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }


class UsedFilter(admin.SimpleListFilter):
    title = _("Usage in Alias Plugins")
    parameter_name = "used"

    def lookups(self, request, model_admin):
        return [
            ("yes", _("Used")),
            ("no", _("Unused")),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(cmsplugins_count__gt=0)
        elif value == "no":
            return queryset.filter(cmsplugins_count=0)
        return queryset

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("All"),
        }
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }
