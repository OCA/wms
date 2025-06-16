from odoo import models


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    def _prepare_move_default_values(self, new_picking):
        vals = super()._prepare_move_default_values(new_picking)
        # Update the destination location if provided in context
        # (used for unrelease return logic).
        unrelease_return_type_loc_dest_id = self.env.context.get("return_loc_dest_id")
        if unrelease_return_type_loc_dest_id:
            vals["location_dest_id"] = unrelease_return_type_loc_dest_id
        return vals
