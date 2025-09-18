from cms.app_base import CMSAppConfig
from cms.templatetags import cms_js_tags
from django.apps import apps
from django.conf import settings
from packaging.version import Version as PackageVersion

from .cms_wizards import create_alias_wizard
from .models import AliasContent, AliasPlugin, copy_alias_content
from .rendering import add_static_alias_js, render_alias_content

try:
    apps.get_app_config("djangocms_internalsearch")
    from .internal_search import AliasContentConfig
except (ImportError, LookupError):
    AliasContentConfig = None

djangocms_versioning_installed = apps.is_installed("djangocms_versioning")


class AliasCMSConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(AliasContent, render_alias_content, "alias")]
    moderated_models = [AliasContent]
    cms_wizards = [create_alias_wizard]

    djangocms_moderation_enabled = getattr(settings, "MODERATING_ALIAS_MODELS_ENABLED", True)
    djangocms_versioning_enabled = getattr(settings, "VERSIONING_ALIAS_MODELS_ENABLED", djangocms_versioning_installed)

    if djangocms_versioning_enabled:
        from cms.utils.i18n import get_language_tuple
        from djangocms_versioning import __version__ as djangocms_versioning_version
        from djangocms_versioning.datastructures import VersionableItem

        if PackageVersion(djangocms_versioning_version) < PackageVersion("2.4"):  # pragma: no cover
            raise ImportError(
                "djangocms_versioning >= 2.4.0 is required for djangocms_alias to work properly."
                " Please upgrade djangocms_versioning."
            )

        versioning = [
            VersionableItem(
                content_model=AliasContent,
                grouper_field_name="alias",
                extra_grouping_fields=["language"],
                version_list_filter_lookups={"language": get_language_tuple},
                copy_function=copy_alias_content,
                grouper_selector_option_label=lambda obj, lang: obj.get_name(lang),
                grouper_admin_mixin="__default__",
            ),
        ]

    djangocms_references_enabled = getattr(settings, "REFERENCES_ALIAS_MODELS_ENABLED", True)
    reference_fields = [
        (AliasPlugin, "alias"),
    ]

    # Internalsearch configuration
    if AliasContentConfig:
        djangocms_internalsearch_enabled = True
        internalsearch_config_list = [
            AliasContentConfig,
        ]

    # Allow for structure board editing of static aliases
    add_static_alias_js(cms_js_tags.render_cms_structure_js)
