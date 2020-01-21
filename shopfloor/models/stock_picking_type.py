from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    process_id = fields.Many2one('shopfloor.process', string="Process")
