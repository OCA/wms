# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class StockAction(Component):
    _inherit = "shopfloor.stock.action"

    def _create_return_move__get_vals(self, return_picking, origin_move):
        res = super()._create_return_move__get_vals(return_picking, origin_move)
        if return_picking.picking_type_code == "incoming":
            res["to_refund"] = True
        return res
