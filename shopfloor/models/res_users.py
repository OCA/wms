from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    shopfloor_group_ids = fields.Many2many(
        'shopfloor.group',
        string="Shopfloor groups"
    )
    shopfloor_current_process = fields.Char()
    shopfloor_last_call = fields.Char()
    shopfloor_picking_id = fields.Many2one('stock.picking')
