from distutils.version import LooseVersion

import cms
from cms.utils.conf import get_cms_setting
from cms.wizards.wizard_base import Wizard


CMS_VERSION = cms.__version__
CMS_36 = LooseVersion(CMS_VERSION) < LooseVersion('3.7')


try:
    from cms.utils.plugins import reorder_plugins
except ImportError:
    reorder_plugins = None


def get_page_placeholders(page, language=None):
    try:
        # cms3.6 compat
        return page.get_placeholders()
    except TypeError:
        return page.get_placeholders(language)


class CompatWizard(Wizard):

    def __init__(self, *args, **kwargs):
        if not CMS_36:
            # cms40 doesn't support this argument
            kwargs.pop('edit_mode_on_success', None)
        super().__init__(*args, **kwargs)


def get_wizard_entires():
    try:
        from cms.wizards.helpers import get_entries
        return get_entries()
    except ImportError:
        from cms.wizards.wizard_pool import wizard_pool
        return wizard_pool.get_entries()


def _get_object_url_for_cms40(func, instance, language=None):
    from cms.models import Page
    from djangocms_alias.models import Alias
    if isinstance(instance, Alias):
        instance = instance.get_content(language=language)
    elif isinstance(instance, Page):
        instance = instance.get_title_obj(language=language, fallback=False)

    if instance:
        return func(instance, language)
    return None


def get_object_edit_url(instance, language=None):
    if CMS_36:
        return instance.get_absolute_url() + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
    return _get_object_url_for_cms40(
        cms.toolbar.utils.get_object_edit_url,
        instance,
        language,
    )


def get_object_preview_url(instance, language=None):
    if CMS_36:
        return instance.get_absolute_url() + '?preview'
    return _get_object_url_for_cms40(
        cms.toolbar.utils.get_object_preview_url,
        instance,
        language,
    )


def get_object_structure_url(instance, language=None):
    if CMS_36:
        return instance.get_absolute_url() + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__BUILD')
    return _get_object_url_for_cms40(
        cms.toolbar.utils.get_object_structure_url,
        instance,
        language,
    )
