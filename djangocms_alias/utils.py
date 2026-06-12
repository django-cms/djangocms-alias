from functools import cache

from django.apps import apps


def get_current_site(request):
    from cms.utils import get_current_site as cms_get_current_site

    try:
        return cms_get_current_site(request)
    except TypeError:
        # django CMS < 5.1
        return cms_get_current_site()


@cache
def get_versionable_item(cms_config) -> type | None:
    if hasattr(cms_config, "get_contract"):
        return cms_config.get_contract("djangocms_versioning")
    elif apps.is_installed("djangocms_versioning"):
        # Pre django CMS 5.1
        try:
            from djangocms_versioning.datastructures import VersionableItem

            return VersionableItem
        except ModuleNotFoundError as exc:
            # Only treat a missing djangocms_versioning module as "no versioning";
            # re-raise for any other import issue so real errors are not hidden.
            if exc.name in ("djangocms_versioning.datastructures", "djangocms_versioning"):
                return None
            raise
    return None


def is_versioning_enabled() -> bool:
    """
    is_versioning_enabled returns True if djangocms-alias has registered itself
    for verisoning
    """
    cms_config = apps.get_app_config("djangocms_alias").cms_config
    return bool(getattr(cms_config, "versioning", False))


def get_alias_usage_context(alias) -> dict:
    """Common template context for the usage and delete confirmation views."""
    from cms.models import Page

    objects_list = sorted(
        alias.objects_using,
        # First show Pages on list
        key=lambda obj: isinstance(obj, Page),
        reverse=True,
    )
    return {
        "objects_list": objects_list,
        # Usages without a visible object (e.g. clipboard content or orphaned
        # placeholders) - set by accessing objects_using above
        "hidden_usages": getattr(alias, "_hidden_usages", []),
    }


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
