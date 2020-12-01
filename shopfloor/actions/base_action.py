from odoo.addons.component.core import AbstractComponent


class ShopFloorProcessAction(AbstractComponent):
    _name = "shopfloor.process.action"
    _collection = "shopfloor.action"
    _usage = "actions"

    def actions_for(self, usage):
        return self.component(usage=usage)
