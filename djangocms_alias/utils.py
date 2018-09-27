from django.apps import apps


def is_versioning_enabled():
    from .models import AliasContent
    try:
        app_config = apps.get_app_config('djangocms_versioning')
        return app_config.cms_extension.is_content_model_versioned(AliasContent)
    except LookupError:
        return False
