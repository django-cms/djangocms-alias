from django.contrib import admin

from cms.admin.placeholderadmin import PlaceholderAdminMixin

from .models import Alias, Category


__all__ = [
    'AliasAdmin',
    'AliasInlineAdmin',
    'CategoryAdmin',
]


class AliasInlineAdmin(admin.StackedInline):
    model = Alias
    fields = ('position', )
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [AliasInlineAdmin]


@admin.register(Alias)
class AliasAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    list_display = ['name']
