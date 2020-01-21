from odoo import fields, models


class ShopfloorMenu(models.Model):
    _name = 'shopfloor.menu'
    _description = "Menu displayed in the scanner application"
    _order = 'sequence'

    name = fields.Char(translate=True)
    sequence = fields.Integer()
    operation_group_ids = fields.Many2many(
        'shopfloor.operation.group',
        string="Groups",
        help="visible for these groups",
    )
