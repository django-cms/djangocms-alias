from functools import cache

from django.apps import apps


@cache
def get_versionable_item(cms_config) -> type | None:
    if hasattr(cms_config, "get_contract"):
        return cms_config.get_contract("djangocms_versioning")
    return None


@cache
def is_versioning_enabled() -> bool:
    from .models import AliasContent

    for app_config in apps.get_app_configs():
        try:
            print(app_config)
            return app_config.cms_extension.is_content_model_versioned(AliasContent)
        except AttributeError:
            continue
    return False


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
