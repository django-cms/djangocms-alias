from django.apps import apps
from django.conf import settings

from cms.app_base import CMSAppConfig

from .models import AliasContent, AliasPlugin, copy_alias_content
from .rendering import render_alias_content


try:
    apps.get_app_config('djangocms_internalsearch')
    from .internal_search import AliasContentConfig
except (ImportError, LookupError):
    AliasContentConfig = None

djangocms_versioning_installed = apps.is_installed("djangocms_versioning")


class AliasCMSConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(AliasContent, render_alias_content)]
    moderated_models = [AliasContent]

    djangocms_moderation_enabled = getattr(
        settings, 'MODERATING_ALIAS_MODELS_ENABLED', True)
    djangocms_versioning_enabled = getattr(
        settings, 'VERSIONING_ALIAS_MODELS_ENABLED', True) and djangocms_versioning_installed

    if djangocms_versioning_enabled:

        from cms.utils.i18n import get_language_tuple

        from djangocms_versioning.datastructures import VersionableItem

        versioning = [
            VersionableItem(
                content_model=AliasContent,
                grouper_field_name='alias',
                extra_grouping_fields=["language"],
                version_list_filter_lookups={"language": get_language_tuple},
                copy_function=copy_alias_content,
                grouper_selector_option_label=lambda obj, lang: obj.get_name(lang),
            ),
        ]

    djangocms_references_enabled = getattr(
        settings, 'REFERENCES_ALIAS_MODELS_ENABLED', True)
    reference_fields = [
        (AliasPlugin, 'alias'),
    ]

    # Internalsearch configuration
    if AliasContentConfig:
        djangocms_internalsearch_enabled = True
        internalsearch_config_list = [
            AliasContentConfig,
        ]
