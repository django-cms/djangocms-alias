from django.conf import settings

"""
List of settings that can be set in project django settings.
"""

ALIAS_SHOW_PREVIEW_LINK = getattr(settings, "ALIAS_SHOW_PREVIEW_LINK", False)
"""
.. _SHOW_PREVIEW_LINK:

Show a preview link towards static-alias content on static_alias-Templatetag (defaults to False).
"""
