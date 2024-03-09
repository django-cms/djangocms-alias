from django.template.response import TemplateResponse


def render_alias_content(request, alias_content):
    template = "djangocms_alias/alias_content_preview.html"
    context = {"alias_content": alias_content}
    return TemplateResponse(request, template, context)
