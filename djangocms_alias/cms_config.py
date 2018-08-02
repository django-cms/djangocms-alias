from cms.app_base import CMSAppConfig


class AliasCMSConfig(CMSAppConfig):
    djangocms_versioning_enabled = False
    versioning_models = []
