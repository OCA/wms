# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super()._prepare_move_default_values(return_line, new_picking)
        # Update the destination location if provided in context
        # (used for unrelease return logic).
        unrelease_return_type_loc_dest_id = self.env.context.get("return_loc_dest_id")
        if unrelease_return_type_loc_dest_id:
            vals["location_dest_id"] = unrelease_return_type_loc_dest_id
        return vals

    def _prepare_picking_default_values(self):
        res = super()._prepare_picking_default_values()
        # Update the destination location if provided in context
        # (used for unrelease return logic).
        unrelease_return_type_loc_dest_id = self.env.context.get("return_loc_dest_id")
        if unrelease_return_type_loc_dest_id:
            res["location_dest_id"] = unrelease_return_type_loc_dest_id
        return res
