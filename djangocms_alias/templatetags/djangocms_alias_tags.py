from django import template
from django.utils.safestring import mark_safe

from cms.toolbar.utils import get_toolbar_from_request

from ..constants import DETAIL_ALIAS_URL_NAME
from ..utils import alias_plugin_reverse


register = template.Library()


@register.simple_tag(takes_context=False)
def get_alias_url(alias):
    return alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk])


@register.inclusion_tag('djangocms_alias/alias_tag.html', takes_context=True)
def render_alias(context, instance, editable=False):
    request = context['request']

    toolbar = get_toolbar_from_request(request)
    renderer = toolbar.get_content_renderer()

    editable = editable and renderer._placeholders_are_editable
    source = instance.get_placeholder()

    if source:
        content = renderer.render_placeholder(
            placeholder=source,
            context=context,
            editable=editable,
        )
        return {'content': mark_safe(content)}
