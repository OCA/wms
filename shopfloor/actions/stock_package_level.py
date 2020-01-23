from odoo.addons.component.core import Component


class StockPackageLevelAction(Component):
    _name = "shopfloor.stock.package_level.action"
    _inherit = "shopfloor.process.action"
    _apply_on = "stock.package_level"

    def hello(self):
        return "world"
