from cms.app_base import CMSAppConfig

from .models import AliasContent
from .rendering import render_alias_content
try:
    from .internal_search import AliasContentConfig
except ImportError:
    AliasContentConfig = None

class AliasCMSConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(AliasContent, render_alias_content)]

    # Internalsearch configuration
    if AliasContentConfig:
        djangocms_internalsearch_enabled = True

        internalsearch_config_list = [
            AliasContentConfig
        ]
