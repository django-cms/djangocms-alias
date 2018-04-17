from django.conf.urls import url

from .constants import (
    CATEGORY_LIST_URL_NAME,
    CREATE_ALIAS_URL_NAME,
    DELETE_ALIAS_PLUGIN_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    DETAIL_ALIAS_URL_NAME,
    LIST_ALIASES_URL_NAME,
    PUBLISH_ALIAS_URL_NAME,
)
from .views import (
    AliasDeleteView,
    AliasDetailView,
    AliasListView,
    CategoryListView,
    create_alias_view,
    detach_alias_plugin_view,
    publish_alias_view,
)


urlpatterns = [
    url(
        r'^create-alias/$',
        create_alias_view,
        name=CREATE_ALIAS_URL_NAME,
    ),
    url(
        r'^publish-alias/(?P<pk>\d+)/(?P<language>\w+)/$',
        publish_alias_view,
        name=PUBLISH_ALIAS_URL_NAME,
    ),
    url(
        r'^aliases/$',
        CategoryListView.as_view(),
        name=CATEGORY_LIST_URL_NAME,
    ),
    url(
        r'^aliases/category/(?P<category_pk>\d+)/$',
        AliasListView.as_view(),
        name=LIST_ALIASES_URL_NAME,
    ),
    url(
        r'^aliases/(?P<pk>\d+)/$',
        AliasDetailView.as_view(),
        name=DETAIL_ALIAS_URL_NAME,
    ),
    url(
        r'^detach-alias/$',
        detach_alias_plugin_view,
        name=DETACH_ALIAS_PLUGIN_URL_NAME,
    ),
    url(
        r'^delete-alias/(?P<pk>\d+)/$',
        AliasDeleteView.as_view(),
        name=DELETE_ALIAS_PLUGIN_URL_NAME,
    ),
]
