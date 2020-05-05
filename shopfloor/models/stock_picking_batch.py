from odoo import fields, models


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    cluster_picking_unload_all = fields.Boolean(
        default=False,
        copy=False,
        help="Technical field. Indicates if a batch is destination is"
        " asked once for all lines or for every line.",
    )

    def total_weight(self):
        return self.calc_weight(self.picking_ids)

    def picking_weight(self, picking):
        return self.calc_weight(picking)

    def calc_weight(self, pickings):
        weight = 0.0
        for move_line in pickings.mapped("move_line_ids"):
            weight += move_line.product_qty * move_line.product_id.weight
        return weight
