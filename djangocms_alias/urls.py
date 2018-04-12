from django.conf.urls import url

from .constants import (
    CREATE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
)

from .views import (
    alias_detail_view,
    alias_list_view,
    create_alias_view,
    detach_alias_plugin_view,
)


urlpatterns = [
    url(
        r'^create-alias/$',
        create_alias_view,
        name=CREATE_ALIAS_URL_NAME,
    ),
    url(
        r'^aliases/$',
        alias_list_view,
        name=LIST_ALIASES_URL_NAME,
    ),
    url(
        r'^aliases/(?P<pk>\d+)/$',
        alias_detail_view,
        name=DETAIL_ALIAS_URL_NAME,
    ),
    url(
        r'^detach-alias/$',
        detach_alias_plugin_view,
        name=DETACH_ALIAS_PLUGIN_URL_NAME,
    ),
]
