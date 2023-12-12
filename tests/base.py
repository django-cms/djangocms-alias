from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.http import QueryDict
from django.test.client import RequestFactory

from cms.api import add_plugin, create_page, create_page_content
from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.utils import (
    get_object_edit_url,
    get_object_preview_url,
    get_object_structure_url,
)
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse

from djangocms_alias.constants import (
    CATEGORY_LIST_URL_NAME,
    CREATE_ALIAS_URL_NAME,
    DELETE_ALIAS_URL_NAME,
    DETACH_ALIAS_PLUGIN_URL_NAME,
    LIST_ALIAS_URL_NAME,
)
from djangocms_alias.models import Alias as AliasModel, AliasContent, Category
from djangocms_alias.utils import is_versioning_enabled


class BaseAliasPluginTestCase(CMSTestCase):

    def get_create_alias_endpoint(self):
        return admin_reverse(CREATE_ALIAS_URL_NAME)

    def get_category_list_endpoint(self):
        return admin_reverse(CATEGORY_LIST_URL_NAME)

    def get_detach_alias_plugin_endpoint(self, plugin_pk):
        return admin_reverse(
            DETACH_ALIAS_PLUGIN_URL_NAME,
            args=[plugin_pk],
        )

    def get_delete_alias_endpoint(self, alias_pk):
        return admin_reverse(
            DELETE_ALIAS_URL_NAME,
            args=[alias_pk],
        )

    def get_list_alias_endpoint(self):
        return admin_reverse(LIST_ALIAS_URL_NAME)

    def setUp(self):
        self.superuser = self.get_superuser()
        self.language = 'en'
        self.page = self._create_page('test')
        self.placeholder = self.page.get_placeholders(self.language).get(
            slot='content',
        )
        self.plugin = add_plugin(
            self.placeholder,
            'TextPlugin',
            language=self.language,
            body='test',
        )
        self.category = Category.objects.create(name='test category')

    def _get_draft_page_placeholder(self):
        page_content = create_page_content(self.language, 'Draft Page', self.page, created_by=self.superuser)
        return page_content.get_placeholders().get(slot='content')

    def _create_alias(self, plugins=None, name='test alias', category=None, position=0,
                      language=None, published=True, static_code=None, site=None):
        if language is None:
            language = self.language
        if category is None:
            category = self.category
        if plugins is None:
            plugins = []
        alias = AliasModel.objects.create(
            category=category,
            position=position,
            static_code=static_code,
            site=site,
        )
        alias_content = AliasContent.objects.create(
            alias=alias,
            name=name,
            language=language,
        )

        if is_versioning_enabled():
            from djangocms_versioning.models import Version
            version = Version.objects.create(content=alias_content, created_by=self.superuser)
            if published:
                version.publish(self.superuser)

        if plugins:
            alias_content.populate(plugins=plugins)
        return alias

    def _get_version(self, grouper, version_state, language=None):
        language = language or self.language

        from djangocms_versioning.models import Version
        versions = Version.objects.filter_by_grouper(grouper).filter(state=version_state)
        for version in versions:
            if hasattr(version.content, 'language') and version.content.language == language:
                return version

    def _publish(self, grouper, language=None):
        from djangocms_versioning.constants import DRAFT
        version = self._get_version(grouper, DRAFT, language)
        version.publish(self.superuser)

    def _unpublish(self, grouper, language=None):
        from djangocms_versioning.constants import PUBLISHED
        version = self._get_version(grouper, PUBLISHED, language)
        version.unpublish(self.superuser)

    def _create_page(self, title, language=None, site=None, published=True, **kwargs):
        if language is None:
            language = self.language

        if is_versioning_enabled() and not kwargs.get('created_by'):
            kwargs['created_by'] = self.superuser

        page = create_page(
            title=title,
            language=language,
            template='page.html',
            menu_title='',
            in_navigation=True,
            limit_visibility_in_menu=None,
            site=site,
            **kwargs
        )
        if is_versioning_enabled() and published:
            self._publish(page, language)
        return page

    def get_alias_request(self, alias, lang_code='en', *args, **kwargs):
        request = self._get_instance_request(alias, *args, **kwargs)
        request.current_page = None
        request = self._process_request_by_toolbar_middleware(request, obj=alias.get_content(lang_code))
        return request

    def get_page_request(self, page, obj=None, *args, **kwargs):
        request = self._get_instance_request(page, *args, **kwargs)
        request.current_page = page
        request = self._process_request_by_toolbar_middleware(request, obj)
        return request

    def _get_instance_request(self, instance, user, path=None, edit=False,
                              preview=False, structure=False, lang_code='en',
                              disable=False):
        if not path:
            if edit:
                path = get_object_edit_url(instance)
            elif preview:
                path = get_object_preview_url(instance)
            elif structure:
                path = get_object_structure_url(instance)
            else:
                path = instance.get_absolute_url()

        request = RequestFactory().get(path)
        request.session = {}
        request.user = user
        request.LANGUAGE_CODE = lang_code
        request.GET = QueryDict('', mutable=True)
        if edit:
            request.GET['edit'] = None
        else:
            request.GET['edit_off'] = None
        if disable:
            request.GET[get_cms_setting('CMS_TOOLBAR_URL__DISABLE')] = None

        return request

    def _process_request_by_toolbar_middleware(self, request, obj=None):
        middleware = ToolbarMiddleware(request)
        middleware.process_request(request)
        if hasattr(request, 'toolbar'):
            if obj:
                request.toolbar.set_object(obj)
            request.toolbar.populate()
            request.toolbar.post_template_populate()
        return request

    def _add_default_permissions(self, user):
        # Text plugin permissions
        user.user_permissions.add(Permission.objects.get(codename='add_text'))
        user.user_permissions.add(Permission.objects.get(codename='delete_text'))
        user.user_permissions.add(Permission.objects.get(codename='change_text'))
        user.user_permissions.add(Permission.objects.get(codename='add_page'))
        user.user_permissions.add(Permission.objects.get(codename='change_page'))
        user.user_permissions.add(Permission.objects.get(codename='delete_page'))

    def add_alias_plugin_to_page(self, page, alias, language=None):
        if language is None:
            language = self.language

        add_plugin(
            page.get_placeholders(language).get(slot='content'),
            'Alias',
            language=language,
            alias=alias,
        )

    def get_staff_user_with_alias_permissions(self):
        staff_user = self._create_user("alias staff", is_staff=True, is_superuser=False)  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('add', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('change', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('delete', AliasModel._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('add', AliasContent._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('change', AliasContent._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('delete', AliasContent._meta))  # noqa: E501
        self.add_permission(staff_user, get_permission_codename('add', Category._meta))  # noqa: E501
        return staff_user
