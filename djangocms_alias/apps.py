from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AliasConfig(AppConfig):
    name = "djangocms_alias"
    verbose_name = _("django CMS Alias")
    default_auto_field = "django.db.models.BigAutoField"
