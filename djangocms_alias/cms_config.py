from cms.app_base import CMSAppConfig

from .models import AliasContent
from .rendering import render_alias_content


class AliasCMSConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(AliasContent, render_alias_content)]
