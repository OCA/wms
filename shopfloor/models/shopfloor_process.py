from odoo import fields, models


class ShopfloorProcess(models.Model):
    _name = "shopfloor.process"
    _description = "a process to be run from the scanners"

    name = fields.Char(required=True)
    picking_type_ids = fields.One2many(
        "stock.picking.type", "process_id", string="Operation types"
    )
