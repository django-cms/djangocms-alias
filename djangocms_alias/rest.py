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

from cms.utils.permissions import get_model_permission_codename
from django.db.models import Q
from django.urls import path
from djangocms_rest.permissions import IsAllowedLanguage, IsAllowedPublicLanguage
from djangocms_rest.serializers.placeholders import PlaceholderSerializer
from djangocms_rest.serializers.plugins import GenericPluginSerializer, base_exclude
from djangocms_rest.views_base import BaseAPIView
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
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


class CanViewAlias(IsAllowedLanguage):
    """Object-level permission for the alias content endpoint.

    Published alias content is public -- it is editorial content embedded in
    public pages, so anyone who may read the page may read the alias. Draft
    content (``?preview=true``) is only served to users who hold the django
    ``view`` permission on :class:`Alias`.
    """

    def has_object_permission(self, request: Request, view: BaseAPIView, obj: Alias) -> bool:
        if not isinstance(obj, Alias):
            return False
        if not super().has_permission(request, view):
            raise NotFound()
        if view._preview_requested():
            return request.user.has_perm(
                get_model_permission_codename(Alias, "view"),
            )
        return True


class AliasContentView(BaseAPIView):
    """Serialize the placeholder content of an alias for a given language.

    The alias is addressed either by primary key (``/en/aliases/42/``) or, for
    static aliases, by its static code (``/en/aliases/footer/``) -- the same
    identifier templates use with ``{% static_alias "footer" %}``.

    The response shape matches djangocms-rest's placeholder endpoint: ``slot``,
    ``label``, ``language``, ``content`` (the plugin tree) and ``details``.
    Add ``?preview=true`` (admin only) to read the latest draft instead of the
    published version when versioning is enabled.
    """

    permission_classes = [IsAllowedPublicLanguage, CanViewAlias]
    serializer_class = PlaceholderSerializer

    def get_alias(self, pk: int | None = None, static_code: str | None = None) -> Alias | None:
        """Resolve the alias by primary key or by static code.

        Static codes are unique per site, and an alias without a site acts as
        the fallback for every site -- so a site-specific alias takes
        precedence over the site-less one, mirroring what the ``static_alias``
        template tag renders.
        """
        if pk is not None:
            return Alias.objects.filter(pk=pk).first()

        candidates = Alias.objects.filter(
            Q(site=self.site) | Q(site__isnull=True),
            static_code=static_code,
        )
        return next(
            (alias for alias in candidates if alias.site_id == self.site.pk),
            None,
        ) or next(iter(candidates), None)

    def get(self, request, language, pk=None, static_code=None):
        alias = self.get_alias(pk=pk, static_code=static_code)
        if alias is None:
            raise NotFound()

        self.check_object_permissions(request, alias)

        placeholder = alias.get_placeholder(
            language,
            show_draft_content=self._preview_requested(),
        )
        if placeholder is None:
            raise NotFound()

        serializer = self.serializer_class(
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
    # Registered after the pk route, so a purely numeric static code is not
    # reachable by code -- static codes are template identifiers, not numbers.
    path(
        "<slug:language>/aliases/<str:static_code>/",
        AliasContentView.as_view(),
        name="alias-static-detail",
    ),
]
