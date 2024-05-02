# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    picking_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. Indicates number of transfers included.",
    )
    move_line_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. Indicates number of move lines included.",
    )
    total_weight = fields.Float(
        compute="_compute_picking_info",
        help="Technical field. Indicates total weight of transfers included.",
    )

    @api.depends(
        "picking_ids.state", "picking_ids.total_weight", "picking_ids.move_line_ids"
    )
    def _compute_picking_info(self):
        for item in self:
            assigned_pickings = item.picking_ids.filtered(
                lambda picking: picking.state == "assigned"
            )
            item.update(
                {
                    "picking_count": len(assigned_pickings.ids),
                    "move_line_count": len(
                        assigned_pickings.mapped("move_line_ids").ids
                    ),
                    "total_weight": item._calc_weight(assigned_pickings),
                }
            )

    def _calc_weight(self, pickings):
        return sum(pickings.mapped("total_weight"))
