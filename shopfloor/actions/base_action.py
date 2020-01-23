from odoo.addons.component.core import AbstractComponent


class ShopFloorProcessAction(AbstractComponent):
    _name = "shopfloor.process.action"
    _collection = "shopfloor.action"
    _usage = "actions"

    def actions_for(self, model_name):
        return self.component(usage="actions", model_name=model_name)
