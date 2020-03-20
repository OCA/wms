from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    process_ids = fields.One2many(
        comodel_name="shopfloor.process",
        inverse_name="picking_type_id",
        string="Shopfloor Processes",
        readonly=True,
    )
