# Copyright 2024 vnikolayev1 Raumschmiede GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class StockAction(Component):
    _inherit = "shopfloor.stock.action"

    def _create_return_move__get_vals(self, return_picking, origin_move):
        res = super()._create_return_move__get_vals(return_picking, origin_move)
        if res.get("to_refund") and origin_move.sale_line_id:
            res["sale_line_id"] = origin_move.sale_line_id.id
        return res
