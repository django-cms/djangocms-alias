"""Optional djangocms-rest integration for djangocms-alias.

This module is only importable when ``djangocms-rest`` is installed. It exposes
the alias content (a reusable, page-independent placeholder) through the
headless API using the cms_config contract: ``cms_config.py`` declares
``djangocms_rest_enabled`` and mounts :data:`urlpatterns` via
``cms_rest_endpoints``.

``serialize_fk`` links an ``AliasPlugin``'s ``alias`` reference to its API
endpoint via the ``Alias.get_api_endpoint`` method (defined on the model) --
the same duck-typed hook djangocms-rest uses for pages.

:class:`AliasInlineSerializer` is the plugin serializer attached to the
``Alias`` plugin (see ``cms_plugins.py``). It expands the referenced alias'
placeholder content inline so an ``AliasPlugin`` nested in a page renders its
plugin tree directly in the headless API response, guarding against recursive
aliases via a per-request stack.
"""

from typing import Any

from django.urls import path
from djangocms_rest.serializers.placeholders import PlaceholderSerializer
from djangocms_rest.serializers.plugins import GenericPluginSerializer, base_exclude
from djangocms_rest.views_base import BaseAPIView
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from .models import Alias, AliasPlugin


class AliasInlineSerializer(GenericPluginSerializer):
    """Serialize an ``AliasPlugin``, expanding the alias content inline.

    Adds a ``content`` field holding the serialized plugin tree of the
    referenced alias' placeholder (for the plugin's language). Recursive
    aliases are short-circuited with a per-request stack so an alias that
    (directly or transitively) references itself yields an empty ``content``
    instead of recursing forever.
    """

    content = serializers.SerializerMethodField()

    class Meta:
        model = AliasPlugin
        exclude = tuple(base_exclude)

    def get_content(self, instance: AliasPlugin) -> list[dict[str, Any]]:
        request = self.request
        language = getattr(instance, "language", None)
        if not request or not language:  # pragma: no cover
            return []

        alias_stack = getattr(request, "_rest_alias_stack", None)
        if alias_stack is None:
            alias_stack = []
            request._rest_alias_stack = alias_stack

        if instance.alias_id in alias_stack:
            # Recursive alias reference -- stop here.
            return []

        alias_stack.append(instance.alias_id)
        try:
            placeholder = instance.alias.get_placeholder(
                language=language,
                show_draft_content=bool(getattr(request, "_preview_mode", False)),
            )
            if placeholder is None:  # pragma: no cover
                return []

            # Imported lazily: plugin_rendering pulls in the full CMS renderer
            # stack, which we only need when actually expanding alias content.
            from djangocms_rest.plugin_rendering import RESTRenderer

            renderer = RESTRenderer(request=request)
            return renderer.serialize_plugins(
                placeholder=placeholder,
                language=language,
                context=self.context,
            )
        finally:
            alias_stack.pop()


class AliasContentView(BaseAPIView):
    """Serialize the placeholder content of an alias for a given language.

    The response shape matches djangocms-rest's placeholder endpoint: ``slot``,
    ``label``, ``language``, ``content`` (the plugin tree) and ``details``.
    Add ``?preview=true`` (admin only) to read the latest draft instead of the
    published version when versioning is enabled.
    """

    def get(self, request, language, pk):
        alias = Alias.objects.filter(pk=pk).first()
        if alias is None:
            raise NotFound()

        placeholder = alias.get_placeholder(
            language,
            show_draft_content=self._preview_requested(),
        )
        if placeholder is None:
            raise NotFound()

        serializer = PlaceholderSerializer(
            instance=placeholder,
            request=request,
            language=language,
            read_only=True,
        )
        return Response(serializer.data)


urlpatterns = [
    path(
        "<slug:language>/aliases/<int:pk>/",
        AliasContentView.as_view(),
        name="alias-detail",
    ),
]
