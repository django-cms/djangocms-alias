from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import add_url_parameters, admin_reverse

from .constants import DETAIL_ALIAS_URL_NAME


__all__ = [
    'alias_plugin_reverse',
]


def alias_plugin_reverse(viewname, *args, **kwargs):
    parameters = kwargs.pop('parameters', {})

    if viewname == DETAIL_ALIAS_URL_NAME:
        parameters = {
            **parameters,
            get_cms_setting('CMS_TOOLBAR_URL__BUILD'): "1",
        }

    reversed_url = admin_reverse(viewname, *args, **kwargs)
    return add_url_parameters(reversed_url, **parameters)


def is_detail_alias_view(request):
    match = request.resolver_match
    return match.url_name == DETAIL_ALIAS_URL_NAME
