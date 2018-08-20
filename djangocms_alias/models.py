import operator

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Q
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from cms.api import add_plugin
from cms.models import CMSPlugin
from cms.models.fields import PlaceholderField
from cms.utils.i18n import get_current_language
from cms.utils.plugins import copy_plugins_to_placeholder

from parler.models import TranslatableModel, TranslatedFields

from .compat import CMS_36
from .constants import DETAIL_ALIAS_URL_NAME, LIST_ALIASES_URL_NAME
from .utils import alias_plugin_reverse


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


def _get_alias_placeholder_slot(alias):
    return slugify(alias.name)


class Category(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(
            verbose_name=_('name'),
            max_length=120,
            unique=True,
        ),
    )

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return alias_plugin_reverse(LIST_ALIASES_URL_NAME, args=[self.pk])


class AliasQuerySet(models.QuerySet):

    def current_language(self):
        return self.filter(
            contents__language=get_current_language(),
        )


class Alias(models.Model):
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

    objects = AliasQuerySet.as_manager()

    class Meta:
        verbose_name = _('alias')
        verbose_name_plural = _('aliases')
        ordering = ['position']

    def __init__(self, *args, **kwargs):
        self._plugins_cache = {}
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
    def pages_using_this_alias(self):
        pages = set()
        alias_plugins = self.cms_plugins.prefetch_related('placeholder__page_set')
        for plugin in alias_plugins:
            page_set = plugin.placeholder.page_set.all()
            if page_set:
                pages.update(page_set)
            else:
                pages.update(plugin.placeholder.alias_contents.first().alias.pages_using_this_alias)
        return list(pages)

    def get_name(self, language=None):
        return getattr(self.get_content(language), 'name', '')

    def get_absolute_url(self):
        return alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[self.pk])

    def get_content(self, language=None):
        if not language:
            language = get_current_language()

        if not hasattr(self, '_content_cache'):
            self._content_cache = {}
        try:
            return self._content_cache[language]
        except KeyError:
            self._content_cache[language] = self.contents.select_related(
                'alias__category',
                'placeholder',
            ).filter(language=language).first()
            return self._content_cache[language]

    def get_placeholder(self, language=None):
        return getattr(self.get_content(language), 'placeholder', None)

    def get_plugins(self, language):
        try:
            return self._plugins_cache[language]
        except KeyError:
            placeholder = self.get_placeholder(language)
            self._plugins_cache[language] = placeholder.get_plugins_list()
            return self._plugins_cache[language]

    def get_languages(self):
        if not hasattr(self, '_content_languages_cache'):
            self._content_languages_cache = self.contents.values_list('language', flat=True)
        return self._content_languages_cache

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
    placeholder = PlaceholderField(
        slotname=_get_alias_placeholder_slot,
        related_name='alias_contents',
    )
    language = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
        default=get_current_language,
    )

    class Meta:
        verbose_name = _('alias content')
        verbose_name_plural = _('alias contents')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[self.alias_id])

    def get_template(self):
        return 'djangocms_alias/alias_detail.html'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.placeholder.source = self
        self.placeholder.save(update_fields=['object_id', 'content_type'])

    @transaction.atomic
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.alias.cms_plugins.filter(language=self.language).delete()
        self.placeholder.delete()

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
            if CMS_36:
                plugins = replaced_plugin.get_tree(replaced_plugin)
            else:
                plugins = CMSPlugin.objects.filter(
                    id__in=[replaced_plugin.pk] + replaced_plugin._get_descendants_ids(),
                )
            placeholder = replaced_plugin.placeholder
            add_plugin_kwargs = {'position': 'left', 'target': replaced_plugin}

        if CMS_36:
            plugins.update(placeholder=self.placeholder, language=self.language)
        else:
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
        return force_text(self.alias.name)

    def is_recursive(self, language=None):
        placeholder = self.alias.get_placeholder(language)

        plugins = AliasPlugin.objects.filter(
            placeholder_id=placeholder,
        )
        plugins = plugins.filter(
            Q(pk=self) | Q(alias__contents__placeholder=placeholder),
        )
        return plugins.exists()
