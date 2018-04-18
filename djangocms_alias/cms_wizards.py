from django.utils.translation import ugettext_lazy as _

from cms.wizards.wizard_base import Wizard
from cms.wizards.wizard_pool import wizard_pool

from .cms_plugins import Alias
from .forms import CreateAliasWizardForm
from .models import Alias as AliasModel


class AliasWizard(Wizard):

    def user_has_add_permission(self, user, **kwargs):
        return Alias.can_create_alias(user)


alias_wizard = AliasWizard(
    title=_('New alias'),
    weight=200,
    form=CreateAliasWizardForm,
    model=AliasModel,
    description=_('Create a new alias.')
)

wizard_pool.register(alias_wizard)
