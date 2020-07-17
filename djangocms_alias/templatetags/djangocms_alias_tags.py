from collections import ChainMap

from django import template

from cms.templatetags.cms_tags import PlaceholderOptions
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils import get_current_site
from cms.utils.placeholder import validate_placeholder_name
from cms.utils.urlutils import add_url_parameters, admin_reverse

from classytags.arguments import Argument, MultiValueArgument
from classytags.core import Tag

from ..constants import DEFAULT_STATIC_ALIAS_CATEGORY_NAME, USAGE_ALIAS_URL_NAME
from ..models import Alias, Category


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
class StaticAlias(Tag):
    """
    This template node is used to render Alias contents and is designed to be a
    replacement for the CMS Static Placeholder.

    eg: {% static_alias "identifier_text" %}


    Keyword arguments:
    identifier -- the unique identifier of the Alias
    """
    name = 'static_alias'
    options = PlaceholderOptions(
        Argument('static_code', resolve=False),
        MultiValueArgument('extra_bits', required=False, resolve=False),
        blocks=[
            ('endstatic_alias', 'nodelist'),
        ],
    )

    def render_tag(self, context, static_code, extra_bits, nodelist=None):
        request = context.get('request')

        if not static_code or not request:
            # an empty string was passed in or the variable is not available in the context
            if nodelist:
                return nodelist.render(context)
            return ''

        validate_placeholder_name(static_code)

        toolbar = get_toolbar_from_request(request)
        renderer = toolbar.get_content_renderer()

        # Try and find an Alias to render or fall back to nothing.
        # FIXME: Could have the same code for site bound and project wide?
        alias_instance = Alias.objects.filter(static_code=static_code).first()
        if not alias_instance:

            # FIXME: Get default language
            # Parlers get_or_create doesn't work well with the translations
            default_category = Category.objects.filter(translations__name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME).first()
            if not default_category:
                default_category = Category.objects.create(name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)

            alias_instance = Alias.objects.create(category=default_category, static_code=static_code)

        kwargs = {
            'static_code': static_code,
            # 'defaults': {'creation_method': StaticPlaceholder.CREATION_BY_TEMPLATE}
        }
        # Site
        if 'site' in extra_bits:
            kwargs['site'] = get_current_site()
        else:
            kwargs['site_id__isnull'] = True

        source = alias_instance.get_placeholder()

        if source:
            content = renderer.render_placeholder(
                placeholder=source,
                context=context,
                nodelist=nodelist,
            )
            return content

        return ''
