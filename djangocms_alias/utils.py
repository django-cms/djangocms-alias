import uuid

from django.apps import apps

from cms.signals import post_obj_operation, pre_obj_operation


def is_versioning_enabled():
    from .models import AliasContent
    try:
        app_config = apps.get_app_config('djangocms_versioning')
        return app_config.cms_extension.is_content_model_versioned(AliasContent)
    except LookupError:
        return False


def send_pre_alias_operation(request, operation, sender=None, **kwargs):
    from .models import Alias
    token = str(uuid.uuid4())
    pre_obj_operation.send(
        sender=sender or Alias,
        operation=operation,
        request=request,
        token=token,
        **kwargs
    )
    return token


def send_post_alias_operation(request, operation, token, sender=None, **kwargs):
    from .models import Alias
    post_obj_operation.send(
        sender=sender or Alias,
        operation=operation,
        request=request,
        token=token,
        **kwargs
    )
