import uuid

from django.db import models
from django.db.models import Q
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from cms.models import (
    CMSPlugin,
    Placeholder,
)
from cms.models.fields import PlaceholderField


__all__ = [
    'Category',
    'AliasPlaceholder',
    'Alias',
    'AliasPluginModel',
]


def _get_alias_placeholder_slot(alias):
    # TODO come up with something cleverer
    if alias.pk:
        return alias.placeholder.slot
    return 'alias-{}'.format(uuid.uuid4())


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


class AliasPlaceholder(Placeholder):

    class Meta:
        proxy = True

    @cached_property
    def alias(self):
        return Alias.objects.get(placeholder=self.pk)

    def get_label(self):
        return self.alias.name


class Alias(models.Model):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=120,
    )
    placeholder = PlaceholderField(
        slotname=_get_alias_placeholder_slot,
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_('category'),
        related_name='aliases',
        on_delete=models.CASCADE,
    )
    position = models.PositiveIntegerField(
        verbose_name=_('position'),
        default=0,
    )

    class Meta:
        verbose_name = _('alias')
        verbose_name_plural = _('aliases')
        ordering = ['position']

    def __str__(self):
        return self.name

    @cached_property
    def alias_placeholder(self):
        placeholder = self.placeholder
        placeholder.__class__ = AliasPlaceholder
        return placeholder


class AliasPluginModel(CMSPlugin):
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
        return force_text(self.alias.alias_placeholder.get_label())

    def is_recursive(self):
        placeholder_id = self.alias.placeholder_id

        plugins = AliasPluginModel.objects.filter(
            plugin_type='Alias2Plugin',
            placeholder_id=placeholder_id,
        )
        plugins = plugins.filter(
            Q(pk=self) | Q(alias__placeholder=placeholder_id),
        )
        return plugins.exists()
