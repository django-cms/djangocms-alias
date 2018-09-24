from cms.app_base import CMSAppConfig

from .models import AliasContent
from .rendering import render_alias_content
from .internal_search import AliasContentConfig

class AliasCMSConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(AliasContent, render_alias_content)]

    # internalsearch config
    djangocms_internalsearch_enabled = True

    if AliasContentConfig:
        internalsearch_config_list = [
            AliasContentConfig
        ]
