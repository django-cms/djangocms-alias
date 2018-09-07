from django.template.response import TemplateResponse


def render_alias_content(request, alias_content):
    template = 'djangocms_alias/alias_detail.html'
    context = {
        'alias': alias_content.alias,
    }
    return TemplateResponse(request, template, context)
