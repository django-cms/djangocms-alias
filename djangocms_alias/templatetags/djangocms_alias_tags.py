from collections import ChainMap

from django import template

from cms.templatetags.cms_tags import PlaceholderOptions
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils import get_current_site, get_language_from_request
from cms.utils.i18n import get_default_language_for_site
from cms.utils.placeholder import validate_placeholder_name
from cms.utils.urlutils import add_url_parameters, admin_reverse

from classytags.arguments import Argument, MultiValueArgument
from classytags.core import Tag

from ..constants import (
    DEFAULT_STATIC_ALIAS_CATEGORY_NAME,
    USAGE_ALIAS_URL_NAME,
)
from ..models import Alias, AliasContent, Category
from ..utils import is_versioning_enabled


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

    # Get draft contents in edit or preview mode?
    get_draft_content = False
    if toolbar.edit_mode_active or toolbar.preview_mode_active:
        get_draft_content = True

    editable = editable and renderer._placeholders_are_editable
    source = instance.get_placeholder()

    if source:
        content = renderer.render_placeholder(
            placeholder=source,
            context=context,
            editable=editable,
            use_cache=not get_draft_content,
        )
        return content or ''
    return ''


@register.tag
class StaticAlias(Tag):
    """
    This template node is used to render Alias contents and is designed to be a
    replacement for the CMS Static Placeholder.

    eg: {% static_alias "identifier_text" %}
    eg: {% static_alias "identifier_text" site %}

    Keyword arguments:
    static_code -- the unique identifier of the Alias
    site -- If site is supplied an Alias instance will be created per site.
    """
    name = 'static_alias'
    options = PlaceholderOptions(
        Argument('static_code', resolve=False),
        MultiValueArgument('extra_bits', required=False, resolve=False),
        blocks=[
            ('endstatic_alias', 'nodelist'),
        ],
    )

    def _get_alias(self, request, static_code, extra_bits):
        alias_filter_kwargs = {
            'static_code': static_code,
        }
        # Site
        current_site = get_current_site()
        if 'site' in extra_bits:
            alias_filter_kwargs['site'] = current_site
        else:
            alias_filter_kwargs['site_id__isnull'] = True

        # Try and find an Alias to render
        alias = Alias.objects.filter(**alias_filter_kwargs).first()
        # If there is no alias found we need to create one
        if not alias:

            # If versioning is enabled we can only create the records with a logged in user / staff member
            if is_versioning_enabled() and not request.user.is_authenticated:
                return None

            language = get_default_language_for_site(current_site)
            # Parlers get_or_create doesn't work well with translations, so we must perform our own get or create
            default_category = Category.objects.filter(translations__name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME).first()
            if not default_category:
                default_category = Category.objects.create(name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)

            alias_creation_kwargs = {
                'static_code': static_code,
                'creation_method': Alias.CREATION_BY_TEMPLATE
            }
            # Site
            if 'site' in extra_bits:
                alias_creation_kwargs['site'] = current_site

            alias = Alias.objects.create(category=default_category, **alias_creation_kwargs)
            alias_content = AliasContent.objects.create(
                alias=alias,
                name=static_code,
                language=language,
            )

            if is_versioning_enabled():
                from djangocms_versioning.models import Version

                Version.objects.create(content=alias_content, created_by=request.user)

        return alias

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
        alias = self._get_alias(request, static_code, extra_bits)

        if not alias:
            return ''

        # Get draft contents in edit or preview mode?
        get_draft_content = False
        if toolbar.edit_mode_active or toolbar.preview_mode_active:
            get_draft_content = True

        language = get_language_from_request(request)
        placeholder = alias.get_placeholder(language=language, show_draft_content=get_draft_content)

        if placeholder:
            content = renderer.render_placeholder(
                placeholder=placeholder,
                context=context,
                nodelist=nodelist,
                use_cache=not get_draft_content,
            )
            return content
        return ''
