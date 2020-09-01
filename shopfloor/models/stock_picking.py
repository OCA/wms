from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    total_weight = fields.Float(
        compute="_compute_picking_info",
        help="Technical field. Indicates total weight of transfers included.",
    )
    move_line_count = fields.Integer(
        compute="_compute_picking_info",
        help="Technical field. Indicates number of move lines included.",
    )
    shopfloor_display_packing_info = fields.Boolean(
        related="picking_type_id.shopfloor_display_packing_info",
    )
    shopfloor_packing_info = fields.Text(
        string="Packing information", related="partner_id.shopfloor_packing_info",
    )

    @api.depends(
        "move_line_ids", "move_line_ids.product_qty", "move_line_ids.product_id.weight"
    )
    def _compute_picking_info(self):
        for item in self:
            item.update(
                {
                    "total_weight": item._calc_weight(),
                    "move_line_count": len(item.move_line_ids),
                }
            )

    def _calc_weight(self):
        weight = 0.0
        for move_line in self.mapped("move_line_ids"):
            weight += move_line.product_qty * move_line.product_id.weight
        return weight

    def _create_backorder(self):
        if self.env.context.get("_sf_no_backorder"):
            return self.browse()
        else:
            return super()._create_backorder()

    def action_done(self):
        self = self.with_context(_action_done_from_picking=True)
        return super().action_done()
