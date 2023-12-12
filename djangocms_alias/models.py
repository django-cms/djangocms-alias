import operator
from collections import defaultdict

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models, transaction
from django.db.models import F, Q
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.translation import get_language, gettext_lazy as _

from cms.api import add_plugin
from cms.models import CMSPlugin, Placeholder
from cms.models.fields import PlaceholderRelationField
from cms.models.managers import WithUserMixin
from cms.toolbar.utils import get_object_preview_url
from cms.utils.plugins import copy_plugins_to_placeholder
from cms.utils.urlutils import admin_reverse

from parler.models import TranslatableModel, TranslatedFields

from .constants import CHANGE_CATEGORY_URL_NAME
from .utils import is_versioning_enabled


__all__ = [
    'Category',
    'Alias',
    'AliasContent',
    'AliasPlugin',
]


# Add additional choices through the ``settings.py``.
TEMPLATE_DEFAULT = 'default'


def get_templates():
    choices = [
        (TEMPLATE_DEFAULT, _('Default')),
    ]
    choices += getattr(
        settings,
        'DJANGOCMS_ALIAS_TEMPLATES',
        [],
    )
    return choices


class Category(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(
            verbose_name=_('name'),
            max_length=120,
        ),
        meta={'unique_together': [('name', 'language_code')]},
    )

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        # Be sure to be able to see the category name even if it's not in the current language
        return self.safe_translation_getter("name", any_language=True)

    def get_absolute_url(self):
        """Builds the url to the admin category change view"""
        return admin_reverse(CHANGE_CATEGORY_URL_NAME, args=[self.pk])


class Alias(models.Model):
    CREATION_BY_TEMPLATE = 'template'
    CREATION_BY_CODE = 'code'
    CREATION_METHODS = (
        (CREATION_BY_TEMPLATE, _('by template')),
        (CREATION_BY_CODE, _('by code')),
    )
    creation_method = models.CharField(
        verbose_name=_('creation_method'), choices=CREATION_METHODS,
        default=CREATION_BY_CODE, max_length=20, blank=True,
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_('category'),
        related_name='aliases',
        on_delete=models.PROTECT,
    )
    position = models.PositiveIntegerField(
        verbose_name=_('position'),
        default=0,
    )
    static_code = models.CharField(
        verbose_name=_('static code'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('To render the alias in templates.')
    )
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = _('alias')
        verbose_name_plural = _('aliases')
        ordering = ['position']
        unique_together = (('static_code', 'site'),)  # Only restrict instances that have a site specified

    def __init__(self, *args, **kwargs):
        self._plugins_cache = {}
        self._content_cache = {}
        self._content_languages_cache = []
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name

    @cached_property
    def name(self):
        """Show alias name for current language"""
        return self.get_name() or ''

    @cached_property
    def is_in_use(self):
        return self.cms_plugins.exists()

    @cached_property
    def objects_using(self):
        objects = set()
        object_ids = defaultdict(set)
        plugins = self.cms_plugins.select_related('placeholder').prefetch_related('placeholder__source')
        for plugin in plugins:
            obj = plugin.placeholder.source
            obj_class_name = obj.__class__.__name__
            if obj_class_name.endswith('Content'):
                attr_name = obj_class_name.replace('Content', '').lower()
                attr_related_model = obj._meta.get_field(attr_name).related_model
                id_attr = getattr(obj, f'{attr_name}_id')
                if id_attr:
                    object_ids[attr_related_model].update([id_attr])
                else:
                    objects.update([obj])
            else:
                objects.update([obj])
        objects.update([
            obj
            for model_class, ids in object_ids.items()
            for obj in model_class.objects.filter(pk__in=ids)
        ])
        return list(objects)

    def get_name(self, language=None):
        content = self.get_content(language, show_draft_content=True)
        name = getattr(content, 'name', f'Alias {self.pk} (No content)')
        if is_versioning_enabled() and content:
            from djangocms_versioning.constants import DRAFT
            version = content.versions.first()

            if version.state == DRAFT:
                return f'{name} (Not published)'

        return name

    def get_absolute_url(self, language=None):
        if is_versioning_enabled():
            from djangocms_versioning.helpers import (
                version_list_url_for_grouper,
            )

            return version_list_url_for_grouper(self)
        content = self.get_content(language=language)
        if content:
            return content.get_absolute_url()

    def get_content(self, language=None, show_draft_content=False):
        if not language:
            language = get_language()

        try:
            return self._content_cache[language]
        except KeyError:
            if show_draft_content and is_versioning_enabled():
                qs = self.contents(manager="admin_manager").latest_content()
            else:
                qs = self.contents.all()
            qs = qs.select_related(
                'alias__category',
            ).prefetch_related(
                'placeholders'
            ).filter(language=language)

            self._content_cache[language] = qs.first()
            return self._content_cache[language]

    def get_placeholder(self, language=None, show_draft_content=False):
        content = self.get_content(language=language, show_draft_content=show_draft_content)
        return getattr(content, 'placeholder', None)

    def get_plugins(self, language=None):
        if not language:
            language = get_language()
        try:
            return self._plugins_cache[language]
        except KeyError:
            placeholder = self.get_placeholder(language)
            plugins = placeholder.get_plugins_list() if placeholder else []
            self._plugins_cache[language] = plugins
            return self._plugins_cache[language]

    def get_languages(self):
        if not self._content_languages_cache:
            queryset = self.contents(manager="admin_manager").current_content()
            self._content_languages_cache = queryset.values_list('language', flat=True)
        return self._content_languages_cache

    def clear_cache(self):
        self._plugins_cache = {}
        self._content_cache = {}
        self._content_languages_cache = []

    @transaction.atomic
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.category.aliases.filter(position__gt=self.position).update(
            position=F('position') - 1,
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.position = self.category.aliases.count()
        return super().save(*args, **kwargs)

    def _set_position(self, position):
        previous_position = self.position

        if previous_position > position:  # moving up
            op = operator.add
            position_range = (position, previous_position)
        else:  # moving down
            op = operator.sub
            position_range = (previous_position, position)

        filters = [
            ~Q(pk=self.pk),
            Q(position__range=position_range),
        ]

        self.position = position
        self.save()
        self.category.aliases.filter(*filters).update(position=op(F('position'), 1))  # noqa: E501


class AliasContentManager(WithUserMixin, models.Manager):
    """Adds with_user syntax to AliasContent w/o using versioning"""
    pass


class AliasContent(models.Model):
    alias = models.ForeignKey(
        Alias,
        on_delete=models.CASCADE,
        related_name='contents',
    )
    name = models.CharField(
        verbose_name=_('name'),
        max_length=120,
    )
    placeholders = PlaceholderRelationField()
    placeholder_slotname = 'content'
    language = models.CharField(
        max_length=10,
        default=get_language,
    )

    objects = AliasContentManager()

    class Meta:
        verbose_name = _('alias content')
        verbose_name_plural = _('alias contents')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field('language').choices = settings.LANGUAGES

    def __str__(self):
        return f'{self.name} ({self.language})'

    @cached_property
    def placeholder(self):
        try:
            return self.placeholders.get(slot=self.placeholder_slotname)
        except Placeholder.DoesNotExist:
            from cms.utils.placeholder import rescan_placeholders_for_obj
            rescan_placeholders_for_obj(self)
            return self.placeholders.get(slot=self.placeholder_slotname)

    def get_placeholders(self):
        return [self.placeholder]

    def get_absolute_url(self):
        return get_object_preview_url(self)

    def get_template(self):
        return 'djangocms_alias/alias_content.html'

    @transaction.atomic
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.alias.cms_plugins.filter(language=self.language).delete()

    @transaction.atomic
    def populate(self, replaced_placeholder=None, replaced_plugin=None, plugins=None):
        if not replaced_placeholder and not replaced_plugin:
            copy_plugins_to_placeholder(
                plugins,
                placeholder=self.placeholder,
            )
            return

        if replaced_placeholder:
            plugins = replaced_placeholder.get_plugins(self.language)
            placeholder = replaced_placeholder
            add_plugin_kwargs = {}
        else:
            plugins = CMSPlugin.objects.filter(
                id__in=[replaced_plugin.pk] + replaced_plugin._get_descendants_ids(),
            )
            placeholder = replaced_plugin.placeholder
            add_plugin_kwargs = {'position': 'left', 'target': replaced_plugin}

        copy_plugins_to_placeholder(
            plugins,
            placeholder=self.placeholder,
            language=self.language,
        )
        plugins.delete()
        placeholder._recalculate_plugin_positions(self.language)

        new_plugin = add_plugin(
            placeholder,
            plugin_type='Alias',
            language=self.language,
            alias=self.alias,
            **add_plugin_kwargs
        )
        if replaced_plugin:
            new_plugin.position = replaced_plugin.position
            new_plugin.save(update_fields=['position'])
        return new_plugin


def copy_alias_content(original_content):
    """Copy the AliasContent object and deepcopy its
    placeholders and plugins

    This is needed for versioning integration.
    """
    # Copy content object
    content_fields = {
        field.name: getattr(original_content, field.name)
        for field in AliasContent._meta.fields
        # don't copy primary key because we're creating a new obj
        if AliasContent._meta.pk.name != field.name
    }
    new_content = AliasContent.objects.create(**content_fields)

    # Copy placeholders
    new_placeholders = []
    for placeholder in original_content.placeholders.all():
        placeholder_fields = {
            field.name: getattr(placeholder, field.name)
            for field in Placeholder._meta.fields
            # don't copy primary key because we're creating a new obj
            # and handle the source field later
            if field.name not in [Placeholder._meta.pk.name, 'source']
        }
        if placeholder.source:
            placeholder_fields['source'] = new_content
        new_placeholder = Placeholder.objects.create(**placeholder_fields)
        # Copy plugins
        placeholder.copy_plugins(new_placeholder)
        new_placeholders.append(new_placeholder)
    new_content.placeholders.add(*new_placeholders)

    return new_content


class AliasPlugin(CMSPlugin):
    alias = models.ForeignKey(
        Alias,
        verbose_name=_('alias'),
        related_name='cms_plugins',
        on_delete=models.CASCADE,
    )
    template = models.CharField(
        verbose_name=_('template'),
        choices=get_templates(),
        default=TEMPLATE_DEFAULT,
        max_length=255,
    )

    class Meta:
        verbose_name = _('alias plugin model')
        verbose_name_plural = _('alias plugin models')

    def __str__(self):
        return force_str(self.alias.name)

    def is_recursive(self, language=None):
        # When versioning is enabled it will only get published content
        # placeholder. If does not exist, then None.
        placeholder = self.alias.get_placeholder(language)

        plugins = AliasPlugin.objects.filter(
            placeholder_id=placeholder,
        )
        plugins = plugins.filter(
            Q(pk=self) | Q(alias__contents__placeholders=placeholder)
        )
        return plugins.exists()
