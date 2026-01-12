import os
from functools import cache
from typing import TYPE_CHECKING

from cms.models import Placeholder
from cms.plugin_rendering import BaseRenderer
from cms.utils.placeholder import _get_nodelist, _scan_placeholders
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import HttpRequest
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe

from djangocms_alias.templatetags.djangocms_alias_tags import StaticAlias, _static_alias_editing_enabled

from .models import Alias, AliasContent

if TYPE_CHECKING:
    from djangocms_alias.templatetags.djangocms_alias_tags import DeclaredStaticAlias


def render_alias_content(request: HttpRequest, alias_content: str) -> TemplateResponse:
    template = "djangocms_alias/alias_content_preview.html"
    context = {"alias_content": alias_content}
    return TemplateResponse(request, template, context)


def get_declared_static_aliases(template: str) -> list["DeclaredStaticAlias"]:
    """Scan a template for static_alias declarations.
    Returns a list of DeclaredStaticAlias namedtuples.
    """
    if _static_alias_editing_enabled is False:
        return []
    compiled_template = get_template(template)
    nodes = _scan_placeholders((_get_nodelist(compiled_template)), node_class=StaticAlias)
    placeholders = [node.get_declaration() for node in nodes]
    return [placeholder for placeholder in placeholders if placeholder.static_code]


if settings.DEBUG is False or "PYTEST_VERSION" in os.environ:
    # Cache in production only, so template changes in development
    # are always reflected without needing a server restart
    get_declared_static_aliases = cache(get_declared_static_aliases)


def render_alias_structure_js(context: dict, renderer: BaseRenderer, obj: models.Model) -> str:
    request = context.get("request")

    # 1. get template, bail early
    template = getattr(obj, "get_template", lambda: None)()
    if not template:
        return ""

    # 2. resolve language once
    lang = getattr(getattr(request, "toolbar", None), "request_language", None)

    # 3. scan for declarations
    declared = get_declared_static_aliases(template)
    if not declared:
        return ""

    # 4. build Q() in two grouped filters (site vs no‐site)
    site_codes = [a.static_code for a in declared if a.site]
    nosite_codes = [a.static_code for a in declared if not a.site]
    q_parts = models.Q(static_code__in=site_codes, site=renderer.current_site) if site_codes else models.Q()
    if nosite_codes:
        q_parts |= models.Q(static_code__in=nosite_codes, site__isnull=True)
    alias_qs = Alias.objects.filter(q_parts)

    # 5. fetch AliasContent PKs & map CMS Placeholder by slot
    content_ct = ContentType.objects.get_for_model(AliasContent)
    alias_pks = AliasContent.admin_manager.current_content(alias__in=alias_qs).values_list("pk", flat=True)
    placeholders = {ph.slot: ph for ph in Placeholder.objects.filter(content_type=content_ct, object_id__in=alias_pks)}

    # 6. render into JS array
    js_parts = []
    for decl in declared:
        ph = placeholders.get(decl.static_code)
        if not ph:
            continue
        ph.is_static = True
        js_parts.append(renderer.render_placeholder(ph, lang, obj))
    return "\n".join(js_parts)


def add_static_alias_js(tag):
    from cms.templatetags.cms_js_tags import register

    def extended_static_alias_js(context: dict, renderer: BaseRenderer, obj: models.Model):
        cms_js = tag(context, renderer, obj)
        alias_js = render_alias_structure_js(context, renderer, obj)
        return mark_safe(f"{cms_js}\n{alias_js}")

    return register.simple_tag(func=extended_static_alias_js, takes_context=True, name="render_cms_structure_js")
