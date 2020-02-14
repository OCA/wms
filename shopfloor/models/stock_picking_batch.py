from odoo import fields, models


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    cluster_picking_unload_all = fields.Boolean(
        default=False,
        copy=False,
        help="Technical field. Indicates if a batch is destination is"
        " asked once for all lines or for every line.",
    )
