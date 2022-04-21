from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from cms.forms.utils import get_sites
from cms.utils.i18n import get_language_tuple, get_site_language_from_request


from .cms_config import AliasCMSConfig
from .constants import (
    LANGUAGE_FILTER_URL_PARAM,
    SITE_FILTER_NO_SITE_VALUE,
    SITE_FILTER_URL_PARAM,
)

djangocms_versioning_enabled = AliasCMSConfig.djangocms_versioning_enabled



class LanguageFilter(admin.SimpleListFilter):
    title = _("Language")
    parameter_name = LANGUAGE_FILTER_URL_PARAM

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


class SiteFilter(admin.SimpleListFilter):
    title = _("Site")
    parameter_name = SITE_FILTER_URL_PARAM

    def lookups(self, request, model_admin):
        return [(site.pk, site.name) for site in get_sites()]

    def queryset(self, request, queryset):
        chosen_site = self.value()
        if chosen_site and chosen_site == SITE_FILTER_NO_SITE_VALUE:
            return queryset.filter(alias__site__isnull=True)
        elif chosen_site:
            return queryset.filter(alias__site__pk=int(chosen_site))
        return queryset

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("All"),
        }
        yield {
            "selected": self.value() == SITE_FILTER_NO_SITE_VALUE,
            "query_string": changelist.get_query_string(
                {self.parameter_name: SITE_FILTER_NO_SITE_VALUE}
            ),
            "display": _("No site"),
        }
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }

if djangocms_versioning_enabled:
    from djangocms_versioning.constants import UNPUBLISHED

    class UnpublishedFilter(admin.SimpleListFilter):
        title = _("unpublished")
        parameter_name = "unpublished"

        def lookups(self, request, model_admin):
            return (("1", _("Show")),)

        def queryset(self, request, queryset):
            show = self.value()
            if show == "1":
                return queryset.filter(versions__state=UNPUBLISHED)
            else:
                return queryset.exclude(versions__state=UNPUBLISHED)

        def choices(self, changelist):
            yield {
                "selected": self.value() is None,
                "query_string": changelist.get_query_string(remove=[self.parameter_name]),
                "display": _("Hide"),
            }
            for lookup, title in self.lookup_choices:
                yield {
                    "selected": self.value() == str(lookup),
                    "query_string": changelist.get_query_string(
                        {self.parameter_name: lookup}
                    ),
                    "display": title,
                }
