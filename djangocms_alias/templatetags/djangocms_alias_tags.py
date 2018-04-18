from django import template
from django.utils.safestring import mark_safe

from cms.toolbar.utils import get_toolbar_from_request

from ..constants import DETAIL_ALIAS_URL_NAME, DRAFT_ALIASES_SESSION_KEY
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
def render_alias(context, instance, use_draft=None, editable=False):
    request = context['request']
    if request is None:
        return ''

    toolbar = get_toolbar_from_request(request)
    renderer = toolbar.get_content_renderer()

    editable = editable and renderer._placeholders_are_editable

    if use_draft is None:
        draft = request.session.get(DRAFT_ALIASES_SESSION_KEY)
    else:
        draft = use_draft

    if draft:
        source = instance.draft_placeholder
    else:
        source = instance.live_placeholder

    # TODO This needs to be using draft/live alias feature
    can_see_content = True

    if can_see_content and source:
        content = renderer.render_placeholder(
            placeholder=source,
            context=context,
            editable=editable,
        )
        return mark_safe(content)
    return ''
