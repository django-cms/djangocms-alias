from django.contrib import admin

from cms.admin.placeholderadmin import PlaceholderAdminMixin
from cms.utils.permissions import get_model_permission_codename

from .models import Alias, AliasPlugin, Category
from .urls import urlpatterns


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

    def get_urls(self):
        return urlpatterns + super().get_urls()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Alias can be deleted by users who can add aliases,
        # if that alias is not referenced anywhere.
        if obj and not obj.is_in_use:
            return request.user.has_perm(
                get_model_permission_codename(self.model, 'add'),
            )
        return super().has_delete_permission(request, obj)
