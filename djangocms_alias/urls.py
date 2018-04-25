from django.conf.urls import url

from . import constants, views


urlpatterns = [
    url(
        r'^create-alias/$',
        views.create_alias_view,
        name=constants.CREATE_ALIAS_URL_NAME,
    ),
    url(
        r'^publish-alias/(?P<pk>\d+)/(?P<language>\w+)/$',
        views.publish_alias_view,
        name=constants.PUBLISH_ALIAS_URL_NAME,
    ),
    url(
        r'^aliases/$',
        views.CategoryListView.as_view(),
        name=constants.CATEGORY_LIST_URL_NAME,
    ),
    url(
        r'^aliases/category/(?P<category_pk>\d+)/$',
        views.AliasListView.as_view(),
        name=constants.LIST_ALIASES_URL_NAME,
    ),
    url(
        r'^aliases/(?P<pk>\d+)/$',
        views.AliasDetailView.as_view(),
        name=constants.DETAIL_ALIAS_URL_NAME,
    ),
    url(
        r'^detach-alias/(?P<plugin_pk>\d+)/$',
        views.detach_alias_plugin_view,
        name=constants.DETACH_ALIAS_PLUGIN_URL_NAME,
    ),
    url(
        r'^delete-alias/(?P<pk>\d+)/$',
        views.delete_alias_view,
        name=constants.DELETE_ALIAS_PLUGIN_URL_NAME,
    ),
    url(
        r'^draft-aliases-mode/$',
        views.set_alias_draft_mode_view,
        name=constants.SET_ALIAS_DRAFT_URL_NAME,
    ),
    url(
        r'^set-alias-position/$',
        views.set_alias_position_view,
        name=constants.SET_ALIAS_POSITION_URL_NAME,
    ),
    url(
        r'^select2/$',
        views.AliasSelect2View.as_view(),
        name=constants.SELECT2_ALIAS_URL_NAME,
    ),
]
