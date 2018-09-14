def is_versioning_enabled():
    from .cms_config import AliasCMSConfig
    return AliasCMSConfig.djangocms_versioning_enabled
