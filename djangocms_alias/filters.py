from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from cms.utils.i18n import get_language_tuple, get_site_language_from_request


class LanguageFilter(admin.SimpleListFilter):
    title = _("language")
    parameter_name = "language"

    def lookups(self, request, model_admin):
        return get_language_tuple()

    def queryset(self, request, queryset):
        language = self.value()
        if language is None:
            language = get_site_language_from_request(request)
        return queryset.filter(language=language)

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("Current"),
        }
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }

from django.contrib.sites.models import Site
from cms.forms.utils import get_sites


class SiteFilter(admin.SimpleListFilter):
    title = _("Site")
    parameter_name = "site"
    no_site_set_value = "none"

    def lookups(self, request, model_admin):
        return [(site.pk, site.name) for site in get_sites()]

    def queryset(self, request, queryset):
        chosen_site = self.value()
        if chosen_site and chosen_site == self.no_site_set_value:
            return queryset.filter(alias__site__isnull=True)
        elif chosen_site:
            return queryset.filter(alias__site=chosen_site)
        return queryset

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("Current"),
        }
        yield {
            "selected": self.value() is self.no_site_set_value,
            "query_string": changelist.get_query_string(
                {self.parameter_name: self.no_site_set_value}
            ),
            "display": _("None"),
        }
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }
