from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from cms.toolbar.utils import get_toolbar_from_request

from ..constants import (
    DETAIL_ALIAS_URL_NAME,
    DRAFT_ALIASES_SESSION_KEY,
    LIST_CATEGORY_URL_NAME,
    PLUGIN_URL_NAME_PREFIX,
)
from ..models import Category
from ..utils import alias_plugin_reverse


register = template.Library()


@register.assignment_tag(takes_context=False)
def get_alias_categories():
    return Category.objects.order_by('name')


@register.assignment_tag(takes_context=False)
def get_alias_url(alias):
    return alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[alias.pk])


@register.inclusion_tag('djangocms_alias/alias_tag.html', takes_context=True)
def render_alias(context, instance, use_draft=None, editable=False):
    request = context['request']

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
        return {
            'content': mark_safe(content),
            'draft': draft,
        }


class Breadcrumb:

    def __init__(self, label, url):
        self.label = label
        self.url = url

    @classmethod
    def from_model_instance(cls, instance):
        return cls(instance.name, instance.get_absolute_url())


@register.inclusion_tag('djangocms_alias/breadcrumb.html', takes_context=True)
def show_alias_breadcrumb(context):
    if context['request'].toolbar.app_name != PLUGIN_URL_NAME_PREFIX:
        return {'items': []}

    items = [
        Breadcrumb(_('Categories'), alias_plugin_reverse(LIST_CATEGORY_URL_NAME)),  # noqa: E501
    ]

    obj = context.get('object', None)
    if obj:
        if hasattr(obj, 'category'):
            items.append(Breadcrumb.from_model_instance(obj.category))
        items.append(Breadcrumb.from_model_instance(obj))

    return {'items': items}
