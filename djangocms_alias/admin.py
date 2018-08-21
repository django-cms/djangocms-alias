from django.contrib import admin

from cms.admin.placeholderadmin import PlaceholderAdminMixin
from cms.utils.permissions import get_model_permission_codename

from parler.admin import TranslatableAdmin

from .forms import AliasContentForm, AliasForm
from .models import Alias, AliasContent, Category
from .urls import urlpatterns


__all__ = [
    'AliasAdmin',
    'CategoryAdmin',
]


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['name']


@admin.register(Alias)
class AliasAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'category']
    form = AliasForm

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


@admin.register(AliasContent)
class AliasContentAdmin(admin.ModelAdmin):
    form = AliasContentForm
