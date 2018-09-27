from django.contrib import admin

from cms.utils.permissions import get_model_permission_codename

from parler.admin import TranslatableAdmin

from . import constants
from .forms import AliasContentForm
from .models import Alias, AliasContent, Category
from .urls import urlpatterns
from .utils import send_post_alias_operation, send_pre_alias_operation


__all__ = [
    'AliasAdmin',
    'CategoryAdmin',
    'AliasContentAdmin',
]


class AliasOperationAdminMixin:
    create_operation = None
    change_operation = None
    delete_operation = None

    def save_model(self, request, obj, form, change):
        operation = self.change_operation if change else self.create_operation
        operation_token = send_pre_alias_operation(
            request=request,
            operation=operation,
            obj=obj,
            sender=self.model,
        )
        super().save_model(request, obj, form, change)
        send_post_alias_operation(
            request=request,
            operation=operation,
            token=operation_token,
            obj=obj,
            sender=self.model,
        )

    def delete_model(self, request, obj):
        operation_token = send_pre_alias_operation(
            request=request,
            operation=self.delete_operation,
            obj=obj,
            sender=self.model,
        )
        super().delete_model(request, obj)
        send_post_alias_operation(
            request=request,
            operation=self.delete_operation,
            token=operation_token,
            obj=obj,
            sender=self.model,
        )


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['name']


@admin.register(Alias)
class AliasAdmin(AliasOperationAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'category']
    fields = ('category',)

    create_operation = constants.CREATE_ALIAS_OPERATION
    change_operation = constants.CHANGE_ALIAS_OPERATION
    delete_operation = constants.DELETE_ALIAS_OPERATION

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
class AliasContentAdmin(AliasOperationAdminMixin, admin.ModelAdmin):
    form = AliasContentForm

    create_operation = constants.ADD_ALIAS_CONTENT_OPERATION
    change_operation = constants.CHANGE_ALIAS_CONTENT_OPERATION
    delete_operation = constants.DELETE_ALIAS_CONTENT_OPERATION
