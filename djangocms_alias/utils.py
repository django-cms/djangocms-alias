from django.apps import apps

from cms.utils.urlutils import admin_reverse

from .constants import CATEGORY_FILTER_URL_PARAM, LIST_ALIAS_URL_NAME


def is_versioning_enabled():
    from .models import AliasContent
    try:
        app_config = apps.get_app_config('djangocms_versioning')
        return app_config.cms_extension.is_content_model_versioned(AliasContent)
    except LookupError:
        return False


def url_for_category_list(category_id):
    """
    category_id: An id of a category
    returns: a url for the list of aliases for a given category.
    """
    return admin_reverse(LIST_ALIAS_URL_NAME) + f"?{CATEGORY_FILTER_URL_PARAM}={category_id}"


def emit_content_change(objs, sender=None):
    try:
        from djangocms_internalsearch.helpers import emit_content_change
    except ImportError:
        return

    for obj in objs:
        emit_content_change(obj, sender=sender)


def emit_content_delete(objs, sender=None):
    try:
        from djangocms_internalsearch.helpers import emit_content_delete
    except ImportError:
        return

    for obj in objs:
        emit_content_delete(obj, sender=sender)
