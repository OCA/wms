# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import AbstractComponent, WorkContext


def get_actions_collection(env):
    return _PseudoCollection("shopfloor.action", env)


def get_actions_for(
    component_instance, usage, propagate_kwargs=None, collection=None, **kw
):
    """Return an Action Component for a usage.

    Action Components are the components supporting the business logic of
    the processes, so we can limit the code in services and other components
    to the minimum and share methods.
    """
    propagate_kwargs = component_instance.work._propagate_kwargs[:] + (
        propagate_kwargs or []
    )
    # propagate custom arguments (such as menu ID/profile ID)
    kwargs = {
        attr_name: getattr(component_instance.work, attr_name)
        for attr_name in propagate_kwargs
        if attr_name not in ("collection", "components_registry")
        and hasattr(component_instance.work, attr_name)
    }
    kwargs.update(kw)
    actions_collection = collection or get_actions_collection(component_instance.env)
    work = WorkContext(collection=actions_collection, **kwargs)
    return work.component(usage=usage)


class ShopFloorProcessAction(AbstractComponent):
    """Base Component for actions"""

    _name = "shopfloor.process.action"
    _collection = "shopfloor.action"
    _usage = "actions"

    def _actions_for(self, usage):
        return self.component(usage=usage)

    @property
    def msg_store(self):
        return self._actions_for("message")
