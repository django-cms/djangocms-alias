from django.conf import settings


def is_versioning_enabled():
    from .cms_config import AliasCMSConfig
    return (
        AliasCMSConfig.djangocms_versioning_enabled
        and 'djangocms_versioning' in getattr(settings, 'INSTALLED_APPS', [])
    )
