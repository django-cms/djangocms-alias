from django.apps import apps


def is_versioning_enabled():
    from .models import AliasContent
    try:
        app_config = apps.get_app_config('djangocms_versioning')
        return app_config.cms_extension.is_content_model_versioned(AliasContent)
    except LookupError:
        return False


def emit_content_change(objs, sender=None):
    try:
        apps.get_app_config('djangocms_internalsearch')
        from djangocms_internalsearch.helpers import emit_content_change
    except (ImportError, LookupError):
        return

    for obj in objs:
        emit_content_change(obj, sender=sender)


def emit_content_delete(objs, sender=None):
    try:
        apps.get_app_config('djangocms_internalsearch')
        from djangocms_internalsearch.helpers import emit_content_delete
    except (ImportError, LookupError):
        return

    for obj in objs:
        emit_content_delete(obj, sender=sender)
