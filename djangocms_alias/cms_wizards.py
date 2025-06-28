from cms.utils.permissions import get_model_permission_codename
from cms.wizards.wizard_base import Wizard
from django.utils.translation import gettext_lazy as _

from .cms_plugins import Alias
from .forms import CreateAliasWizardForm, CreateCategoryWizardForm
from .models import Alias as AliasModel
from .models import Category


class CreateAliasWizard(Wizard):
    def user_has_add_permission(self, user, **kwargs):
        return Alias.can_create_alias(user)

    def get_success_url(self, obj, **kwargs):
        return obj.get_admin_change_url()


class CreateAliasCategoryWizard(Wizard):
    def user_has_add_permission(self, user, **kwargs):
        return user.has_perm(
            get_model_permission_codename(Category, "add"),
        )

    def get_success_url(self, obj, **kwargs):
        return obj.get_admin_change_url()


create_alias_wizard = CreateAliasWizard(
    title=_("New alias"),
    weight=200,
    form=CreateAliasWizardForm,
    model=AliasModel,
    description=_("Create a new alias."),
)
create_alias_category_wizard = CreateAliasCategoryWizard(
    title=_("New alias category"),
    weight=200,
    form=CreateCategoryWizardForm,
    model=Category,
    description=_("Create a new alias category."),
)
