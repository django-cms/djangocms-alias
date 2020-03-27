from collections import ChainMap

from django import template

from cms.templatetags.cms_tags import PlaceholderOptions
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils.placeholder import validate_placeholder_name
from cms.utils.urlutils import add_url_parameters, admin_reverse

from classytags.arguments import (
    Argument,
    MultiValueArgument,
    MultiKeywordArgument,
)
from classytags.core import Options, Tag

from ..constants import USAGE_ALIAS_URL_NAME
from ..models import Alias


register = template.Library()


@register.simple_tag(takes_context=False)
def get_alias_usage_view_url(alias, **kwargs):
    url = admin_reverse(USAGE_ALIAS_URL_NAME, args=[alias.pk])
    return add_url_parameters(url, **ChainMap(kwargs))


@register.filter()
def verbose_name(obj):
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
        return content or ''
    return ''


@register.tag
class AliasPlaceholder(Tag):
    """
    This template node is used to render Alias contents and is designed to be a
    replacement for the CMS Static Placeholder.

    eg: {% alias_placeholder "identifier_text" %}


    Keyword arguments:
    identifier -- the unique identifier of the Alias
    """
    name = 'alias_placeholder'
    options = PlaceholderOptions(
        Argument('identifier', resolve=False),
        MultiValueArgument('extra_bits', required=False, resolve=False),
        blocks=[
            ('endalias_placeholder', 'nodelist'),
        ],
    )

    def render_tag(self, context, identifier, extra_bits, nodelist=None):
        request = context.get('request')

        validate_placeholder_name(identifier)

        toolbar = get_toolbar_from_request(request)
        renderer = toolbar.get_content_renderer()

        # TODO: Show draft content?

        # Try and find an Alias to render or fall back to nothing.
        alias_instance = Alias.objects.filter(identifier=identifier)
        if not alias_instance.count():
            if nodelist:
                return nodelist.render(context)
            return ''


        alias_instance = alias_instance.first()
        source = alias_instance.get_placeholder()

        if source:
            content = renderer.render_placeholder(
                placeholder=source,
                context=context,
                nodelist=nodelist,
            )
            return content

        return ''
