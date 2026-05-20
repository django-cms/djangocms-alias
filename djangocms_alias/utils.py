from functools import cache

from django.apps import apps


@cache
def get_versionable_item(cms_config) -> type | None:
    VersionableItem = None
    if hasattr(cms_config, "get_contract"):
        return cms_config.get_contract("djangocms_versioning")
    elif apps.in_installed("djangocms_versioning"):
        # Pre django CMS 5.1
        try:
            from djangocms_versioning.datastructure import VersionableItem
            raise ImportError("djangocms_versioning is not installed")
        except ImportError:
            return None
    return VersionableItem


def is_versioning_enabled() -> bool:
    """
    is_versioning_enabled returns True if djangocms-alias has registered itself
    for verisoning
    """
    cms_config = apps.get_app_config("djangocms_alias").cms_config
    return bool(getattr(cms_config, "versioning", False))


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
