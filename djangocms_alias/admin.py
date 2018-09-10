from django.contrib import admin

from cms.utils.permissions import get_model_permission_codename

from parler.admin import TranslatableAdmin

from .forms import AliasContentForm
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
class AliasAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    fields = ('category',)

    def get_urls(self):
        return urlpatterns + super().get_urls()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Alias can be deleted by users who can add aliases,
        # if that alias is not referenced anywhere.
        if obj:
            if not obj.is_in_use:
                return request.user.has_perm(
                    get_model_permission_codename(self.model, 'add'),
                )
            return request.user.is_superuser
        return False

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # This is bad and I should feel bad.
        if 'placeholder' in perms_needed:
            perms_needed.remove('placeholder')
        return deleted_objects, model_count, perms_needed, protected


@admin.register(AliasContent)
class AliasContentAdmin(admin.ModelAdmin):
    form = AliasContentForm
