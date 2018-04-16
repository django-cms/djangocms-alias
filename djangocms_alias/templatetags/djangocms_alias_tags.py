from django import template
from django.utils.safestring import mark_safe

from cms.toolbar.utils import get_toolbar_from_request

from ..constants import DETAIL_ALIAS_URL_NAME
from ..models import Category
from ..utils import alias_plugin_reverse


register = template.Library()


@register.assignment_tag(takes_context=False)
def get_alias_categories():
    return Category.objects.order_by('name')


@register.assignment_tag(takes_context=False)
def get_alias_url(alias):
    return alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk])


@register.simple_tag(takes_context=True)
def render_alias_plugin(context, instance, draft=False):
    if not instance:
        return ''
    return render_alias(context, instance.alias, draft)


@register.simple_tag(takes_context=True)
def render_alias(context, instance, draft=False):
    request = context['request']
    toolbar = get_toolbar_from_request(request)
    renderer = toolbar.content_renderer

    if not instance:
        return ''

    if draft:
        source = instance.draft_content
    else:
        source = instance.live_content

    # TODO This needs to be using draft/live alias feature
    can_see_content = True

    if can_see_content and source:
        content = renderer.render_placeholder(
            placeholder=source,
            context=context,
            editable=False,
        )
        return mark_safe(content)
    return ''
