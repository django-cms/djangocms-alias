from django.urls import re_path


from . import constants, views  # isort:skip


urlpatterns = [
    re_path(
        r'^create-alias/$',
        views.create_alias_view,
        name=constants.CREATE_ALIAS_URL_NAME,
    ),
    re_path(
        r'^aliases/$',
        views.CategoryListView.as_view(),
        name=constants.CATEGORY_LIST_URL_NAME,
    ),
    re_path(
        r'^aliases/(?P<pk>\d+)/usage/$',
        views.alias_usage_view,
        name=constants.USAGE_ALIAS_URL_NAME,
    ),
    re_path(
        r'^detach-alias/(?P<plugin_pk>\d+)/$',
        views.detach_alias_plugin_view,
        name=constants.DETACH_ALIAS_PLUGIN_URL_NAME,
    ),
    re_path(
        r'^delete-alias/(?P<pk>\d+)/$',
        views.delete_alias_view,
        name=constants.DELETE_ALIAS_URL_NAME,
    ),
    re_path(
        r'^set-alias-position/$',
        views.set_alias_position_view,
        name=constants.SET_ALIAS_POSITION_URL_NAME,
    ),
    re_path(
        r'^select2/$',
        views.AliasSelect2View.as_view(),
        name=constants.SELECT2_ALIAS_URL_NAME,
    ),
    re_path(
        r'^category-select2/$',
        views.CategorySelect2View.as_view(),
        name=constants.CATEGORY_SELECT2_URL_NAME,
    ),


]
