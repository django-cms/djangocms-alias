from django.urls import path


from . import constants, views  # isort:skip


urlpatterns = [
    path(
        'create-alias/',
        views.create_alias_view,
        name=constants.CREATE_ALIAS_URL_NAME,
    ),
    path(
        'aliases/<int:pk>/usage/',
        views.alias_usage_view,
        name=constants.USAGE_ALIAS_URL_NAME,
    ),
    path(
        'detach-alias/<int:plugin_pk>/',
        views.detach_alias_plugin_view,
        name=constants.DETACH_ALIAS_PLUGIN_URL_NAME,
    ),
    path(
        'delete-alias/<int:pk>/',
        views.delete_alias_view,
        name=constants.DELETE_ALIAS_URL_NAME,
    ),
    path(
        'select2/',
        views.AliasSelect2View.as_view(),
        name=constants.SELECT2_ALIAS_URL_NAME,
    ),
    path(
        'category-select2/',
        views.CategorySelect2View.as_view(),
        name=constants.CATEGORY_SELECT2_URL_NAME,
    ),


]
