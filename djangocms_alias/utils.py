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


def invalidate_alias_cache(alias) -> None:
    """Invalidates the caches holding rendered content of the alias. To be
    called when the visible content of an alias changes, e.g., upon publishing.

    * The placeholder cache of all placeholders showing the alias through an
      Alias plugin. Those placeholders are not touched when the alias changes.
      If such a placeholder belongs to another alias, the placeholders showing
      that alias are cleared, too.
    * The page cache of all pages: the pages showing the alias through the
      ``{% static_alias %}`` template tag cannot be determined.
    """
    from cms.cache import invalidate_cms_page_cache
    from cms.cache.placeholder import clear_placeholder_cache
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.sites.models import Site

    from .models import AliasContent, AliasPlugin

    alias_content_type = ContentType.objects.get_for_model(AliasContent)
    site_ids = None
    cleared = set()
    seen = set()
    alias_ids = {alias.pk}
    while alias_ids:
        seen |= alias_ids
        plugins = AliasPlugin.objects.filter(alias_id__in=alias_ids).select_related("placeholder")
        alias_content_ids = set()
        for plugin in plugins:
            placeholder = plugin.placeholder
            if placeholder is None or (placeholder.pk, plugin.language) in cleared:
                continue
            cleared.add((placeholder.pk, plugin.language))
            if placeholder.content_type_id == alias_content_type.pk:
                # The alias holding the plugin is shown somewhere else
                alias_content_ids.add(placeholder.object_id)
            if placeholder.page:
                placeholder_site_ids = [placeholder.page.site_id]
            else:
                # Not bound to a site, e.g., the placeholder of an alias
                if site_ids is None:
                    site_ids = list(Site.objects.values_list("pk", flat=True))
                placeholder_site_ids = site_ids
            for site_id in placeholder_site_ids:
                clear_placeholder_cache(placeholder, plugin.language, site_id)
        alias_ids = (
            set(AliasContent.admin_manager.filter(pk__in=alias_content_ids).values_list("alias_id", flat=True)) - seen
        )

    invalidate_cms_page_cache()
