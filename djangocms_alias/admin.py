from django.contrib import admin

from cms.utils.permissions import get_model_permission_codename

from parler.admin import TranslatableAdmin

from .forms import AliasContentForm
from .models import Alias, AliasContent, Category
from .urls import urlpatterns


__all__ = [
    'AliasAdmin',
    'CategoryAdmin',
    'AliasContentAdmin',
]


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['name']

    def save_model(self, request, obj, form, change):
        change = not obj._state.adding
        super().save_model(request, obj, form, change)
        if change:
            try:
                from djangocms_internalsearch.helpers import emit_content_change
                for content in AliasContent._base_manager.filter(alias__in=obj.aliases.all()):
                    emit_content_change(obj=content, sender=self.model)
            except ImportError:
                pass


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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            from djangocms_internalsearch.helpers import emit_content_change
            for content in AliasContent._base_manager.filter(alias=obj):
                emit_content_change(obj=content, sender=self.model)
        except ImportError:
            pass

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        try:
            from djangocms_internalsearch.helpers import emit_content_change
            for content in AliasContent._base_manager.filter(alias=obj):
                emit_content_change(obj=content, sender=self.model)
        except ImportError:
            pass


@admin.register(AliasContent)
class AliasContentAdmin(admin.ModelAdmin):
    form = AliasContentForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            from djangocms_internalsearch.helpers import emit_content_change
            emit_content_change(obj=obj, sender=self.model)
        except ImportError:
            pass

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        try:
            from djangocms_internalsearch.helpers import emit_content_change
            emit_content_change(obj=obj, sender=self.model)
        except ImportError:
            pass
