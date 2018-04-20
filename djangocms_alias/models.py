from django.db import models, transaction
from django.db.models import Q
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin, Placeholder
from cms.models.fields import PlaceholderField
from cms.utils.plugins import copy_plugins_to_placeholder

from .constants import DETAIL_ALIAS_URL_NAME, LIST_ALIASES_URL_NAME
from .utils import alias_plugin_reverse


__all__ = [
    'Category',
    'AliasPlaceholder',
    'Alias',
    'AliasPlugin',
]


def _get_alias_placeholder_slot(alias):
    return slugify(alias.name)


class Category(models.Model):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=120,
        unique=True,
    )

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return alias_plugin_reverse(LIST_ALIASES_URL_NAME, args=[self.pk])


class AliasPlaceholder(Placeholder):

    class Meta:
        proxy = True

    @cached_property
    def alias(self):
        return Alias.objects.get(
            Q(draft_content=self.pk) | Q(live_content=self.pk),
        )

    def get_label(self):
        return self.alias.name


class Alias(models.Model):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=120,
    )
    draft_content = PlaceholderField(
        slotname=_get_alias_placeholder_slot,
        related_name='alias_draft',
    )
    live_content = PlaceholderField(
        slotname=_get_alias_placeholder_slot,
        related_name='live_draft',
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

    class Meta:
        verbose_name = _('alias')
        verbose_name_plural = _('aliases')
        ordering = ['position']
        unique_together = [
            ('name', 'category'),
        ]

    def __str__(self):
        return self.name

    @cached_property
    def draft_placeholder(self):
        placeholder = self.draft_content
        placeholder.__class__ = AliasPlaceholder
        return placeholder

    @cached_property
    def live_placeholder(self):
        placeholder = self.live_content
        placeholder.__class__ = AliasPlaceholder
        return placeholder

    @cached_property
    def is_in_use(self):
        return self.cms_plugins.exists()

    @cached_property
    def pages_using_this_alias(self):
        # TODO: list of pages model objects (?) then in template you can show
        # name and link to it
        # TODO handle nested aliases and overall nested plugins
        # TODO handle also public/draft of pages (show indicator), alias can be
        # used in live version but not in draft (was detached)
        return []

    def get_absolute_url(self):
        return alias_plugin_reverse(DETAIL_ALIAS_URL_NAME, args=[self.pk])

    def publish(self, language):
        self.live_content.clear(language=language)
        copy_plugins_to_placeholder(
            self.draft_content.get_plugins(language=language),
            placeholder=self.live_content,
        )

    @transaction.atomic
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # deletion of placeholders and all cms_plugins in it
        self.draft_content.delete()
        self.live_content.delete()


class AliasPlugin(CMSPlugin):
    alias = models.ForeignKey(
        Alias,
        verbose_name=_('alias'),
        related_name='cms_plugins',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('alias plugin model')
        verbose_name_plural = _('alias plugin models')

    def __str__(self):
        return force_text(self.alias.name)

    def is_recursive(self):
        draft_content_id = self.alias.draft_content_id

        plugins = AliasPlugin.objects.filter(
            placeholder_id=draft_content_id,
        )
        plugins = plugins.filter(
            Q(pk=self) | Q(alias__draft_content=draft_content_id),
        )
        return plugins.exists()
