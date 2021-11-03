from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q

from djangocms_alias.models import AliasContent


def _get_excluded_alias_site_list(site):
    """
    Get a list of Alias objects that cannot be viewed by the current site

    :param site: A site object to query against
    :return: A filtered list of alias objects
    """
    alias_exclusion_set = AliasContent._original_manager.exclude(Q(alias__site=site) | Q(alias__site__isnull=True))
    alias_exclusion_set.select_related('alias')
    return alias_exclusion_set.values_list('id', flat=True)


def content_expiry_site_alias_excluded_set(queryset, request):
    """
    Filter ContentExpiry records to show only Alias objects available on a given site.
    Model structure: Expiry->Version->Content->Alias->site

    CAUTION: This helper is used by a third party (djangocms-content-expiry), change with caution.

    :param site: A site object to query against
    :param queryset: A queryset object of ContentExpiry records
    :return: A filtered list of Content Expiry records minus any none site PageContent models
    """
    current_site = get_current_site(request)
    alias_content_ctype = ContentType.objects.get_for_model(AliasContent)
    alias_exclusion_set = _get_excluded_alias_site_list(current_site)

    queryset = queryset.exclude(
      version__content_type=alias_content_ctype, version__object_id__in=alias_exclusion_set
    )

    return queryset
