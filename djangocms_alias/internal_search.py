from cms.toolbar.utils import get_object_preview_url, get_toolbar_from_request
from django.template import RequestContext
from django.utils.translation import gettext_lazy as _
from djangocms_internalsearch.base import BaseSearchConfig
from djangocms_internalsearch.helpers import get_request, get_version_object
from haystack import indexes

from .models import AliasContent


def get_title(obj):
    return obj.result.title


get_title.short_description = _("Title")


def get_category(obj):
    return obj.result.category


get_category.short_description = _("Category")


def get_language(obj):
    return obj.result.language


get_language.short_description = _("Language")


def get_url(obj):
    return obj.result.url


get_url.short_description = _("URL")


def get_version_status(obj):
    return obj.result.version_status


get_version_status.short_description = _("Version status")


class AliasContentConfig(BaseSearchConfig):
    # indexes definition
    title = indexes.CharField(model_attr="name")
    category = indexes.CharField()
    language = indexes.CharField(model_attr="language")
    url = indexes.CharField()
    version_status = indexes.CharField()

    # admin setting
    list_display = [get_title, get_category, get_language, get_url, get_version_status]
    search_fields = ()
    list_filter = ()

    model = AliasContent

    def prepare_text(self, obj):
        request = get_request(obj.language)
        context = RequestContext(request)
        if "request" not in context:
            context["request"] = request

        toolbar = get_toolbar_from_request(request)
        renderer = toolbar.get_content_renderer()
        source = obj.placeholder
        if not source:
            return
        content = renderer.render_placeholder(
            placeholder=source,
            context=context,
            editable=False,
        )
        return content

    def prepare_url(self, obj):
        return get_object_preview_url(obj)

    def prepare_category(self, obj):
        obj.alias.category.set_current_language(obj.language)
        return obj.alias.category.name

    def prepare_version_status(self, obj):
        version_obj = get_version_object(obj)
        if not version_obj:
            return
        return version_obj.state
