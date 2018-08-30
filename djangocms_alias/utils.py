from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import add_url_parameters, admin_reverse

from .compat import CMS_36
from .constants import DETAIL_ALIAS_URL_NAME


__all__ = [
    'alias_plugin_reverse',
]


def alias_plugin_reverse(viewname, *args, **kwargs):
    parameters = kwargs.pop('parameters', {})

    if CMS_36 and viewname == DETAIL_ALIAS_URL_NAME:
        parameters[get_cms_setting('CMS_TOOLBAR_URL__BUILD')] = "1"

    reversed_url = admin_reverse(viewname, *args, **kwargs)
    return add_url_parameters(reversed_url, **parameters)
