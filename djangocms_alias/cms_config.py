from django.conf import settings

from cms.app_base import CMSAppConfig

from .models import AliasContent, copy_alias_content
from .rendering import render_alias_content


try:
    from .internal_search import AliasContentConfig
except ImportError:
    AliasContentConfig = None


class AliasCMSConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(AliasContent, render_alias_content)]

    djangocms_versioning_enabled = getattr(
        settings, 'VERSIONING_ALIAS_MODELS_ENABLED', True)
    if djangocms_versioning_enabled:
        from djangocms_versioning.datastructures import VersionableItem
        versioning = [
            VersionableItem(
                content_model=AliasContent,
                grouper_field_name='alias',
                copy_function=copy_alias_content,
                grouper_selector_option_label=lambda obj, lang: obj.get_name(lang),
            ),
        ]

    # Internalsearch configuration
    if AliasContentConfig:
        djangocms_internalsearch_enabled = True
        internalsearch_config_list = [
            AliasContentConfig,
        ]
