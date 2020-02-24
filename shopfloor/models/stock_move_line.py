from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    shopfloor_unloaded = fields.Boolean(default=False)
