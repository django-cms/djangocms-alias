from django import template

from cms.toolbar.utils import get_toolbar_from_request
from cms.utils.urlutils import add_url_parameters, admin_reverse

from ..constants import USAGE_ALIAS_URL_NAME


register = template.Library()


@register.simple_tag(takes_context=False)
def get_alias_usage_view_url(alias, show_back_btn):
    parameters = {'back': 1} if show_back_btn else {}
    return add_url_parameters(
        admin_reverse(
            USAGE_ALIAS_URL_NAME,
            args=[alias.pk],
        ),
        **parameters,
    )


@register.simple_tag(takes_context=False)
def get_object_type(obj):
    return obj._meta.verbose_name


@register.simple_tag(takes_context=True)
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
        return content
