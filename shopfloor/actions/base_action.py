from odoo.addons.component.core import AbstractComponent


class ShopFloorProcessAction(AbstractComponent):
    """Base Component for actions"""

    _name = "shopfloor.process.action"
    _collection = "shopfloor.action"
    _usage = "actions"

    def actions_for(self, usage):
        return self.component(usage=usage)

    @property
    def msg_store(self):
        return self.actions_for("message")
