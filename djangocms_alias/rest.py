"""Optional djangocms-rest integration for djangocms-alias.

This module is only importable when ``djangocms-rest`` is installed. It exposes
the alias content (a reusable, page-independent placeholder) through the
headless API using the cms_config contract: ``cms_config.py`` declares
``djangocms_rest_enabled`` and mounts :data:`urlpatterns` via
``cms_rest_endpoints``.

It also teaches ``serialize_fk`` how to link an ``AliasPlugin``'s ``alias``
reference to its API endpoint, by adding a ``get_api_endpoint`` method to the
``Alias`` model -- the same duck-typed hook djangocms-rest uses for pages.
"""

from django.urls import path
from djangocms_rest.serializers.placeholders import PlaceholderSerializer
from djangocms_rest.views_base import BaseAPIView
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from .models import Alias


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
