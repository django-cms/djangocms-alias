from cms.models import Placeholder
from cms.plugin_rendering import BaseRenderer
from cms.utils.placeholder import _get_nodelist, _scan_placeholders
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import HttpRequest
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe

from djangocms_alias.templatetags.djangocms_alias_tags import StaticAlias

from .models import Alias, AliasContent


def render_alias_content(request: HttpRequest, alias_content: str) -> TemplateResponse:
    template = "djangocms_alias/alias_content_preview.html"
    context = {"alias_content": alias_content}
    return TemplateResponse(request, template, context)


def get_declared_static_aliases(template: str, context: dict) -> list:
    compiled_template = get_template(template)
    nodes = _scan_placeholders((_get_nodelist(compiled_template)), node_class=StaticAlias)
    placeholders = [node.get_declaration() for node in nodes]
    return [placeholder for placeholder in placeholders if placeholder.static_code]


def render_alias_structure_js(context: dict, renderer: BaseRenderer, obj: models.Model) -> str:
    try:
        template = obj.get_template()
    except AttributeError:
        template = None

    if not template:
        # No template - no static alias declarations
        return ""

    try:
        lang = context["request"].toolbar.request_language
    except AttributeError:
        lang = None

    declared_static_aliases = get_declared_static_aliases(template, context)

    alias_selector = models.Q()
    for static_alias in declared_static_aliases:
        kwargs = {
            "static_code": static_alias.static_code,
        }
        if static_alias.site:
            kwargs["site"] = renderer.current_site
        else:
            kwargs["site_id__isnull"] = True
        alias_selector |= models.Q(**kwargs)

    alias_qs = Alias.objects.filter(alias_selector)
    alias_contents_qs = AliasContent.admin_manager.current_content(alias__in=alias_qs).values_list("pk")
    placeholders = {
        placeholder.slot: placeholder
        for placeholder in Placeholder.objects.filter(
            content_type=ContentType.objects.get_for_model(AliasContent), object_id__in=alias_contents_qs
        )
    }

    alias_js = []
    for static_alias in declared_static_aliases:
        placeholder = placeholders.get(static_alias.static_code)
        placeholder.is_static = True
        placeholder.is_editable = placeholder.check_source(context["request"].user)
        if placeholder:
            alias_js.append(renderer.render_placeholder(placeholder, language=lang, page=obj))

    return "\n".join(alias_js)


def add_static_alias_js(tag):
    from cms.templatetags.cms_js_tags import register

    def extended_static_alias_js(context: dict, renderer: BaseRenderer, obj: models.Model):
        cms_js = tag(context, renderer, obj)
        alias_js = render_alias_structure_js(context, renderer, obj)
        return mark_safe(f"{cms_js}\n{alias_js}")

    return register.simple_tag(func=extended_static_alias_js, takes_context=True, name="render_cms_structure_js")
